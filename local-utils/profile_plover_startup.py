import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from _shared import DEFAULT_PLOVER_PATH_STR

ROOT_PATH = Path(__file__).parent.parent
LOADED_RE = re.compile(r"loaded \d+ dictionaries in")


def _main(args: argparse.Namespace) -> None:
    out_path = args.out_path
    out_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    base_path = out_path / f"{args.prefix}-{timestamp}"
    stdout_path = base_path.with_suffix(".stdout.log")
    stderr_path = base_path.with_suffix(".stderr.log")
    pid_path = base_path.with_suffix(".pid.txt")
    report_path = base_path.with_suffix(f".{args.format_extension}")
    py_spy_stdout_path = base_path.with_suffix(".py-spy.stdout.log")
    py_spy_stderr_path = base_path.with_suffix(".py-spy.stderr.log")

    py_spy_path = _resolve_py_spy(args.py_spy)
    plover_console_path = args.plover_path / "plover_console.exe"
    if args.maturin_dev:
        _run_maturin_dev(args, base_path)

    existing_pids = {process["pid"] for process in _list_candidate_processes()}

    with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
        launcher_cmd = [
            sys.executable,
            str(ROOT_PATH / "local-utils" / "plover_debug.py"),
            "--plover-path",
            str(args.plover_path),
        ]
        if args.reinstall:
            launcher_cmd.append("--reinstall")

        target_pid: int | None = None
        launcher = subprocess.Popen(
            launcher_cmd,
            cwd=ROOT_PATH,
            stdout=stdout_file,
            stderr=stderr_file,
        )

        try:
            target = _wait_for_plover_process(existing_pids, args.attach_timeout, args.poll_interval)
            target_pid = target["pid"]
            pid_path.write_text(f"{target_pid}\n")

            py_spy_cmd = _build_py_spy_command(py_spy_path, target_pid, report_path, args)
            with py_spy_stdout_path.open("wb") as py_spy_stdout_file, py_spy_stderr_path.open("wb") as py_spy_stderr_file:
                py_spy = subprocess.Popen(
                    py_spy_cmd,
                    cwd=ROOT_PATH,
                    stdout=py_spy_stdout_file,
                    stderr=py_spy_stderr_file,
                )

                print(f"Attached py-spy to PID {target_pid}; {target['command_line']}")

                loaded_line = _wait_for_loaded_marker(
                    [stderr_path, stdout_path],
                    args.loaded_timeout,
                    args.poll_interval,
                )
                if loaded_line:
                    print(f"Loaded marker: {loaded_line}")
                else:
                    print("WARNING: did not observe dictionary-loaded marker before timeout")

                _wait_or_stop(py_spy, args.py_spy_wait_timeout, "py-spy")
        finally:
            if not args.keep_plover:
                _quit_plover(plover_console_path, args.plover_path, base_path)
                if target_pid is not None:
                    _stop_process(target_pid)
            _wait_or_stop(launcher, args.launcher_wait_timeout, "plover_debug.py")

    if not report_path.exists():
        raise RuntimeError(f"py-spy did not produce report: {report_path}")

    print(f"\x1b[32mReport done! \x1b[33m{report_path}\x1b[0m")


def _resolve_py_spy(py_spy_arg: str | None) -> Path:
    if py_spy_arg:
        return Path(py_spy_arg)

    executable = shutil.which("py-spy")
    if executable:
        return Path(executable)

    script_name = "py-spy.exe" if sys.platform == "win32" else "py-spy"
    venv_executable = ROOT_PATH / ".venv" / ("Scripts" if sys.platform == "win32" else "bin") / script_name
    if venv_executable.exists():
        return venv_executable

    raise RuntimeError("Could not find py-spy. Run `uv sync --dev` or pass `--py-spy`.")


def _list_candidate_processes() -> list[dict[str, Any]]:
    if sys.platform != "win32":
        raise RuntimeError("This profiler currently uses Windows process inspection.")

    command = """
$ErrorActionPreference = 'Stop'
Get-CimInstance Win32_Process |
  Where-Object { $_.Name -in @('python.exe', 'pythonw.exe', 'plover.exe', 'plover_console.exe') } |
  Select-Object ProcessId, Name, CommandLine |
  ConvertTo-Json -Compress
"""
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
        check=True,
        capture_output=True,
        text=True,
    )
    if not result.stdout.strip():
        return []

    raw_processes = json.loads(result.stdout)
    if isinstance(raw_processes, dict):
        raw_processes = [raw_processes]

    processes: list[dict[str, Any]] = []
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


def _wait_for_plover_process(existing_pids: set[int], timeout: float, poll_interval: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for process in _list_candidate_processes():
            if process["pid"] in existing_pids:
                continue
            if _is_plover_debug_process(process):
                return process
        time.sleep(poll_interval)

    raise TimeoutError("Timed out waiting for the Plover debug Python process")


def _is_plover_debug_process(process: dict[str, Any]) -> bool:
    command_line = process["command_line"].lower()
    name = process["name"].lower()
    if name not in {"python.exe", "pythonw.exe", "plover.exe"}:
        return False
    if not re.search(r"(?<!\S)-l\s+debug", command_line):
        return False
    if "plover_debug.py" in command_line or "plover_send_command" in command_line:
        return False
    return "-m plover.scripts.main" in command_line or "plover.exe" in command_line


def _build_py_spy_command(py_spy_path: Path, target_pid: int, report_path: Path, args: argparse.Namespace) -> list[str]:
    command = [
        str(py_spy_path),
        "record",
        "--pid",
        str(target_pid),
        "--output",
        str(report_path),
        "--format",
        args.format,
        "--rate",
        str(args.rate),
        "--duration",
        str(args.duration),
    ]
    if args.threads:
        command.append("--threads")
    if args.native:
        command.append("--native")
    if args.nonblocking:
        command.append("--nonblocking")
    if args.full_filenames:
        command.append("--full-filenames")
    return command


def _run_maturin_dev(args: argparse.Namespace, base_path: Path) -> None:
    stdout_path = base_path.with_suffix(".maturin-dev.stdout.log")
    stderr_path = base_path.with_suffix(".maturin-dev.stderr.log")
    command = [
        sys.executable,
        str(ROOT_PATH / "local-utils" / "maturin_dev.py"),
        "--plover-path",
        str(args.plover_path),
    ]
    print("Running maturin_dev.py before profiling")
    with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
        subprocess.run(command, cwd=ROOT_PATH, stdout=stdout_file, stderr=stderr_file, check=True)


def _wait_for_loaded_marker(log_paths: list[Path], timeout: float, poll_interval: float) -> str | None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        for log_path in log_paths:
            if not log_path.exists():
                continue
            loaded_line = _latest_loaded_line(log_path)
            if loaded_line:
                return loaded_line
        time.sleep(poll_interval)
    return None


def _latest_loaded_line(log_path: Path) -> str | None:
    try:
        lines = log_path.read_text(errors="replace").splitlines()
    except OSError:
        return None

    for line in reversed(lines):
        if LOADED_RE.search(line):
            return line
    return None


def _quit_plover(plover_console_path: Path, plover_path: Path, base_path: Path) -> None:
    if not plover_console_path.exists():
        print(f"WARNING: cannot quit Plover; missing {plover_console_path}")
        return

    stdout_path = base_path.with_suffix(".quit.stdout.log")
    stderr_path = base_path.with_suffix(".quit.stderr.log")
    with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
        try:
            subprocess.run(
                [str(plover_console_path), "-s", "plover_send_command", "quit"],
                cwd=plover_path,
                stdout=stdout_file,
                stderr=stderr_file,
                timeout=20,
                check=False,
            )
        except subprocess.TimeoutExpired:
            print("WARNING: timed out while sending Plover quit command")


def _wait_or_stop(process: subprocess.Popen[bytes], timeout: float, label: str) -> None:
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"WARNING: stopping {label} after timeout")
        process.kill()
        process.wait(timeout=10)


def _stop_process(pid: int) -> None:
    if sys.platform == "win32":
        subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                f"Stop-Process -Id {pid} -Force -ErrorAction SilentlyContinue",
            ],
            check=False,
            capture_output=True,
        )
        return

    try:
        import os
        import signal

        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Profile Plover startup through plover_debug.py with py-spy.")
    _ = parser.add_argument("--plover-path", type=Path, default=Path(DEFAULT_PLOVER_PATH_STR))
    _ = parser.add_argument("--out-path", type=Path, default=ROOT_PATH / "local-utils/py-spy-out")
    _ = parser.add_argument("--prefix", default="plover-startup")
    _ = parser.add_argument("--py-spy")
    _ = parser.add_argument("--rate", type=int, default=5)
    _ = parser.add_argument("--duration", type=int, default=260)
    _ = parser.add_argument("--loaded-timeout", type=float, default=330)
    _ = parser.add_argument("--attach-timeout", type=float, default=30)
    _ = parser.add_argument("--py-spy-wait-timeout", type=float, default=330)
    _ = parser.add_argument("--launcher-wait-timeout", type=float, default=20)
    _ = parser.add_argument("--poll-interval", type=float, default=0.1)
    _ = parser.add_argument("--format", choices=["flamegraph", "raw", "speedscope", "chrometrace"], default="flamegraph")
    _ = parser.add_argument("--format-extension", default="svg")
    _ = parser.add_argument("--no-threads", dest="threads", action="store_false")
    _ = parser.add_argument("--native", action="store_true", default=True)
    _ = parser.add_argument("--nonblocking", action="store_true")
    _ = parser.add_argument("--full-filenames", action="store_true")
    _ = parser.add_argument("--keep-plover", action="store_true")
    _ = parser.add_argument("--reinstall", action="store_true", help="Pass --reinstall through to plover_debug.py.")
    _ = parser.add_argument("--maturin-dev", action="store_true", help="Run local-utils/maturin_dev.py before profiling.")
    parser.set_defaults(threads=True)
    _main(parser.parse_args())
