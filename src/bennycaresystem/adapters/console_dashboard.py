from bennycaresystem.adapters.terminal import clear

import time
import os



def render(snapshot):

    print("SYSTEM HEALTH")
    print(snapshot.get("pi_health"))

    print()
    print("NETWORK")
    print(snapshot.get("network"))

    print()
    print("HONEY ACTUATOR")
    print(snapshot.get("honey_actuator"))

    print()
    print("KIBBLE FEEDER")
    print(snapshot.get("kibble_feeder"))

    print()
    print("GLUCOSE")
    print(snapshot.get("glucose"))


def run_dashboard(telemetry):

    while True:

        clear()

        snap = telemetry.snapshot()

        render(snap)

        time.sleep(2)