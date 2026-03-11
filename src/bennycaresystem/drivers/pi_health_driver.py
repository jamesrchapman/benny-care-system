import os
import shutil
import time


def read_uptime():
    with open("/proc/uptime", "r") as f:
        seconds = float(f.readline().split()[0])

    seconds = int(seconds)

    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60

    return f"{days}d {hours}h {minutes}m"


def read_cpu_temp():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        millideg = int(f.read().strip())

    return round(millideg / 1000.0, 1)


def read_memory_percent():
    total = None
    available = None

    with open("/proc/meminfo") as f:
        for line in f:
            if line.startswith("MemTotal:"):
                total = int(line.split()[1])
            elif line.startswith("MemAvailable:"):
                available = int(line.split()[1])

    used = total - available
    return round((used / total) * 100, 1)


def read_disk_percent():
    total, used, free = shutil.disk_usage("/")

    return round((used / total) * 100, 1)


class PiHealthDriver:

    def read(self):

        return {
            "uptime": read_uptime(),
            "cpu_temp": read_cpu_temp(),
            "memory": read_memory_percent(),
            "disk": read_disk_percent()
        }