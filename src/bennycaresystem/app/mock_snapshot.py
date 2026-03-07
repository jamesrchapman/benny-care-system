from datetime import datetime
from bennycaresystem.app import mock_providers as mock


event_log = [
    "13:12:56  COOKIE_DROP_COMPLETE",
    "13:12:55  CMD_COOKIE_DROP",
    "12:45:03  KIBBLE_DROP_COMPLETE",
    "12:04:16  HONEY_PUSH_COMPLETE",
    "11:30:10  SYSTEM_BOOT",
]


def get_mock_snapshot():

    return {
        "pi_health": mock.pi_health(),
        "network": mock.network(),
        "power": mock.power(),
        "honey_actuator": mock.honey_actuator(),
        "kibble_feeder": {
            "state": "READY",
            "motor_driver": "MOSFET",
            "gpio": 24,
            "last_drop": "12:45:03",
            "drops_today": 5,
        },
        "cookie_dispenser": {
            "state": "READY",
            "gpio": 25,
            "last_drop": "13:12:56",
            "drops_today": 2,
        },
        "safety": {
            "watchdog": "ACTIVE",
            "timeout": "2h",
            "last_command": "13:12:55",
            "next_rescue": "15:12:55",
            "rescue_action": "honey_push",
        },
        "glucose": mock.glucose(),
        "camera": {
            "camera": "ONLINE",
            "last_frame": datetime.now().strftime("%H:%M:%S"),
            "stream": "AVAILABLE",
        },
        "schedule": {
            "next_kibble": "18:00",
            "next_cookie": "manual",
            "rescue_check": "ACTIVE",
        },
        "heartbeat": {
            "system_heartbeat": datetime.now().strftime("%H:%M:%S"),
        },
        "events": event_log,
    }