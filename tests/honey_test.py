import sys
from pathlib import Path
import time

# add src/ to python path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import bennycaresystem.drivers.honey_driver as honey

print("=== Honey actuator direction test ===")

print("Test 1: tiny forward push")
honey.push_honey_ml(0.2)
time.sleep(2)

print("Test 2: short retract")
honey.retract_seconds(0.5)
time.sleep(2)

print("Test 3: tiny push again")
honey.push_honey_ml(0.2)

for _ in range(20):
    honey.push_honey_ml(0.2)
    time.sleep(1)
    honey.retract_seconds(0.5)
    time.sleep(1)

print("Done.")