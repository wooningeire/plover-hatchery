import argparse
from pathlib import Path

from _shared import (
    DEFAULT_PLOVER_EXIT_TIMEOUT,
    DEFAULT_PLOVER_INSTALL_SETTLE_TIME,
    DEFAULT_PLOVER_INSTALL_TIMEOUT,
    DEFAULT_PLOVER_PATH,
    quit_plover,
    run_command,
    run_plover_plugin_install,
)


def _main(args: argparse.Namespace, rest: list[str]) -> None:
    root_path = Path(__file__).parent.parent.resolve()
    wheels_path = root_path / Path(r"./plover_hatchery_lib_rs/target/wheels/")

    quit_plover(args.plover_path, exit_timeout=args.plover_exit_timeout)

    manifest_path = root_path / Path(r"./plover_hatchery_lib_rs/Cargo.toml")

    run_command(["maturin", "build", "--manifest-path", manifest_path, *rest], cwd=root_path)

    wheel_paths = sorted(wheels_path.glob("*.whl"))
    if not wheel_paths:
        raise RuntimeError(f"No wheels found in {wheels_path}")

    for wheel_path in wheel_paths:
        run_plover_plugin_install(
            args.plover_path,
            [wheel_path, "--force-reinstall"],
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
    args, rest = parser.parse_known_args()

    _main(args, rest)
