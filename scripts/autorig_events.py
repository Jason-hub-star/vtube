#!/usr/bin/env python3
"""AUTORIG 이벤트 로그(JSONL) 공유 라이브러리.

파이프라인/시뮬레이터는 EventWriter로 쓰기만 하고, 관제탑은 read_events/derive_state로
읽기만 한다. 서로 프로세스가 달라도 JSONL 파일이 유일한 접점이다.

이벤트 v1 타입:
  run_started(title, budget_seconds, stages)
  stage_started/stage_progress/stage_completed/stage_failed(stage, ...)
  artifact_created(path, label, stage)
  qa_result(name, status, value, detail, stage)
  gate_waiting(gate, title, instructions, artifact, parts)
  gate_resolved(gate, decision, overrides, source)
  log(message, level)
  run_completed(status) / run_failed(error)
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / "runs"

STAGE_ORDER = ["P0", "P1", "H1", "P2", "H1_5", "P3", "P4", "P5", "P6", "H2"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class EventWriter:
    """runs/<run_id>/events.jsonl에 이벤트를 append하고 run_state.json을 갱신한다."""

    def __init__(self, run_id: str, runs_dir: Path = RUNS_DIR):
        self.run_dir = runs_dir / run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
        (self.run_dir / "artifacts").mkdir(exist_ok=True)
        self.events_path = self.run_dir / "events.jsonl"
        self.run_id = run_id
        self._seq = self._last_seq()

    def _last_seq(self) -> int:
        if not self.events_path.exists():
            return 0
        last = 0
        for event in read_events(self.run_dir):
            last = max(last, event.get("seq", 0))
        return last

    def emit(self, event_type: str, **fields: Any) -> dict:
        self._seq += 1
        event = {"seq": self._seq, "ts": now_iso(), "type": event_type, **fields}
        with self.events_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        state = derive_state(read_events(self.run_dir), run_id=self.run_id)
        (self.run_dir / "run_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")
        return event

    # --- 헬퍼 ---
    def run_started(self, title: str, budget_seconds: int | None = None, stages: list[str] | None = None) -> None:
        self.emit("run_started", title=title, budget_seconds=budget_seconds, stages=stages or STAGE_ORDER)

    def stage_started(self, stage: str, title: str = "") -> None:
        self.emit("stage_started", stage=stage, title=title)

    def stage_progress(self, stage: str, progress: float, note: str = "") -> None:
        self.emit("stage_progress", stage=stage, progress=round(float(progress), 4), note=note)

    def stage_completed(self, stage: str) -> None:
        self.emit("stage_completed", stage=stage)

    def stage_failed(self, stage: str, error: str) -> None:
        self.emit("stage_failed", stage=stage, error=error)

    def artifact_created(self, path: str, label: str = "", stage: str = "") -> None:
        self.emit("artifact_created", path=path, label=label, stage=stage)

    def qa_result(self, name: str, status: str, value: Any = None, detail: str = "", stage: str = "") -> None:
        self.emit("qa_result", name=name, status=status, value=value, detail=detail, stage=stage)

    def gate_waiting(
        self,
        gate: str,
        title: str,
        instructions: str = "",
        artifact: str = "",
        parts: list[dict] | None = None,
    ) -> None:
        self.emit("gate_waiting", gate=gate, title=title, instructions=instructions, artifact=artifact, parts=parts or [])

    def gate_resolved(self, gate: str, decision: str, overrides: dict | None = None, source: str = "pipeline") -> None:
        self.emit("gate_resolved", gate=gate, decision=decision, overrides=overrides or {}, source=source)

    def log(self, message: str, level: str = "info") -> None:
        self.emit("log", message=message, level=level)

    def run_completed(self, status: str = "PASS") -> None:
        self.emit("run_completed", status=status)

    def run_failed(self, error: str) -> None:
        self.emit("run_failed", error=error)

    def wait_for_gate(self, gate: str, poll_seconds: float = 0.5, timeout: float = 3600.0) -> dict | None:
        """gate_resolved(gate)가 나타날 때까지 자신의 JSONL을 폴링한다."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            for event in read_events(self.run_dir):
                if event.get("type") == "gate_resolved" and event.get("gate") == gate:
                    return event
            time.sleep(poll_seconds)
        return None


def read_events(run_dir: Path, after_seq: int = 0) -> list[dict]:
    """JSONL을 읽는다. 손상된 라인은 건너뛴다 (크래시 안전)."""
    events_path = run_dir / "events.jsonl"
    if not events_path.exists():
        return []
    events: list[dict] = []
    for line in events_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("seq", 0) > after_seq:
            events.append(event)
    return events


def derive_state(events: list[dict], run_id: str = "") -> dict:
    """이벤트 재생만으로 현재 런 상태를 복원한다."""
    state: dict[str, Any] = {
        "run_id": run_id,
        "title": "",
        "status": "UNKNOWN",
        "budget_seconds": None,
        "started_at": None,
        "ended_at": None,
        "stage_order": list(STAGE_ORDER),
        "stages": {},
        "gates": {},
        "artifacts": [],
        "qa": [],
        "last_seq": 0,
        "counts": {"events": 0, "artifacts": 0, "qa": 0, "logs": 0},
    }
    for event in events:
        etype = event.get("type")
        state["last_seq"] = max(state["last_seq"], event.get("seq", 0))
        state["counts"]["events"] += 1
        if etype == "run_started":
            state["title"] = event.get("title", "")
            state["budget_seconds"] = event.get("budget_seconds")
            state["started_at"] = event.get("ts")
            state["status"] = "RUNNING"
            if event.get("stages"):
                state["stage_order"] = event["stages"]
        elif etype == "stage_started":
            state["stages"][event["stage"]] = {"status": "RUNNING", "progress": 0.0, "started_at": event.get("ts")}
        elif etype == "stage_progress":
            stage = state["stages"].setdefault(event["stage"], {"status": "RUNNING", "progress": 0.0})
            stage["progress"] = event.get("progress", 0.0)
            if event.get("note"):
                stage["note"] = event["note"]
        elif etype == "stage_completed":
            stage = state["stages"].setdefault(event["stage"], {})
            stage.update({"status": "DONE", "progress": 1.0, "ended_at": event.get("ts")})
        elif etype == "stage_failed":
            stage = state["stages"].setdefault(event["stage"], {})
            stage.update({"status": "FAILED", "error": event.get("error", ""), "ended_at": event.get("ts")})
        elif etype == "artifact_created":
            state["counts"]["artifacts"] += 1
            state["artifacts"].append(
                {"seq": event.get("seq"), "ts": event.get("ts"), "path": event.get("path"), "label": event.get("label", ""), "stage": event.get("stage", "")}
            )
        elif etype == "qa_result":
            state["counts"]["qa"] += 1
            state["qa"].append(
                {"seq": event.get("seq"), "name": event.get("name"), "status": event.get("status"), "value": event.get("value"), "detail": event.get("detail", ""), "stage": event.get("stage", "")}
            )
        elif etype == "gate_waiting":
            state["gates"][event["gate"]] = {
                "status": "WAITING",
                "title": event.get("title", ""),
                "instructions": event.get("instructions", ""),
                "artifact": event.get("artifact", ""),
                "parts": event.get("parts", []),
                "waiting_seq": event.get("seq"),
                "ts": event.get("ts"),
            }
            state["status"] = "GATE_WAITING"
        elif etype == "gate_resolved":
            gate = state["gates"].setdefault(event["gate"], {})
            gate.update({"status": "RESOLVED", "decision": event.get("decision"), "source": event.get("source", ""), "resolved_ts": event.get("ts")})
            if state["status"] == "GATE_WAITING" and not any(g.get("status") == "WAITING" for g in state["gates"].values()):
                state["status"] = "RUNNING"
        elif etype == "log":
            state["counts"]["logs"] += 1
        elif etype == "run_completed":
            state["status"] = event.get("status", "PASS")
            state["ended_at"] = event.get("ts")
        elif etype == "run_failed":
            state["status"] = "FAILED"
            state["error"] = event.get("error", "")
            state["ended_at"] = event.get("ts")
    return state


def list_runs(runs_dir: Path = RUNS_DIR) -> list[dict]:
    if not runs_dir.exists():
        return []
    runs = []
    for run_dir in sorted(runs_dir.iterdir(), reverse=True):
        if not run_dir.is_dir() or not (run_dir / "events.jsonl").exists():
            continue
        state = derive_state(read_events(run_dir), run_id=run_dir.name)
        runs.append(
            {"run_id": run_dir.name, "title": state["title"], "status": state["status"], "started_at": state["started_at"], "ended_at": state["ended_at"], "last_seq": state["last_seq"]}
        )
    return runs
