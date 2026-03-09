from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Protocol, Sequence


# =============================================================================
# TYPES / PORTS
# =============================================================================


class EventLogger(Protocol):
    def __call__(self, event_type: str, **data: object) -> None:
        ...


class Notifier(Protocol):
    def __call__(self, message: str) -> None:
        ...


@dataclass(frozen=True)
class Reading:
    timestamp: datetime
    glucose_mgdl: float


class InterventionLevel(str, Enum):
    BELOW_100 = "below_100"
    BELOW_80 = "below_80"
    BELOW_70 = "below_70"
    BELOW_60 = "below_60"


@dataclass(frozen=True)
class FeedPlan:
    kibble_bins: int = 0
    cookie_dust_doses: int = 0
    cookies: int = 0
    honey_g: int = 0


@dataclass(frozen=True)
class AlertSpec:
    level: InterventionLevel
    threshold_mgdl: float
    response_window: timedelta
    feed_plan: FeedPlan
    suppress_if_dramatic_increase: bool
    alert_event: str
    action_event: str


ALERT_SPECS: tuple[AlertSpec, ...] = (
    AlertSpec(
        level=InterventionLevel.BELOW_60,
        threshold_mgdl=60,
        response_window=timedelta(minutes=2),
        feed_plan=FeedPlan(kibble_bins=1, cookies=2, honey_g=20),
        suppress_if_dramatic_increase=False,
        alert_event="AUTO_ALERT_60",
        action_event="AUTO_HONEY_20G",
    ),
    AlertSpec(
        level=InterventionLevel.BELOW_70,
        threshold_mgdl=70,
        response_window=timedelta(minutes=2),
        feed_plan=FeedPlan(kibble_bins=1, cookies=2, honey_g=15),
        suppress_if_dramatic_increase=False,
        alert_event="AUTO_ALERT_70",
        action_event="AUTO_HONEY_15G",
    ),
    AlertSpec(
        level=InterventionLevel.BELOW_80,
        threshold_mgdl=80,
        response_window=timedelta(minutes=5),
        feed_plan=FeedPlan(kibble_bins=1, cookies=2, honey_g=10),
        suppress_if_dramatic_increase=True,
        alert_event="AUTO_ALERT_80",
        action_event="AUTO_HONEY_10G",
    ),
    AlertSpec(
        level=InterventionLevel.BELOW_100,
        threshold_mgdl=100,
        response_window=timedelta(minutes=10),
        feed_plan=FeedPlan(kibble_bins=1, cookie_dust_doses=1),
        suppress_if_dramatic_increase=True,
        alert_event="AUTO_ALERT_100",
        action_event="AUTO_SNACK",
    ),
)


@dataclass
class PendingIntervention:
    spec: AlertSpec
    created_at: datetime
    execute_at: datetime
    reading_at_creation: Reading
    cancelled: bool = False
    operator_responded: bool = False
    completed: bool = False


@dataclass
class ProtocolStatus:
    enabled: bool
    pending_intervention: PendingIntervention | None
    last_honey_at: datetime | None
    latest_valid_reading: Reading | None
    recent_readings: list[Reading]
    dramatic_increase: bool
    in_honey_cooldown: bool


@dataclass
class ProtocolDecision:
    notifications: list[str] = field(default_factory=list)
    log_events: list[tuple[str, dict[str, object]]] = field(default_factory=list)
    actions: list[FeedPlan] = field(default_factory=list)


# =============================================================================
# SAFETY PROTOCOL
# =============================================================================


class BennyLowGlucoseSafetyProtocol:
    """
    Deterministic autonomous low-glucose safety protocol.

    Design goals:
    - Alert operator before automatic intervention.
    - Avoid runaway repeated honey doses.
    - Ignore obvious single-point sensor glitches.
    - Keep all state explicit and inspectable.

    This object is intentionally side-effect free except through the injected
    notifier and logger ports.
    """

    HONEY_COOLDOWN = timedelta(minutes=10)
    CRITICAL_COOLDOWN_BYPASS_MGDL = 55
    ARTIFACT_JUMP_MGDL = 15
    POST_URGENT_RECHECK = timedelta(minutes=10)

    def __init__(
        self,
        *,
        notify_operator: Notifier,
        log_event: EventLogger,
        time_provider: Callable[[], datetime] | None = None,
    ) -> None:
        self._notify_operator = notify_operator
        self._log_event = log_event
        self._time_provider = time_provider or datetime.now

        self._enabled = True
        self._recent_readings: list[Reading] = []
        self._latest_valid_reading: Reading | None = None
        self._pending: PendingIntervention | None = None
        self._last_honey_at: datetime | None = None
        self._awaiting_post_urgent_recheck_until: datetime | None = None

    # -------------------------------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------------------------------

    def status(self) -> ProtocolStatus:
        now = self._time_provider()
        return ProtocolStatus(
            enabled=self._enabled,
            pending_intervention=self._pending,
            last_honey_at=self._last_honey_at,
            latest_valid_reading=self._latest_valid_reading,
            recent_readings=list(self._recent_readings),
            dramatic_increase=self._compute_dramatic_increase(),
            in_honey_cooldown=self._is_honey_cooldown(now, self._latest_valid_reading),
        )

    def set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self._log_event("AUTO_PROTOCOL_ENABLED" if enabled else "AUTO_PROTOCOL_DISABLED")
        if not enabled and self._pending is not None:
            self._cancel_pending_internal(reason="protocol_disabled")

    def operator_response(self, note: str = "operator responded") -> None:
        if self._pending is None:
            self._log_event("AUTO_OPERATOR_RESPONSE_WITHOUT_PENDING", note=note)
            return

        self._pending.operator_responded = True
        self._pending.cancelled = True
        self._log_event(
            "AUTO_INTERVENTION_CANCELLED_BY_OPERATOR",
            level=self._pending.spec.level.value,
            note=note,
        )
        self._pending = None

    def cancel_pending_intervention(self, reason: str = "manual cancel") -> None:
        self._cancel_pending_internal(reason=reason)

    def ingest_reading(self, reading: Reading) -> ProtocolDecision:
        decision = ProtocolDecision()

        # Always keep the raw series for artifact checks and trend windows.
        self._recent_readings.append(reading)
        self._recent_readings.sort(key=lambda r: r.timestamp)
        self._trim_readings(window=timedelta(minutes=40))

        # <60 bypasses artifact suppression per protocol.
        if reading.glucose_mgdl >= 60 and self._is_artifact_middle_point():
            self._log_event(
                "AUTO_READING_IGNORED_ARTIFACT",
                glucose_mgdl=reading.glucose_mgdl,
                timestamp=reading.timestamp.isoformat(),
            )
            # Do not treat artifact as valid state.
            self._evaluate_pending_timeout(decision)
            return decision

        self._latest_valid_reading = reading

        # Time-based state machine: execute pending if its timeout has elapsed.
        self._evaluate_pending_timeout(decision)

        if not self._enabled:
            return decision

        # Schedule new pending intervention if thresholds warrant it.
        self._schedule_if_needed(reading, decision)

        # If we are in post-urgent recheck mode, re-evaluate urgency at 10-minute marks.
        self._evaluate_post_urgent_recheck(reading, decision)

        return decision

    # -------------------------------------------------------------------------
    # INTERNALS: SCHEDULING / EXECUTION
    # -------------------------------------------------------------------------

    def _schedule_if_needed(self, reading: Reading, decision: ProtocolDecision) -> None:
        if self._pending is not None:
            # Keep the highest-severity pending intervention. Escalate if needed.
            new_spec = self._pick_spec(reading.glucose_mgdl)
            if new_spec is None:
                return
            if self._is_more_severe(new_spec, self._pending.spec):
                self._log_event(
                    "AUTO_PENDING_ESCALATED",
                    old_level=self._pending.spec.level.value,
                    new_level=new_spec.level.value,
                )
                self._pending = self._create_pending(new_spec, reading)
                self._emit_alert(self._pending, decision)
            return

        spec = self._pick_spec(reading.glucose_mgdl)
        if spec is None:
            return

        self._pending = self._create_pending(spec, reading)
        self._emit_alert(self._pending, decision)

    def _create_pending(self, spec: AlertSpec, reading: Reading) -> PendingIntervention:
        return PendingIntervention(
            spec=spec,
            created_at=self._time_provider(),
            execute_at=self._time_provider() + spec.response_window,
            reading_at_creation=reading,
        )

    def _emit_alert(self, pending: PendingIntervention, decision: ProtocolDecision) -> None:
        msg = self._format_alert_message(pending)
        decision.notifications.append(msg)
        decision.log_events.append(
            (
                pending.spec.alert_event,
                {
                    "glucose_mgdl": pending.reading_at_creation.glucose_mgdl,
                    "execute_at": pending.execute_at.isoformat(),
                    "level": pending.spec.level.value,
                },
            )
        )
        self._notify_operator(msg)
        self._log_event(
            pending.spec.alert_event,
            glucose_mgdl=pending.reading_at_creation.glucose_mgdl,
            execute_at=pending.execute_at.isoformat(),
            level=pending.spec.level.value,
        )

    def _evaluate_pending_timeout(self, decision: ProtocolDecision) -> None:
        if self._pending is None:
            return

        now = self._time_provider()
        if now < self._pending.execute_at:
            return

        pending = self._pending
        self._pending = None

        if pending.cancelled or pending.operator_responded:
            return

        current = self._latest_valid_reading
        if current is None:
            self._log_event(
                "AUTO_PENDING_SKIPPED_NO_VALID_READING",
                level=pending.spec.level.value,
            )
            return

        # Condition must still hold at execution time.
        if current.glucose_mgdl >= pending.spec.threshold_mgdl:
            self._log_event(
                "AUTO_PENDING_SKIPPED_THRESHOLD_RECOVERED",
                level=pending.spec.level.value,
                current_glucose_mgdl=current.glucose_mgdl,
            )
            return

        if pending.spec.suppress_if_dramatic_increase and self._compute_dramatic_increase():
            self._log_event(
                "AUTO_PENDING_SKIPPED_DRAMATIC_INCREASE",
                level=pending.spec.level.value,
                current_glucose_mgdl=current.glucose_mgdl,
            )
            return

        if pending.spec.feed_plan.honey_g > 0 and self._is_honey_cooldown(now, current):
            self._log_event(
                "AUTO_PENDING_SKIPPED_HONEY_COOLDOWN",
                level=pending.spec.level.value,
                current_glucose_mgdl=current.glucose_mgdl,
            )
            return

        self._execute_feed_plan(pending.spec, current, decision)

    def _execute_feed_plan(
        self,
        spec: AlertSpec,
        reading: Reading,
        decision: ProtocolDecision,
    ) -> None:
        decision.actions.append(spec.feed_plan)
        decision.log_events.append(
            (
                spec.action_event,
                {
                    "glucose_mgdl": reading.glucose_mgdl,
                    "level": spec.level.value,
                    "honey_g": spec.feed_plan.honey_g,
                    "cookies": spec.feed_plan.cookies,
                    "cookie_dust_doses": spec.feed_plan.cookie_dust_doses,
                    "kibble_bins": spec.feed_plan.kibble_bins,
                },
            )
        )

        self._log_event(
            spec.action_event,
            glucose_mgdl=reading.glucose_mgdl,
            level=spec.level.value,
            honey_g=spec.feed_plan.honey_g,
            cookies=spec.feed_plan.cookies,
            cookie_dust_doses=spec.feed_plan.cookie_dust_doses,
            kibble_bins=spec.feed_plan.kibble_bins,
        )

        if spec.feed_plan.honey_g > 0:
            self._last_honey_at = self._time_provider()

        if spec.level in {InterventionLevel.BELOW_70, InterventionLevel.BELOW_60}:
            self._awaiting_post_urgent_recheck_until = self._time_provider() + self.POST_URGENT_RECHECK
            self._log_event(
                "AUTO_URGENT_RECHECK_SCHEDULED",
                recheck_at=self._awaiting_post_urgent_recheck_until.isoformat(),
                level=spec.level.value,
            )

    def _evaluate_post_urgent_recheck(self, reading: Reading, decision: ProtocolDecision) -> None:
        if self._awaiting_post_urgent_recheck_until is None:
            return

        now = self._time_provider()
        if now < self._awaiting_post_urgent_recheck_until:
            return

        self._awaiting_post_urgent_recheck_until = None

        # Re-check logic per protocol: repeat appropriate intervention level
        # if still low and not rising.
        slope = self._compute_slope_over_window(timedelta(minutes=10))
        is_rising = slope is not None and slope > 0

        if reading.glucose_mgdl < 60 and not is_rising:
            spec = self._spec_for_level(InterventionLevel.BELOW_60)
            assert spec is not None
            self._log_event("AUTO_URGENT_RECHECK_TRIGGERED", level=spec.level.value)
            self._pending = self._create_pending(spec, reading)
            self._emit_alert(self._pending, decision)
            return

        if reading.glucose_mgdl < 70 and not is_rising:
            spec = self._spec_for_level(InterventionLevel.BELOW_70)
            assert spec is not None
            self._log_event("AUTO_URGENT_RECHECK_TRIGGERED", level=spec.level.value)
            self._pending = self._create_pending(spec, reading)
            self._emit_alert(self._pending, decision)

    # -------------------------------------------------------------------------
    # INTERNALS: MATH / HEURISTICS
    # -------------------------------------------------------------------------

    def _compute_dramatic_increase(self) -> bool:
        recent = self._compute_average_slope_between(
            start_offset=timedelta(minutes=10),
            end_offset=timedelta(minutes=0),
        )
        previous = self._compute_average_slope_between(
            start_offset=timedelta(minutes=20),
            end_offset=timedelta(minutes=10),
        )
        if recent is None or previous is None:
            return False
        return (recent - previous >= 0.8) and (recent >= 2.0)

    def _compute_slope_over_window(self, window: timedelta) -> float | None:
        if self._latest_valid_reading is None:
            return None

        end = self._latest_valid_reading.timestamp
        start = end - window
        candidates = [r for r in self._recent_readings if start <= r.timestamp <= end]
        if len(candidates) < 2:
            return None

        first = min(candidates, key=lambda r: r.timestamp)
        last = max(candidates, key=lambda r: r.timestamp)
        dt_minutes = (last.timestamp - first.timestamp).total_seconds() / 60.0
        if dt_minutes <= 0:
            return None
        return (last.glucose_mgdl - first.glucose_mgdl) / dt_minutes

    def _compute_average_slope_between(
        self,
        *,
        start_offset: timedelta,
        end_offset: timedelta,
    ) -> float | None:
        if self._latest_valid_reading is None:
            return None

        ref = self._latest_valid_reading.timestamp
        start = ref - start_offset
        end = ref - end_offset
        candidates = [r for r in self._recent_readings if start <= r.timestamp <= end]
        if len(candidates) < 2:
            return None

        first = min(candidates, key=lambda r: r.timestamp)
        last = max(candidates, key=lambda r: r.timestamp)
        dt_minutes = (last.timestamp - first.timestamp).total_seconds() / 60.0
        if dt_minutes <= 0:
            return None
        return (last.glucose_mgdl - first.glucose_mgdl) / dt_minutes

    def _is_honey_cooldown(self, now: datetime, reading: Reading | None) -> bool:
        if self._last_honey_at is None:
            return False
        if reading is not None and reading.glucose_mgdl < self.CRITICAL_COOLDOWN_BYPASS_MGDL:
            return False
        return now - self._last_honey_at < self.HONEY_COOLDOWN

    def _is_artifact_middle_point(self) -> bool:
        # Check the newest reading as the center of a 3-point pattern is impossible,
        # so inspect the middle of the last 3 points. We only need a simple
        # single-point glitch detector matching the protocol.
        if len(self._recent_readings) < 3:
            return False

        a, b, c = self._recent_readings[-3:]
        return (
            abs(b.glucose_mgdl - a.glucose_mgdl) > self.ARTIFACT_JUMP_MGDL
            and abs(b.glucose_mgdl - c.glucose_mgdl) > self.ARTIFACT_JUMP_MGDL
        )

    # -------------------------------------------------------------------------
    # INTERNALS: HELPERS
    # -------------------------------------------------------------------------

    def _trim_readings(self, window: timedelta) -> None:
        cutoff = self._time_provider() - window
        self._recent_readings = [r for r in self._recent_readings if r.timestamp >= cutoff]

    def _pick_spec(self, glucose_mgdl: float) -> AlertSpec | None:
        for spec in ALERT_SPECS:
            if glucose_mgdl < spec.threshold_mgdl:
                return spec
        return None

    def _spec_for_level(self, level: InterventionLevel) -> AlertSpec | None:
        for spec in ALERT_SPECS:
            if spec.level == level:
                return spec
        return None

    @staticmethod
    def _is_more_severe(new_spec: AlertSpec, existing_spec: AlertSpec) -> bool:
        severity_order = {
            InterventionLevel.BELOW_100: 1,
            InterventionLevel.BELOW_80: 2,
            InterventionLevel.BELOW_70: 3,
            InterventionLevel.BELOW_60: 4,
        }
        return severity_order[new_spec.level] > severity_order[existing_spec.level]

    def _cancel_pending_internal(self, reason: str) -> None:
        if self._pending is None:
            self._log_event("AUTO_CANCEL_WITHOUT_PENDING", reason=reason)
            return
        self._pending.cancelled = True
        self._log_event(
            "AUTO_PENDING_CANCELLED",
            reason=reason,
            level=self._pending.spec.level.value,
        )
        self._pending = None

    def _format_alert_message(self, pending: PendingIntervention) -> str:
        g = pending.reading_at_creation.glucose_mgdl
        minutes = int(pending.spec.response_window.total_seconds() // 60)
        dramatic = self._compute_dramatic_increase()
        dramatic_text = "YES" if dramatic else "NO"

        return (
            f"Benny low-glucose alert\n"
            f"level: {pending.spec.level.value}\n"
            f"glucose: {g:.0f} mg/dL\n"
            f"dramatic increase: {dramatic_text}\n"
            f"auto action in: {minutes} min\n"
            f"plan: honey={pending.spec.feed_plan.honey_g}g, cookies={pending.spec.feed_plan.cookies}, "
            f"cookie_dust={pending.spec.feed_plan.cookie_dust_doses}, kibble_bins={pending.spec.feed_plan.kibble_bins}"
        )


# =============================================================================
# SIMPLE IN-MEMORY UTILITIES FOR LOCAL TESTING
# =============================================================================


@dataclass
class MemoryEventSink:
    events: list[tuple[str, dict[str, object]]] = field(default_factory=list)

    def __call__(self, event_type: str, **data: object) -> None:
        self.events.append((event_type, data))


@dataclass
class MemoryNotifier:
    messages: list[str] = field(default_factory=list)

    def __call__(self, message: str) -> None:
        self.messages.append(message)


# =============================================================================
# EXAMPLE
# =============================================================================


def _example() -> None:
    notifier = MemoryNotifier()
    logger = MemoryEventSink()

    # Fake time source for deterministic testing.
    current = datetime(2026, 3, 7, 9, 0, 0)

    def now() -> datetime:
        return current

    protocol = BennyLowGlucoseSafetyProtocol(
        notify_operator=notifier,
        log_event=logger,
        time_provider=now,
    )

    readings = [
        Reading(current - timedelta(minutes=20), 105),
        Reading(current - timedelta(minutes=10), 98),
        Reading(current, 79),
    ]

    for r in readings:
        protocol.ingest_reading(r)

    # No operator response; advance time past the 5-minute timeout for <80.
    current = current + timedelta(minutes=6)
    protocol.ingest_reading(Reading(current, 77))

    print("Messages:")
    for msg in notifier.messages:
        print("-", msg)

    print("\nEvents:")
    for event_type, data in logger.events:
        print(event_type, data)


if __name__ == "__main__":
    _example()
