import sys
from pathlib import Path
import time

# add src/ to python path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import bennycaresystem.drivers.honey_driver as honey

print("=== Honey actuator direction test ===")

print("record initial position")
input("Test 1: 3 second push")
honey.push_honey_seconds(3)
time.sleep(2)

print("record position after push")
input("Test 2: 3 second retract")
honey.retract_seconds(3)
time.sleep(2)

print("record position after retract")
input("wiring test: 20 cycles of 1 second push, 1 second retract")
for _ in range(20):
    honey.push_honey_ml(1)
    time.sleep(1)
    honey.retract_seconds(1)
    time.sleep(1)


print("record position after 20 cycles")
print("Done.")