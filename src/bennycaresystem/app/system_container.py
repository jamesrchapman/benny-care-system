pi_driver = PiHealthDriver()
network_driver = NetworkDriver()

telemetry = TelemetryService()

telemetry.register("pi_health", pi_driver.read)
telemetry.register("network", network_driver.read)