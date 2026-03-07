@dataclass
class TelemetrySnapshot:

    subsystem: str
    state: str
    metrics: dict
    timestamp: float


SUBSYSTEM_PI = "pi_health"
SUBSYSTEM_NETWORK = "network"
SUBSYSTEM_FEEDER = "feeder"
SUBSYSTEM_CAMERA = "camera"
SUBSYSTEM_GLUCOSE = "glucose"