from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.console import Group


def _kv_panel(title, rows, border="cyan"):
    table = Table.grid(expand=True)
    table.add_column(ratio=2)
    table.add_column(ratio=3)

    for key, value in rows:
        table.add_row(f"[bold]{key}[/bold]", str(value))

    return Panel(table, title=title, border_style=border)


def _title_bar():
    text = Text("BENNY CARE SYSTEM", style="bold white")
    return Panel(Align.center(text), border_style="bright_white")


def _event_log_panel(events):

    table = Table.grid(expand=True)
    table.add_column()

    for event in events[:12]:
        table.add_row(event)

    return Panel(table, title="EVENT LOG", border_style="magenta")


def build_dashboard(snapshot):
    """
    snapshot: dict produced by telemetry service
    """

    pi = snapshot.get("pi_health", {})
    net = snapshot.get("network", {})
    power = snapshot.get("power", {})
    honey = snapshot.get("honey_actuator", {})
    kibble = snapshot.get("kibble_feeder", {})
    cookie = snapshot.get("cookie_dispenser", {})
    safety = snapshot.get("safety", {})
    glucose = snapshot.get("glucose", {})
    camera = snapshot.get("camera", {})
    schedule = snapshot.get("schedule", {})
    heartbeat = snapshot.get("heartbeat", {})
    events = snapshot.get("events", [])

    layout = Layout()

    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )

    layout["header"].update(_title_bar())

    layout["body"].split_column(
        Layout(name="row1"),
        Layout(name="row2"),
        Layout(name="row3"),
        Layout(name="log"),
    )

    layout["row1"].split_row(
        Layout(name="system"),
        Layout(name="network"),
        Layout(name="power"),
    )

    layout["row2"].split_row(
        Layout(name="honey"),
        Layout(name="kibble"),
        Layout(name="cookie"),
    )

    layout["row3"].split_row(
        Layout(name="safety"),
        Layout(name="glucose"),
        Layout(name="camera"),
        Layout(name="schedule"),
    )

    layout["system"].update(
        _kv_panel(
            "PI HEALTH",
            [
                ("uptime", pi.get("uptime")),
                ("cpu temp", pi.get("cpu_temp")),
                ("memory", pi.get("memory")),
                ("disk", pi.get("disk")),
                ("feed_service", pi.get("feed_service")),
                ("camera_service", pi.get("camera_service")),
            ],
            "blue",
        )
    )

    layout["network"].update(
        _kv_panel(
            "NETWORK",
            [
                ("wifi", net.get("wifi")),
                ("signal", net.get("signal")),
                ("internet", net.get("internet")),
                ("ping", net.get("last_ping")),
                ("watch link", net.get("watch_link")),
            ],
            "magenta",
        )
    )

    layout["power"].update(
        _kv_panel(
            "POWER",
            [
                ("5V rail", power.get("5V_rail")),
                ("12V rail", power.get("12V_rail")),
                ("state", power.get("power_state")),
            ],
            "yellow",
        )
    )

    layout["honey"].update(
        _kv_panel(
            "HONEY ACTUATOR",
            [
                ("state", honey.get("state")),
                ("driver", honey.get("driver")),
                ("gpio", honey.get("gpio")),
                ("last cycle", honey.get("last_cycle")),
                ("duration", honey.get("duration")),
                ("cycles today", honey.get("cycles_today")),
                ("faults", honey.get("faults")),
            ],
            "green",
        )
    )

    layout["kibble"].update(
        _kv_panel(
            "KIBBLE FEEDER",
            [
                ("state", kibble.get("state")),
                ("motor driver", kibble.get("motor_driver")),
                ("gpio", kibble.get("gpio")),
                ("last drop", kibble.get("last_drop")),
                ("drops today", kibble.get("drops_today")),
            ],
            "green",
        )
    )

    layout["cookie"].update(
        _kv_panel(
            "COOKIE DISPENSER",
            [
                ("state", cookie.get("state")),
                ("gpio", cookie.get("gpio")),
                ("last drop", cookie.get("last_drop")),
                ("drops today", cookie.get("drops_today")),
            ],
            "green",
        )
    )

    layout["safety"].update(
        _kv_panel(
            "SAFETY SYSTEM",
            [
                ("watchdog", safety.get("watchdog")),
                ("timeout", safety.get("timeout")),
                ("last command", safety.get("last_command")),
                ("next rescue", safety.get("next_rescue")),
                ("action", safety.get("rescue_action")),
            ],
            "red",
        )
    )

    layout["glucose"].update(
        _kv_panel(
            "LIBRE",
            [
                ("glucose", glucose.get("current")),
                ("trend", glucose.get("trend")),
                ("last reading", glucose.get("last_reading")),
                ("sensor age", glucose.get("sensor_age")),
                ("bluetooth", glucose.get("bluetooth")),
            ],
            "cyan",
        )
    )

    layout["camera"].update(
        _kv_panel(
            "CAMERA",
            [
                ("camera", camera.get("camera")),
                ("last frame", camera.get("last_frame")),
                ("stream", camera.get("stream")),
            ],
            "blue",
        )
    )

    layout["schedule"].update(
        _kv_panel(
            "SCHEDULE",
            [
                ("next kibble", schedule.get("next_kibble")),
                ("next cookie", schedule.get("next_cookie")),
                ("rescue check", schedule.get("rescue_check")),
                ("heartbeat", heartbeat.get("system_heartbeat")),
            ],
            "white",
        )
    )

    layout["log"].update(_event_log_panel(events))

    layout["footer"].update(
        Panel(Group(Text("Mock dashboard. Replace snapshot providers with real telemetry.")))
    )

    return layout