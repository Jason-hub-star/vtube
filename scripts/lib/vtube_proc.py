"""프로세스/포트 공통 유틸. (wait_for_server 17벌 복붙의 단일 원본)"""

from __future__ import annotations

import socket
import subprocess
import time


def wait_for_server(host: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"server did not start on {host}:{port}")


def terminate(proc: subprocess.Popen | None, timeout: float = 5.0) -> None:
    """백그라운드 프로세스를 안전하게 종료한다."""
    if proc is None or proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
