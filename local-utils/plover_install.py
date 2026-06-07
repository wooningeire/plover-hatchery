import argparse
from pathlib import Path

from _shared import (
    DEFAULT_PLOVER_EXIT_TIMEOUT,
    DEFAULT_PLOVER_INSTALL_SETTLE_TIME,
    DEFAULT_PLOVER_INSTALL_TIMEOUT,
    DEFAULT_PLOVER_PATH,
    quit_plover,
    run_plover_plugin_install,
)


def _main(args: argparse.Namespace) -> None:
    quit_plover(args.plover_path, exit_timeout=args.plover_exit_timeout)

    plugin_path = Path(__file__).parent.parent.resolve()

    run_plover_plugin_install(
        args.plover_path,
        ["-e", plugin_path],
        install_timeout=args.plover_install_timeout,
        install_settle_time=args.plover_install_settle_time,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    _ = parser.add_argument(
        "--plover-path",
        type=Path,
        help="Path to the directory that directly contains Plover's python_console binary",
        default=DEFAULT_PLOVER_PATH,
    )
    _ = parser.add_argument("--plover-exit-timeout", type=float, default=DEFAULT_PLOVER_EXIT_TIMEOUT)
    _ = parser.add_argument("--plover-install-timeout", type=float, default=DEFAULT_PLOVER_INSTALL_TIMEOUT)
    _ = parser.add_argument("--plover-install-settle-time", type=float, default=DEFAULT_PLOVER_INSTALL_SETTLE_TIME)
    args = parser.parse_args()

    _main(args)
