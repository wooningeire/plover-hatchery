from argparse import Namespace
from pathlib import Path

import profile_plover_startup


def _py_spy_args(duration: float | None) -> Namespace:
    return Namespace(
        duration=duration,
        format="flamegraph",
        full_filenames=False,
        native=True,
        nonblocking=False,
        rate=5,
        threads=True,
    )


def test_build_py_spy_command_omits_duration_by_default():
    command = profile_plover_startup._build_py_spy_command(
        Path("py-spy"),
        123,
        Path("out.svg"),
        _py_spy_args(None),
    )

    assert "--duration" not in command


def test_build_py_spy_command_keeps_explicit_duration():
    command = profile_plover_startup._build_py_spy_command(
        Path("py-spy"),
        123,
        Path("out.svg"),
        _py_spy_args(12.5),
    )

    assert "--duration" in command
    assert "12.5" in command
