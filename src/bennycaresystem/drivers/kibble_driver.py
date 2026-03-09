import time
import RPi.GPIO as GPIO

KIBBLE_GATE = 25
KIBBLE_FEEDBACK = 24

BIN_TIMEOUT_SECONDS = 5
MAX_BINS_PER_COMMAND = 5
DEBOUNCE_DELAY = 0.2
GATE_SETTLE_DELAY = 0.05


def _setup():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(KIBBLE_GATE, GPIO.OUT)
    GPIO.setup(KIBBLE_FEEDBACK, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # force a known idle state
    GPIO.output(KIBBLE_GATE, GPIO.LOW)
    time.sleep(0.05)


_setup()


def drop_kibble_bins(bins: int) -> bool:
    if bins <= 0 or bins > MAX_BINS_PER_COMMAND:
        return False

    for _ in range(bins):
        if not _drop_one_bin():
            return False

    return True


def _drop_one_bin() -> bool:
    start_state = GPIO.input(KIBBLE_FEEDBACK)

    start_time = time.time()

    try:
        GPIO.output(KIBBLE_GATE, GPIO.HIGH)

        while True:
            current = GPIO.input(KIBBLE_FEEDBACK)

            # detect bin sensor transition
            if current != start_state:
                break

            if time.time() - start_time > BIN_TIMEOUT_SECONDS:
                return False

            time.sleep(0.01)

        # debounce sensor
        time.sleep(DEBOUNCE_DELAY)

        return True

    finally:
        GPIO.output(KIBBLE_GATE, GPIO.LOW)
        time.sleep(GATE_SETTLE_DELAY)