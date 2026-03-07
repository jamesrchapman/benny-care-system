class PiHealthDriver:

    def read(self):

        return {
            "uptime": read_uptime(),
            "cpu_temp": read_cpu_temp(),
            "memory": read_memory_percent(),
            "disk": read_disk_percent()
        }