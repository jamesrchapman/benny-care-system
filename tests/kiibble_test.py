import sys
from pathlib import Path
import time

# add src/ to python path
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

import bennycaresystem.drivers.kibble_driver as kibble

print("=== Kibble Dropper Test ===")

input("confirm feeder ready and empty bin visible, press ENTER")

print("Test 1: single bin")
success = kibble.drop_kibble_bins(1)
print("Result:", success)

time.sleep(2)

print("Test 2: two bins")
success = kibble.drop_kibble_bins(2)
print("Result:", success)

time.sleep(2)

print("Test 3: five bins (max)")
success = kibble.drop_kibble_bins(5)
print("Result:", success)

print("Done.")