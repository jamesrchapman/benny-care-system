import random
from datetime import datetime


def pi_health():

    return {
        "uptime": "1d 04h",
        "cpu_temp": f"{random.randint(50,56)} C",
        "memory": f"{random.randint(35,42)}% used",
        "disk": "41% used",
        "feed_service": "RUNNING",
        "camera_service": "RUNNING",
    }


def network():

    return {
        "wifi": "CONNECTED",
        "signal": "-61 dBm",
        "internet": "REACHABLE",
        "last_ping": f"{random.randint(18,32)} ms",
        "watch_link": "CONNECTED",
    }


def power():

    return {
        "5V_rail": "5.08 V",
        "12V_rail": "11.9 V",
        "power_state": "NORMAL",
    }


def honey_actuator():

    return {
        "state": "READY",
        "driver": "MOSFET_SWITCH",
        "gpio": 23,
        "last_cycle": "12:04:11 → 12:04:16",
        "duration": "5.0s",
        "cycles_today": random.randint(1,5),
        "faults": "none",
    }


def glucose():

    return {
        "current": f"{random.randint(110,140)} mg/dL",
        "trend": random.choice(["stable", "↑ rising", "↓ falling"]),
        "last_reading": datetime.now().strftime("%H:%M:%S"),
        "sensor_age": "6 days",
        "bluetooth": "CONNECTED",
    }