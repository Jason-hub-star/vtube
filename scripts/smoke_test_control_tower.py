#!/usr/bin/env python3
"""관제탑 다각도 스모크 (파이썬 측).

1) 라이브러리 단위: 이벤트 append→derive 재생 일치, 손상 라인 스킵 생존
2) API: 시뮬런(고속, 게이트 자동) + 전 엔드포인트 응답/스키마
3) 게이트 왕복: gate_waiting 감지 → POST gate-response → run_completed 도달
4) 크래시 복원: 서버 재시작 후 동일 상태 파생

결과: experiments/autorig-control-tower-001/reports/control_tower_smoke_report.json
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from autorig_events import EventWriter, derive_state, read_events  # noqa: E402

REPORTS = ROOT / "experiments/autorig-control-tower-001/reports"
PORT = 8096
BASE = f"http://127.0.0.1:{PORT}"
RUNS_DIR = ROOT / "runs"

checks: list[dict] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    checks.append({"name": name, "ok": bool(ok), "detail": detail})
    print(f"  {'✅' if ok else '❌'} {name} {detail}")


def get_json(path: str) -> dict:
    with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as response:
        return json.loads(response.read())


def post_json(path: str, payload: dict) -> dict:
    request = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read())


def get_status(path: str) -> int:
    try:
        with urllib.request.urlopen(f"{BASE}{path}", timeout=10) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def wait_for_server(port: int, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError("server did not start")


def start_server() -> subprocess.Popen:
    proc = subprocess.Popen(
        ["python3", str(ROOT / "scripts/run_autorig_control_tower.py"), "--port", str(PORT), "--no-open", "--no-notify"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    wait_for_server(PORT)
    return proc


def stop(proc: subprocess.Popen) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()


def wait_until(predicate, timeout: float = 90.0, interval: float = 0.5):
    deadline = time.time() + timeout
    while time.time() < deadline:
        value = predicate()
        if value:
            return value
        time.sleep(interval)
    return None


def main() -> int:
    print("[1] 라이브러리 단위")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_runs = Path(tmp)
        writer = EventWriter("unit-001", tmp_runs)
        writer.run_started("단위 테스트", budget_seconds=60)
        for i in range(97):
            writer.log(f"event {i}")
        writer.stage_started("P1", "시트 생성")
        writer.run_completed("PASS")
        events = read_events(tmp_runs / "unit-001")
        check("이벤트 100개 기록", len(events) == 100, f"got {len(events)}")
        derived = derive_state(events, run_id="unit-001")
        saved = json.loads((tmp_runs / "unit-001/run_state.json").read_text())
        check("derive == run_state.json", derived == saved)
        check("상태 PASS", derived["status"] == "PASS")
        # 손상 라인 주입
        with (tmp_runs / "unit-001/events.jsonl").open("a") as fh:
            fh.write("{broken json line\n")
        events_after = read_events(tmp_runs / "unit-001")
        check("손상 라인 스킵 생존", len(events_after) == 100)

    print("[2] API 스모크 (시뮬런 자동 게이트)")
    run_id = f"smoke-auto-{int(time.time())}"
    server = start_server()
    sim = subprocess.Popen(
        ["python3", str(ROOT / "scripts/simulate_autorig_run.py"), "--speed", "40", "--auto-resolve-gates", "--run-id", run_id],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        found = wait_until(lambda: any(r["run_id"] == run_id for r in get_json("/api/runs")["runs"]))
        check("런 목록에 등장", bool(found))
        done = wait_until(lambda: get_json(f"/api/runs/{run_id}/state").get("status") == "PASS", timeout=120)
        check("자동 게이트 런 완주(PASS)", bool(done))
        state = get_json(f"/api/runs/{run_id}/state")
        check("스테이지 9개 완료", sum(1 for s in state["stages"].values() if s.get("status") == "DONE") == 7
              and sum(1 for g in state["gates"].values() if g.get("status") == "RESOLVED") == 3,
              f"stages={len(state['stages'])} gates={len(state['gates'])}")
        check("아티팩트 존재", state["counts"]["artifacts"] >= 8, str(state["counts"]))
        check("QA 결과 존재", state["counts"]["qa"] >= 5)
        tail = get_json(f"/api/runs/{run_id}/events?after=0")
        mid = tail["last_seq"] // 2
        tail2 = get_json(f"/api/runs/{run_id}/events?after={mid}")
        check("이벤트 tail 증분", len(tail2["events"]) < len(tail["events"]) and tail2["events"][0]["seq"] > mid)
        artifact_name = Path(state["artifacts"][0]["path"]).name
        check("아티팩트 서빙 200", get_status(f"/runs/{run_id}/artifacts/{artifact_name}") == 200)
        check("썸네일 생성 200", get_status(f"/runs/{run_id}/thumbs/{artifact_name}") == 200)
        check("앱 서빙 200", get_status("/") == 200)
        check("notified.json 기록", (RUNS_DIR / run_id / "notified.json").exists())
        sim.wait(timeout=10)
    finally:
        if sim.poll() is None:
            sim.kill()

    print("[3] 게이트 왕복 (수동 응답)")
    run_id2 = f"smoke-gate-{int(time.time())}"
    sim2 = subprocess.Popen(
        ["python3", str(ROOT / "scripts/simulate_autorig_run.py"), "--speed", "40", "--run-id", run_id2],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        def waiting_gate():
            try:
                state = get_json(f"/api/runs/{run_id2}/state")
            except Exception:
                return None
            for gate_id, gate in state["gates"].items():
                if gate.get("status") == "WAITING":
                    return gate_id
            return None

        resolved_count = 0
        overrides_sent = None
        for _ in range(3):
            gate_id = wait_until(waiting_gate, timeout=60)
            if not gate_id:
                break
            payload = {"gate": gate_id, "decision": "approve", "overrides": {}}
            if gate_id == "H1_5":
                overrides_sent = {"eye_L_open": {"target_anchor": [900, 700]}}
                payload["overrides"] = overrides_sent
            result = post_json(f"/api/runs/{run_id2}/gate-response", payload)
            if result.get("ok"):
                resolved_count += 1
        check("게이트 3개 수동 해결", resolved_count == 3, f"resolved={resolved_count}")
        done2 = wait_until(lambda: get_json(f"/api/runs/{run_id2}/state").get("status") == "PASS", timeout=120)
        check("수동 게이트 런 완주(PASS)", bool(done2))
        events = read_events(RUNS_DIR / run_id2)
        saved_override = next(
            (e for e in events if e.get("type") == "gate_resolved" and e.get("gate") == "H1_5" and e.get("source") == "control_tower"),
            None,
        )
        check("H1.5 오버라이드 JSONL 기록", bool(saved_override and saved_override.get("overrides") == overrides_sent))
        sim2.wait(timeout=10)
    finally:
        if sim2.poll() is None:
            sim2.kill()

    print("[4] 크래시 복원")
    state_before = get_json(f"/api/runs/{run_id2}/state")
    stop(server)
    server = start_server()
    state_after = get_json(f"/api/runs/{run_id2}/state")
    check("서버 재시작 후 상태 동일", state_before == state_after)
    stop(server)

    status = "PASS" if all(c["ok"] for c in checks) else "FAIL"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "test_id": "control_tower_python_smoke",
        "status": status,
        "checks": checks,
        "self_review": {
            "library_unit_pass": all(c["ok"] for c in checks[:4]),
            "api_pass": all(c["ok"] for c in checks[4:14]),
            "gate_roundtrip_pass": all(c["ok"] for c in checks[14:17]),
            "crash_recovery_pass": all(c["ok"] for c in checks[17:]),
            "status": status,
        },
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "control_tower_smoke_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"status": status, "failed": [c for c in checks if not c["ok"]]}, ensure_ascii=False, indent=2))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
