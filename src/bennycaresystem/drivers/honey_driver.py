import time
import RPi.GPIO as GPIO

HONEY_FWD = 18
HONEY_REV = 19
HONEY_EN  = 23

ML_PER_SECOND = 0.35
MAX_ML_PER_COMMAND = 5.0
MAX_DURATION_SECONDS = 15
MIN_INTERVAL_SECONDS = 20

_last_push_time = 0


def _setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(HONEY_FWD, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(HONEY_REV, GPIO.OUT, initial=GPIO.LOW)
    GPIO.setup(HONEY_EN, GPIO.OUT, initial=GPIO.LOW)


_setup()


def _stop():
    GPIO.output(HONEY_FWD, GPIO.LOW)
    GPIO.output(HONEY_REV, GPIO.LOW)
    GPIO.output(HONEY_EN, GPIO.LOW)


def _run(direction: str, duration: float):
    if duration <= 0:
        return False

    try:
        GPIO.output(HONEY_EN, GPIO.HIGH)

        if direction == "forward":
            GPIO.output(HONEY_REV, GPIO.LOW)
            GPIO.output(HONEY_FWD, GPIO.HIGH)

        elif direction == "reverse":
            GPIO.output(HONEY_FWD, GPIO.LOW)
            GPIO.output(HONEY_REV, GPIO.HIGH)

        else:
            _stop()
            return False

        time.sleep(duration)
        _stop()
        return True

    except Exception:
        _stop()
        raise


def push_honey_ml(ml: float) -> bool:
    global _last_push_time

    now = time.time()

    if ml <= 0 or ml > MAX_ML_PER_COMMAND:
        return False

    if now - _last_push_time < MIN_INTERVAL_SECONDS:
        return False

    duration = ml / ML_PER_SECOND

    if duration > MAX_DURATION_SECONDS:
        return False

    result = _run("forward", duration)

    if result:
        _last_push_time = time.time()

    return result


def retract_seconds(seconds: float) -> bool:
    if seconds <= 0 or seconds > MAX_DURATION_SECONDS:
        return False

    return _run("reverse", seconds)