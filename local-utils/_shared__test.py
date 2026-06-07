from pathlib import Path

import _shared


def test_resolve_plover_console_prefers_install_directory_executable(monkeypatch):
    monkeypatch.setattr(_shared.sys, "platform", "win32")
    monkeypatch.setattr(_shared.shutil, "which", lambda name: None)

    plover_path = Path("C:/Plover")
    executable_path = plover_path / "plover_console.exe"
    monkeypatch.setattr(Path, "exists", lambda path: path == executable_path)

    assert _shared.resolve_plover_console(plover_path) == executable_path


def test_is_plover_process_matches_main_plover_command():
    assert _shared.is_plover_process(
        {
            "pid": 1,
            "name": "python.exe",
            "command_line": r"C:\Plover\python.exe -m plover.scripts.main -l debug",
        }
    )


def test_is_plover_process_ignores_helper_command():
    assert not _shared.is_plover_process(
        {
            "pid": 1,
            "name": "python.exe",
            "command_line": r"C:\Repo\local-utils\plover_debug.py --plover-path C:\Plover",
        }
    )


def test_wait_for_processes_to_exit_returns_unfinished_pids(monkeypatch):
    snapshots = iter(
        [
            [{"pid": 1}, {"pid": 2}],
            [{"pid": 2}],
            [{"pid": 2}],
        ]
    )

    monkeypatch.setattr(_shared, "list_candidate_processes", lambda: next(snapshots))
    monkeypatch.setattr(_shared.time, "monotonic", iter([0, 1, 2, 3]).__next__)
    monkeypatch.setattr(_shared.time, "sleep", lambda _: None)

    assert _shared.wait_for_processes_to_exit({1, 2}, timeout=3, poll_interval=0) == {2}


def test_is_plover_plugin_install_process_matches_target_path():
    assert _shared.is_plover_plugin_install_process(
        {
            "pid": 1,
            "name": "plover_console.exe",
            "command_line": r"C:\Plover\plover_console.exe -s plover_plugins install -e C:\Repo",
        },
        [Path("C:/Repo")],
    )


def test_is_plover_plugin_install_process_ignores_other_install():
    assert not _shared.is_plover_plugin_install_process(
        {
            "pid": 1,
            "name": "python.exe",
            "command_line": r"C:\Plover\python.exe -m pip install C:\Other",
        },
        [Path("C:/Repo")],
    )


def test_wait_for_plover_plugin_install_requires_quiet_period(monkeypatch):
    snapshots = iter(
        [
            [{"pid": 1, "name": "plover_console.exe", "command_line": "plover_plugins install C:/Repo"}],
            [],
            [],
        ]
    )

    monkeypatch.setattr(_shared, "list_candidate_processes", lambda: next(snapshots))
    monkeypatch.setattr(_shared.time, "monotonic", iter([0, 1, 1, 2, 3]).__next__)
    monkeypatch.setattr(_shared.time, "sleep", lambda _: None)

    _shared.wait_for_plover_plugin_install([Path("C:/Repo")], timeout=3, settle_time=1, poll_interval=0)
