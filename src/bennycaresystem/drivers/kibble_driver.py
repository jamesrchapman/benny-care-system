import time
import logging
import RPi.GPIO as GPIO

KIBBLE_GATE = 25
KIBBLE_FEEDBACK = 24

BIN_TIMEOUT_SECONDS = 5
MAX_BINS_PER_COMMAND = 5
DEBOUNCE_DELAY = 0.2
GATE_SETTLE_DELAY = 0.05

logging.basicConfig(level=logging.INFO)


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
        logging.error(
            "KIBBLE COMMAND REJECTED: requested_bins=%s exceeds allowed range (1-%s). "
            "This guard prevents accidental hopper dump from malformed commands.",
            bins,
            MAX_BINS_PER_COMMAND,
        )
        return False

    logging.info("KIBBLE COMMAND ACCEPTED: dropping %s bins", bins)

    for i in range(bins):
        if not _drop_one_bin():
            logging.error(
                "KIBBLE DROP FAILURE: bin_index=%s of %s did not complete before timeout",
                i + 1,
                bins,
            )
            return False

    logging.info("KIBBLE COMMAND COMPLETE: dropped %s bins", bins)
    return True



def _drop_one_bin() -> bool:
    start_state = GPIO.input(KIBBLE_FEEDBACK)
    transitions = 0

    start_time = time.time()

    try:
        GPIO.output(KIBBLE_GATE, GPIO.HIGH)

        while transitions < 2:
            current = GPIO.input(KIBBLE_FEEDBACK)

            if current != start_state:
                transitions += 1
                start_state = current
                time.sleep(DEBOUNCE_DELAY)

            if time.time() - start_time > BIN_TIMEOUT_SECONDS:
                return False

            time.sleep(0.005)

        return True

    finally:
        GPIO.output(KIBBLE_GATE, GPIO.LOW)
        time.sleep(GATE_SETTLE_DELAY)