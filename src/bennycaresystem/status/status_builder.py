from datetime import datetime
from bennycaresystem.drivers.pi_health_driver import PiHealthDriver

_pi_health = PiHealthDriver()


def build_status(honey_lock, kibble_lock, camera_lock):

    health = _pi_health.read()

    honey_ready = not honey_lock.locked()
    kibble_ready = not kibble_lock.locked()
    camera_ready = not camera_lock.locked()

    glucose = "unknown"
    slope = "unknown"
    protocol_state = "idle"

    return (
        "BCS STATUS\n\n"

        f"glucose: {glucose}\n"
        f"slope: {slope}\n"
        f"protocol: {protocol_state}\n\n"

        f"honey driver: {'ready' if honey_ready else 'BUSY'}\n"
        f"kibble driver: {'ready' if kibble_ready else 'BUSY'}\n"
        f"camera: {'ready' if camera_ready else 'BUSY'}\n\n"

        f"pi uptime: {health['uptime']}\n"
        f"cpu temp: {health['cpu_temp']}\n"
        f"memory: {health['memory']}%\n"
        f"disk: {health['disk']}%\n\n"

        f"time: {datetime.utcnow().isoformat()}Z"
    )