"""Run the app for development in two terminal windows: backend (uvicorn --reload, :8000)
and frontend (pnpm dev, :5173), so each log is visible on its own.

Usage: uv run python scripts/run-app.py      then open http://localhost:5173
Ctrl+C here stops both. Closing either window stops the other too.
On a crash the window stays open (press a key) so the error can be read.
"""

import logging
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
WINDOWS = sys.platform == "win32"
VENV_PYTHON = BACKEND / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")
BACKEND_PORT, FRONTEND_PORT = 8000, 5173

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s [run-app] %(message)s", datefmt="%H:%M:%S"
)
log = logging.getLogger("run-app")


def port_in_use(port: int) -> bool:
    # Vite listens on ::1, uvicorn on 127.0.0.1: check both.
    for host in ("127.0.0.1", "::1"):
        try:
            with socket.create_connection((host, port), timeout=0.3):
                return True
        except OSError:
            pass
    return False


def start(title: str, cmd: list[str], cwd: Path) -> subprocess.Popen[bytes]:
    if not WINDOWS:
        # shortcut: no portable way to open a terminal window; logs share this terminal instead.
        return subprocess.Popen(cmd, cwd=cwd)
    command = subprocess.list2cmdline(cmd)
    # `|| pause` keeps the window open after a crash so the traceback stays readable.
    return subprocess.Popen(
        ["cmd", "/c", f"title {title} && {command} || pause"],
        cwd=cwd,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def stop(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    if WINDOWS:
        # Kill the whole tree: uvicorn's reload worker and vite would otherwise keep the ports.
        subprocess.call(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def wait_until_up(procs: dict[str, subprocess.Popen[bytes]], timeout: float = 60) -> bool:
    deadline = time.monotonic() + timeout
    pending = {"backend": BACKEND_PORT, "frontend": FRONTEND_PORT}
    while pending and time.monotonic() < deadline:
        for name, port in list(pending.items()):
            if procs[name].poll() is not None:
                log.error("%s exited during startup; see its window", name)
                return False
            if port_in_use(port):
                log.info("%s up on :%d", name, port)
                del pending[name]
        time.sleep(0.5)
    if pending:
        log.error("timed out waiting for %s", ", ".join(pending))
    return not pending


def main() -> int:
    if not VENV_PYTHON.exists():
        log.error("no venv at %s; run `uv sync` in backend/ first", VENV_PYTHON)
        return 1
    pnpm = shutil.which("pnpm")  # resolves pnpm.cmd on Windows
    if pnpm is None:
        log.error("pnpm not found on PATH")
        return 1
    if not (FRONTEND / "node_modules").exists():
        log.error("no frontend/node_modules; run `pnpm install` in frontend/ first")
        return 1
    busy = [p for p in (BACKEND_PORT, FRONTEND_PORT) if port_in_use(p)]
    if busy:
        log.error("port(s) %s already in use; is the app already running?", busy)
        return 1

    procs = {
        "backend": start(
            "The System - backend :8000",
            [str(VENV_PYTHON), "-m", "uvicorn", "app.main:app", "--reload"],
            BACKEND,
        ),
        "frontend": start("The System - frontend :5173", [pnpm, "dev"], FRONTEND),
    }
    log.info("started: %s", ", ".join(f"{n} (pid {p.pid})" for n, p in procs.items()))

    code = 0
    try:
        if not wait_until_up(procs):
            code = 1
        else:
            log.info("ready: http://localhost:%d", FRONTEND_PORT)
            log.info("API docs: http://localhost:%d/docs", BACKEND_PORT)
            log.info("Ctrl+C to stop both")
            while all(p.poll() is None for p in procs.values()):
                time.sleep(0.5)
            gone = [name for name, p in procs.items() if p.poll() is not None]
            log.warning("%s stopped; stopping the rest", ", ".join(gone))
    except KeyboardInterrupt:
        log.info("Ctrl+C received")
    finally:
        for name, proc in procs.items():
            stop(proc)
            log.info("%s stopped", name)
    return code


if __name__ == "__main__":
    sys.exit(main())
