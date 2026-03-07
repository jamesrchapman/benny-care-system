import time
from rich.live import Live

from bennycaresystem.adapters.rich_dashboard import build_dashboard
from bennycaresystem.app.mock_snapshot import get_mock_snapshot


def main():

    with Live(build_dashboard({}), refresh_per_second=2, screen=True) as live:

        while True:

            snapshot = get_mock_snapshot()

            live.update(build_dashboard(snapshot))

            time.sleep(1)


if __name__ == "__main__":
    main()