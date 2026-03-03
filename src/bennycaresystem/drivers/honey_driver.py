import time
import RPi.GPIO as GPIO

HONEY_FWD_PWM = 18
HONEY_FWD_EN  = 23
HONEY_REV_PWM = 19
HONEY_REV_EN  = 26

ML_PER_SECOND = 0.35
MAX_ML_PER_COMMAND = 5.0
MAX_DURATION_SECONDS = 15
MIN_INTERVAL_SECONDS = 20

_last_push_time = 0


def _setup():
    GPIO.setmode(GPIO.BCM)

    for pin in (
        HONEY_FWD_PWM,
        HONEY_FWD_EN,
        HONEY_REV_PWM,
        HONEY_REV_EN,
    ):
        GPIO.setup(pin, GPIO.OUT, initial=GPIO.LOW)


_setup()


def _stop():
    GPIO.output(HONEY_FWD_PWM, GPIO.LOW)
    GPIO.output(HONEY_REV_PWM, GPIO.LOW)
    GPIO.output(HONEY_FWD_EN, GPIO.LOW)
    GPIO.output(HONEY_REV_EN, GPIO.LOW)


def _run_forward(duration: float):
    GPIO.output(HONEY_REV_EN, GPIO.LOW)
    GPIO.output(HONEY_REV_PWM, GPIO.LOW)

    GPIO.output(HONEY_FWD_EN, GPIO.HIGH)
    GPIO.output(HONEY_FWD_PWM, GPIO.HIGH)

    time.sleep(duration)
    _stop()


def _run_reverse(duration: float):
    GPIO.output(HONEY_FWD_EN, GPIO.LOW)
    GPIO.output(HONEY_FWD_PWM, GPIO.LOW)

    GPIO.output(HONEY_REV_EN, GPIO.HIGH)
    GPIO.output(HONEY_REV_PWM, GPIO.HIGH)

    time.sleep(duration)
    _stop()


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

    try:
        _run_forward(duration)
        _last_push_time = time.time()
        return True
    except Exception:
        _stop()
        raise


def retract_seconds(seconds: float) -> bool:
    if seconds <= 0 or seconds > MAX_DURATION_SECONDS:
        return False

    try:
        _run_reverse(seconds)
        return True
    except Exception:
        _stop()
        raise