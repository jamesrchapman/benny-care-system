from __future__ import annotations

import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable

from rich.align import Align
from rich.console import Group
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


# ============================================================================
# FAKE MODEL / STATE
# ============================================================================

@dataclass
class DashboardState:
    boot_time: datetime
    event_log: list[str]
    kibble_drops_today: int = 5
    cookie_drops_today: int = 2
    honey_cycles_today: int = 3
    heartbeat_counter: int = 0


# ============================================================================
# SMALL UTILS
# ============================================================================

def now_str() -> str:
    return datetime.now().strftime("%H:%M:%S")


def format_uptime(boot_time: datetime) -> str:
    delta = datetime.now() - boot_time
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    if days > 0:
        return f"{days}d {hours:02}h {minutes:02}m"
    return f"{hours:02}h {minutes:02}m"


def style_for_status(value: str) -> str:
    v = value.upper()
    if v in {"RUNNING", "CONNECTED", "REACHABLE", "ONLINE", "READY", "ACTIVE", "NORMAL", "AVAILABLE"}:
        return "bold green"
    if v in {"WARNING", "DEGRADED", "UNKNOWN", "MANUAL"}:
        return "bold yellow"
    if v in {"FAULT", "ERROR", "OFFLINE", "DISCONNECTED", "FAILED", "NOT_AVAILABLE"}:
        return "bold red"
    return "white"


def render_value(value: Any) -> Text:
    if value is None:
        return Text("N/A", style="dim")
    if isinstance(value, str):
        upper = value.upper()
        if upper in {
            "RUNNING", "CONNECTED", "REACHABLE", "ONLINE", "READY", "ACTIVE",
            "NORMAL", "AVAILABLE", "WARNING", "DEGRADED", "UNKNOWN", "MANUAL",
            "FAULT", "ERROR", "OFFLINE", "DISCONNECTED", "FAILED", "NOT_AVAILABLE"
        }:
            return Text(value, style=style_for_status(value))
        return Text(value)
    return Text(str(value))


def kv_panel(
    title: str,
    rows: Iterable[tuple[str, Any]],
    border_style: str = "cyan",
) -> Panel:
    table = Table.grid(expand=True)
    table.add_column(justify="left", ratio=2)
    table.add_column(justify="left", ratio=3)

    for key, value in rows:
        table.add_row(f"[bold]{key}[/bold]", render_value(value))

    return Panel(table, title=title, border_style=border_style, padding=(0, 1))


def section_header(text: str) -> Panel:
    return Panel(
        Align.center(Text(text, style="bold white")),
        border_style="bright_black",
        padding=(0, 1),
    )


# ============================================================================
# FAKE PROVIDERS
# ============================================================================

def get_pi_health(state: DashboardState) -> dict[str, Any]:
    cpu_temp = random.choice([49, 50, 51, 52, 53, 54, 55, 56])
    mem = random.choice([34, 35, 36, 37, 38, 39, 40, 41])
    disk = random.choice([40, 41, 41, 42, 42, 43])
    feed_service = random.choices(["RUNNING", "WARNING"], weights=[9, 1])[0]
    camera_service = random.choices(["RUNNING", "WARNING"], weights=[9, 1])[0]

    return {
        "uptime": format_uptime(state.boot_time),
        "cpu_temp": f"{cpu_temp} C",
        "memory": f"{mem}% used",
        "disk": f"{disk}% used",
        "feed_service": feed_service,
        "camera_service": camera_service,
    }


def get_network_health(_: DashboardState) -> dict[str, Any]:
    wifi = random.choices(["CONNECTED", "DEGRADED"], weights=[8, 2])[0]
    signal = random.choice([-58, -60, -61, -63, -65, -67])
    internet = random.choices(["REACHABLE", "WARNING"], weights=[9, 1])[0]
    ping = random.choice([19, 21, 22, 23, 24, 27, 31])
    watch_link = random.choices(["CONNECTED", "UNKNOWN"], weights=[8, 2])[0]

    return {
        "wifi": wifi,
        "signal": f"{signal} dBm",
        "internet": internet,
        "last_ping": f"{ping} ms",
        "watch_link": watch_link,
    }


def get_power(_: DashboardState) -> dict[str, Any]:
    rail_5v = random.choice([5.05, 5.07, 5.08, 5.09, 5.10, 4.96])
    rail_12v = random.choice([11.8, 11.9, 12.0, 12.1, 11.7])
    power_state = "NORMAL" if rail_5v >= 5.0 and rail_12v >= 11.8 else "WARNING"

    return {
        "5V_rail": f"{rail_5v:.2f} V",
        "12V_rail": f"{rail_12v:.1f} V",
        "power_state": power_state,
    }


def get_honey_actuator(state: DashboardState) -> dict[str, Any]:
    start = datetime.now().replace(hour=12, minute=4, second=11)
    end = start + timedelta(seconds=5)

    faults = random.choices(["none", "none", "none", "stalled_once"], weights=[7, 7, 7, 1])[0]
    state_text = "READY" if faults == "none" else "WARNING"

    return {
        "state": state_text,
        "driver": "MOSFET_SWITCH",
        "gpio": 23,
        "last_cycle": f"{start.strftime('%H:%M:%S')} -> {end.strftime('%H:%M:%S')}",
        "duration": "5.0 s",
        "cycles_today": state.honey_cycles_today,
        "faults": faults,
    }


def get_kibble_feeder(state: DashboardState) -> dict[str, Any]:
    return {
        "state": random.choices(["READY", "WARNING"], weights=[9, 1])[0],
        "motor_driver": "MOSFET",
        "gpio": 24,
        "last_drop": "12:45:03",
        "drops_today": state.kibble_drops_today,
    }


def get_cookie_dispenser(state: DashboardState) -> dict[str, Any]:
    return {
        "state": random.choices(["READY", "MANUAL"], weights=[8, 2])[0],
        "gpio": 25,
        "last_drop": "13:12:56",
        "drops_today": state.cookie_drops_today,
    }


def get_safety_system(_: DashboardState) -> dict[str, Any]:
    next_rescue = datetime.now() + timedelta(minutes=random.choice([52, 58, 61, 73, 89]))
    return {
        "watchdog": "ACTIVE",
        "rescue_timeout": "2 h",
        "last_command": "13:12:55",
        "next_rescue": next_rescue.strftime("%H:%M:%S"),
        "rescue_action": "honey_push",
    }


def get_glucose(_: DashboardState) -> dict[str, Any]:
    trend = random.choice(["stable", "↑ rising", "↓ falling"])
    glucose = random.choice([112, 118, 121, 128, 133, 137, 141])
    bt = random.choices(["CONNECTED", "DISCONNECTED"], weights=[9, 1])[0]

    return {
        "current_glucose": f"{glucose} mg/dL",
        "trend": trend,
        "last_reading": now_str(),
        "sensor_age": "6 days",
        "bluetooth": bt,
    }


def get_camera(_: DashboardState) -> dict[str, Any]:
    motion = random.choices(["none", "none", "dog_nearby"], weights=[8, 8, 1])[0]
    return {
        "camera": "ONLINE",
        "last_frame": now_str(),
        "stream": "AVAILABLE",
        "motion_detected": motion,
    }


def get_schedule(_: DashboardState) -> dict[str, Any]:
    return {
        "next_kibble": "18:00",
        "next_cookie": "manual",
        "rescue_check": "ACTIVE",
        "next_expected_operator_check": "20:00",
    }


def get_heartbeat(state: DashboardState) -> dict[str, Any]:
    state.heartbeat_counter += 1
    return {
        "system_heartbeat": now_str(),
        "tick": state.heartbeat_counter,
    }


def maybe_mutate_events(state: DashboardState) -> None:
    candidates = [
        "COOKIE_DROP_COMPLETE",
        "CMD_COOKIE_DROP",
        "KIBBLE_DROP_COMPLETE",
        "HONEY_PUSH_COMPLETE",
        "WATCHDOG_PING",
        "GLUCOSE_READING_CAPTURED",
        "CAMERA_FRAME_OK",
        "POWER_SAMPLE_OK",
        "BLE_SENSOR_RECONNECT",
        "SYSTEM_BOOT",
    ]
    if random.random() < 0.25:
        event = f"{now_str()}  {random.choice(candidates)}"
        state.event_log.insert(0, event)
        del state.event_log[20:]


# ============================================================================
# PANEL BUILDERS
# ============================================================================

def build_system_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "PI HEALTH",
        [
            ("uptime", data["uptime"]),
            ("cpu temp", data["cpu_temp"]),
            ("memory", data["memory"]),
            ("disk", data["disk"]),
            ("feed_service", data["feed_service"]),
            ("camera_service", data["camera_service"]),
        ],
        border_style="blue",
    )


def build_network_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "NETWORK",
        [
            ("wifi", data["wifi"]),
            ("signal", data["signal"]),
            ("internet", data["internet"]),
            ("last ping", data["last_ping"]),
            ("watch link", data["watch_link"]),
        ],
        border_style="magenta",
    )


def build_power_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "POWER",
        [
            ("5V rail", data["5V_rail"]),
            ("12V rail", data["12V_rail"]),
            ("power state", data["power_state"]),
        ],
        border_style="yellow",
    )


def build_honey_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "HONEY ACTUATOR",
        [
            ("state", data["state"]),
            ("driver", data["driver"]),
            ("gpio", data["gpio"]),
            ("last cycle", data["last_cycle"]),
            ("duration", data["duration"]),
            ("cycles today", data["cycles_today"]),
            ("faults", data["faults"]),
        ],
        border_style="green",
    )


def build_kibble_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "KIBBLE FEEDER",
        [
            ("state", data["state"]),
            ("motor driver", data["motor_driver"]),
            ("gpio", data["gpio"]),
            ("last drop", data["last_drop"]),
            ("drops today", data["drops_today"]),
        ],
        border_style="green",
    )


def build_cookie_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "COOKIE DISPENSER",
        [
            ("state", data["state"]),
            ("gpio", data["gpio"]),
            ("last drop", data["last_drop"]),
            ("drops today", data["drops_today"]),
        ],
        border_style="green",
    )


def build_safety_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "SAFETY SYSTEM",
        [
            ("watchdog", data["watchdog"]),
            ("rescue timeout", data["rescue_timeout"]),
            ("last command", data["last_command"]),
            ("next rescue", data["next_rescue"]),
            ("rescue action", data["rescue_action"]),
        ],
        border_style="red",
    )


def build_glucose_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "LIBRE DATA",
        [
            ("current glucose", data["current_glucose"]),
            ("trend", data["trend"]),
            ("last reading", data["last_reading"]),
            ("sensor age", data["sensor_age"]),
            ("bluetooth", data["bluetooth"]),
        ],
        border_style="cyan",
    )


def build_camera_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "CAMERA",
        [
            ("camera", data["camera"]),
            ("last frame", data["last_frame"]),
            ("stream", data["stream"]),
            ("motion detected", data["motion_detected"]),
        ],
        border_style="bright_blue",
    )


def build_schedule_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "SCHEDULE",
        [
            ("next kibble", data["next_kibble"]),
            ("next cookie", data["next_cookie"]),
            ("rescue check", data["rescue_check"]),
            ("operator check", data["next_expected_operator_check"]),
        ],
        border_style="white",
    )


def build_heartbeat_panel(data: dict[str, Any]) -> Panel:
    return kv_panel(
        "HEARTBEAT",
        [
            ("system heartbeat", data["system_heartbeat"]),
            ("tick", data["tick"]),
        ],
        border_style="bright_black",
    )


def build_commands_panel() -> Panel:
    text = Text()
    text.append("COMMANDS (MOCK)\n", style="bold")
    text.append(" [1] Honey push\n")
    text.append(" [2] Kibble drop\n")
    text.append(" [3] Cookie drop\n")
    text.append(" [4] Snapshot camera\n")
    text.append(" [5] Trigger rescue\n")
    text.append(" [Q] Quit (not wired in this mock)\n", style="dim")
    return Panel(text, title="COMMANDS", border_style="white")


def build_event_log_panel(events: list[str]) -> Panel:
    table = Table.grid(expand=True)
    table.add_column(ratio=1)

    for event in events[:14]:
        table.add_row(Text(event))

    return Panel(table, title="EVENT LOG", border_style="bright_magenta", padding=(0, 1))


def build_title_bar() -> Panel:
    text = Text("BENNY CARE SYSTEM :: MOCK CONTROL ROOM DASHBOARD", style="bold white")
    return Panel(Align.center(text), border_style="bright_white", padding=(0, 1))


# ============================================================================
# DASHBOARD COMPOSITION
# ============================================================================

def build_dashboard(state: DashboardState) -> Layout:
    maybe_mutate_events(state)

    pi = get_pi_health(state)
    network = get_network_health(state)
    power = get_power(state)
    honey = get_honey_actuator(state)
    kibble = get_kibble_feeder(state)
    cookie = get_cookie_dispenser(state)
    safety = get_safety_system(state)
    glucose = get_glucose(state)
    camera = get_camera(state)
    schedule = get_schedule(state)
    heartbeat = get_heartbeat(state)

    layout = Layout(name="root")
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3),
    )

    layout["header"].update(build_title_bar())

    layout["body"].split_column(
        Layout(name="row_top", ratio=2),
        Layout(name="row_mid", ratio=3),
        Layout(name="row_bottom", ratio=3),
        Layout(name="row_log", ratio=4),
    )

    layout["row_top"].split_row(
        Layout(name="system"),
        Layout(name="network"),
        Layout(name="power"),
    )

    layout["row_mid"].split_row(
        Layout(name="honey"),
        Layout(name="kibble"),
        Layout(name="cookie"),
    )

    layout["row_bottom"].split_row(
        Layout(name="safety"),
        Layout(name="glucose"),
        Layout(name="camera"),
        Layout(name="right_stack"),
    )

    layout["right_stack"].split_column(
        Layout(name="schedule"),
        Layout(name="heartbeat"),
        Layout(name="commands"),
    )

    layout["row_log"].update(build_event_log_panel(state.event_log))

    layout["system"].update(build_system_panel(pi))
    layout["network"].update(build_network_panel(network))
    layout["power"].update(build_power_panel(power))

    layout["honey"].update(build_honey_panel(honey))
    layout["kibble"].update(build_kibble_panel(kibble))
    layout["cookie"].update(build_cookie_panel(cookie))

    layout["safety"].update(build_safety_panel(safety))
    layout["glucose"].update(build_glucose_panel(glucose))
    layout["camera"].update(build_camera_panel(camera))

    layout["schedule"].update(build_schedule_panel(schedule))
    layout["heartbeat"].update(build_heartbeat_panel(heartbeat))
    layout["commands"].update(build_commands_panel())

    footer = Group(
        Text("Mock mode only. Hardware is not queried. Missing data later becomes real providers.", style="dim"),
    )
    layout["footer"].update(Panel(footer, border_style="bright_black"))

    return layout


# ============================================================================
# MAIN
# ============================================================================

def main() -> None:
    state = DashboardState(
        boot_time=datetime.now() - timedelta(days=1, hours=4, minutes=12),
        event_log=[
            "13:12:56  COOKIE_DROP_COMPLETE",
            "13:12:55  CMD_COOKIE_DROP",
            "12:45:03  KIBBLE_DROP_COMPLETE",
            "12:04:16  HONEY_PUSH_COMPLETE",
            "11:30:10  SYSTEM_BOOT",
        ],
    )

    with Live(build_dashboard(state), refresh_per_second=2, screen=True) as live:
        while True:
            live.update(build_dashboard(state))
            time.sleep(1)


if __name__ == "__main__":
    main()