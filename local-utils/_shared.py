import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, IO


DEFAULT_PLOVER_PATH = Path(r"C:/Program Files/Open Steno Project/Plover 5.1.0")
DEFAULT_PLOVER_PATH_STR = str(DEFAULT_PLOVER_PATH)

DEFAULT_POLL_INTERVAL = 0.1
DEFAULT_PLOVER_QUIT_TIMEOUT = 20.0
DEFAULT_PLOVER_EXIT_TIMEOUT = 60.0
DEFAULT_PLOVER_INSTALL_TIMEOUT = 120.0
DEFAULT_PLOVER_INSTALL_SETTLE_TIME = 2.0

PLOVER_PROCESS_NAMES = {"python.exe", "pythonw.exe", "plover.exe", "plover_console.exe"}

ProcessInfo = dict[str, Any]
OutputTarget = IO[bytes] | int | None


def run_command(
    command: list[str | Path],
    *,
    cwd: Path | None = None,
    stdout: OutputTarget = None,
    stderr: OutputTarget = None,
    timeout: float | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(part) for part in command],
        cwd=cwd,
        stdout=stdout,
        stderr=stderr,
        timeout=timeout,
        check=check,
    )


def resolve_plover_console(plover_path: Path) -> Path:
    names = (
        ["plover_console.exe", "plover_console"]
        if sys.platform == "win32"
        else ["plover_console"]
    )
    for name in names:
        candidate = plover_path / name
        if candidate.exists():
            return candidate

    executable = shutil.which("plover_console")
    if executable:
        return Path(executable)

    return plover_path / names[0]


def run_plover_console(
    plover_path: Path,
    args: list[str | Path],
    *,
    stdout: OutputTarget = None,
    stderr: OutputTarget = None,
    timeout: float | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    return run_command(
        [resolve_plover_console(plover_path), *args],
        cwd=plover_path,
        stdout=stdout,
        stderr=stderr,
        timeout=timeout,
        check=check,
    )


def run_plover_plugin_install(
    plover_path: Path,
    install_args: list[str | Path],
    *,
    stdout: OutputTarget = None,
    stderr: OutputTarget = None,
    install_timeout: float = DEFAULT_PLOVER_INSTALL_TIMEOUT,
    install_settle_time: float = DEFAULT_PLOVER_INSTALL_SETTLE_TIME,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> subprocess.CompletedProcess[bytes]:
    result = run_plover_console(
        plover_path,
        ["-s", "plover_plugins", "install", *install_args],
        stdout=stdout,
        stderr=stderr,
    )
    wait_for_plover_plugin_install(
        install_args,
        timeout=install_timeout,
        settle_time=install_settle_time,
        poll_interval=poll_interval,
    )
    return result


def list_candidate_processes() -> list[ProcessInfo]:
    if sys.platform != "win32":
        raise RuntimeError("Plover process inspection currently supports Windows only.")

    command = """
$ErrorActionPreference = 'Stop'
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -in @('python.exe', 'pythonw.exe', 'plover.exe', 'plover_console.exe') } |
  Select-Object ProcessId, Name, CommandLine |
  ConvertTo-Json -Compress
"""
    result = run_command(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if not result.stdout.strip():
        return []

    raw_processes = json.loads(result.stdout)
    if raw_processes is None:
        return []
    if isinstance(raw_processes, dict):
        raw_processes = [raw_processes]

    processes: list[ProcessInfo] = []
    for process in raw_processes:
        command_line = process.get("CommandLine") or ""
        processes.append(
            {
                "pid": int(process["ProcessId"]),
                "name": process.get("Name") or "",
                "command_line": command_line,
            }
        )
    return processes


def is_plover_process(process: ProcessInfo) -> bool:
    command_line = process["command_line"].lower()
    name = process["name"].lower()
    if name not in PLOVER_PROCESS_NAMES:
        return False
    if "plover_debug.py" in command_line or "plover_send_command" in command_line:
        return False
    return name == "plover.exe" or "-m plover.scripts.main" in command_line


def list_plover_processes() -> list[ProcessInfo]:
    return [process for process in list_candidate_processes() if is_plover_process(process)]


def is_plover_plugin_install_process(process: ProcessInfo, install_args: list[str | Path]) -> bool:
    command_line = process["command_line"].lower()
    name = process["name"].lower()
    if name not in PLOVER_PROCESS_NAMES:
        return False
    if not (
        "plover_plugins" in command_line
        or "pip_wrapper" in command_line
        or "pip" in command_line
    ):
        return False
    if "install" not in command_line:
        return False

    targets = [
        str(arg).lower()
        for arg in install_args
        if not str(arg).startswith("-")
    ]
    return any(target in command_line for target in targets)


def process_exists(pid: int) -> bool:
    if sys.platform == "win32":
        return any(process["pid"] == pid for process in list_candidate_processes())

    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def wait_for_process_exit(pid: int, timeout: float, poll_interval: float = DEFAULT_POLL_INTERVAL) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not process_exists(pid):
            return True
        time.sleep(poll_interval)
    return not process_exists(pid)


def wait_for_processes_to_exit(
    pids: set[int],
    timeout: float,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> set[int]:
    remaining = set(pids)
    deadline = time.monotonic() + timeout
    while remaining and time.monotonic() < deadline:
        running_pids = {process["pid"] for process in list_candidate_processes()}
        remaining &= running_pids
        if remaining:
            time.sleep(poll_interval)
    return remaining


def wait_for_plover_plugin_install(
    install_args: list[str | Path],
    *,
    timeout: float = DEFAULT_PLOVER_INSTALL_TIMEOUT,
    settle_time: float = DEFAULT_PLOVER_INSTALL_SETTLE_TIME,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> None:
    deadline = time.monotonic() + timeout
    quiet_since: float | None = None
    latest_matches: list[ProcessInfo] = []

    while time.monotonic() < deadline:
        matches = [
            process
            for process in list_candidate_processes()
            if is_plover_plugin_install_process(process, install_args)
        ]
        if matches:
            latest_matches = matches
            quiet_since = None
        else:
            now = time.monotonic()
            if quiet_since is None:
                quiet_since = now
            elif now - quiet_since >= settle_time:
                return
        time.sleep(poll_interval)

    pids = [process["pid"] for process in latest_matches]
    raise TimeoutError(f"Timed out waiting for Plover plugin install to finish: {pids}")


def quit_plover(
    plover_path: Path,
    *,
    stdout: OutputTarget = None,
    stderr: OutputTarget = None,
    command_timeout: float = DEFAULT_PLOVER_QUIT_TIMEOUT,
    exit_timeout: float = DEFAULT_PLOVER_EXIT_TIMEOUT,
    poll_interval: float = DEFAULT_POLL_INTERVAL,
) -> bool:
    existing_pids = {process["pid"] for process in list_plover_processes()}
    result = run_plover_console(
        plover_path,
        ["-s", "plover_send_command", "quit"],
        stdout=stdout,
        stderr=stderr,
        timeout=command_timeout,
        check=False,
    )
    if result.returncode != 0 and existing_pids:
        raise RuntimeError(f"Plover quit command failed with exit code {result.returncode}.")
    if not existing_pids:
        return False

    remaining = wait_for_processes_to_exit(existing_pids, exit_timeout, poll_interval)
    if remaining:
        raise TimeoutError(f"Timed out waiting for Plover process(es) to exit: {sorted(remaining)}")
    return True


def stop_process(pid: int) -> None:
    if sys.platform == "win32":
        run_command(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue",
            ],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
