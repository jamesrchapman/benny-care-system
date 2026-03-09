from bennycaresystem.app.telemetry_service import TelemetryService
from bennycaresystem.adapters.console_dashboard import run_dashboard

import bennycaresystem.app.mock_providers as mock


telemetry = TelemetryService()

telemetry.register("pi_health", mock.pi_health)
telemetry.register("network", mock.network)
telemetry.register("honey_actuator", mock.honey_actuator)
telemetry.register("kibble_feeder", mock.kibble_feeder)
telemetry.register("glucose", mock.glucose)


run_dashboard(telemetry)