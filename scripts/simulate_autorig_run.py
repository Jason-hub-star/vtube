#!/usr/bin/env python3
"""AUTORIG 가짜 런 시뮬레이터 — 관제탑 개발/스모크용.

실제 파이프라인과 동일한 이벤트 컨벤션(autorig_events)으로 P0~P6 + H1/H1.5/H2를 방출한다.
아티팩트는 현재 후보 매니페스트의 실제 PNG를 복사해서 라이브 피드를 채운다.

  --speed 8                8배속 (게이트 대기 시간은 영향 없음)
  --auto-resolve-gates     게이트를 1초 후 자동 승인 (헤드리스 스모크용)
  --run-id smoke-001       런 ID 고정 (기본: sim-<epoch>)
"""

from __future__ import annotations

import argparse
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autorig_events import EventWriter, RUNS_DIR  # noqa: E402

CANDIDATES = (
    ROOT
    / "experiments/cubism-v2-new-character-002/reports/autorig_current_candidates/current_candidates.json"
)

STAGES = [
    ("P0", "캐릭터 설정", 4),
    ("P1", "템플릿 시트 생성", 18),
    ("H1", None, 0),  # 게이트
    ("P2", "추출·캔버스 배치", 12),
    ("H1_5", None, 0),  # 게이트 (메인 배치 검수)
    ("P3", "자동 리깅", 14),
    ("P4", "수치 QA", 8),
    ("P5", "런타임 스윕", 8),
    ("P6", "웹캠 연동", 6),
    ("H2", None, 0),  # 게이트
]

GATES = {
    "H1": {
        "title": "스타일 확인이 필요해요",
        "instructions": "마스터 시트의 그림체와 캐릭터가 맞는지 봐주세요.",
    },
    "H1_5": {
        "title": "파트 배치를 봐주세요",
        "instructions": "어긋난 파트가 있으면 마커를 드래그해서 옮긴 뒤 저장해주세요.",
    },
    "H2": {
        "title": "최종 승인이 필요해요",
        "instructions": "웹캠 연동 결과를 보고 승인해주세요.",
    },
}


def sample_artifacts(count: int) -> list[Path]:
    if not CANDIDATES.exists():
        return []
    entries = json.loads(CANDIDATES.read_text())["entries"]
    picked = entries[:: max(1, len(entries) // count)][:count]
    return [ROOT / e["path"] for e in picked if (ROOT / e["path"]).exists()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--auto-resolve-gates", action="store_true")
    parser.add_argument("--run-id", default=f"sim-{int(time.time())}")
    parser.add_argument("--budget-seconds", type=int, default=3600)
    parser.add_argument("--gate-timeout", type=float, default=3600.0)
    args = parser.parse_args()

    writer = EventWriter(args.run_id, RUNS_DIR)
    writer.run_started("시뮬레이션 런 (character-002)", budget_seconds=args.budget_seconds)
    writer.log("자동화파이프라인 시뮬레이션을 시작해요.")

    artifacts = sample_artifacts(12)
    artifact_iter = iter(artifacts)

    def sleep(seconds: float) -> None:
        time.sleep(max(0.02, seconds / args.speed))

    def emit_artifacts(stage: str, n: int) -> str:
        last = ""
        for _ in range(n):
            src = next(artifact_iter, None)
            if src is None:
                break
            dest = writer.run_dir / "artifacts" / src.name
            shutil.copyfile(src, dest)
            writer.artifact_created(f"artifacts/{src.name}", label=src.stem, stage=stage)
            last = f"artifacts/{src.name}"
            sleep(1.2)
        return last

    last_artifact = ""
    for stage, title, duration in STAGES:
        if stage in GATES:
            gate = GATES[stage]
            parts = []
            if stage == "H1_5":
                parts = [
                    {"part_id": "hair_front_center", "center": [1024, 430], "bbox": [824, 230, 1224, 630]},
                    {"part_id": "eye_L_open", "center": [880, 687], "bbox": [780, 627, 980, 747]},
                    {"part_id": "mouth_line", "center": [1024, 980], "bbox": [924, 930, 1124, 1030]},
                ]
            writer.gate_waiting(stage, gate["title"], gate["instructions"], artifact=last_artifact, parts=parts)
            if args.auto_resolve_gates:
                time.sleep(1.0)
                writer.gate_resolved(stage, "approve", source="auto")
            else:
                resolved = writer.wait_for_gate(stage, timeout=args.gate_timeout)
                if resolved is None:
                    writer.run_failed(f"gate timeout: {stage}")
                    return 1
            writer.log(f"{stage} 게이트가 해결됐어요.")
            continue

        writer.stage_started(stage, title or stage)
        writer.log(f"{stage} {title} 시작")
        steps = 4
        for i in range(1, steps + 1):
            sleep(duration / steps)
            writer.stage_progress(stage, i / steps, note=f"{title} {i}/{steps}")
        if stage == "P1":
            last_artifact = emit_artifacts(stage, 5)
            writer.qa_result("슬롯 점유율", "PASS", value=0.94, detail="18/18 슬롯 충족", stage=stage)
        if stage == "P2":
            last_artifact = emit_artifacts(stage, 4)
            writer.qa_result("알파/크기 검사", "PASS", value="64/64", stage=stage)
        if stage == "P3":
            emit_artifacts(stage, 3)
            writer.qa_result("키폼 바인딩", "PASS", value=15, stage=stage)
        if stage == "P4":
            writer.qa_result("스타일 드리프트", "WARN", value=0.07, detail="기준 0.05 초과, 허용 범위", stage=stage)
        if stage == "P5":
            writer.qa_result("파라미터 스윕", "PASS", value="7/7", stage=stage)
        if stage == "P6":
            writer.qa_result("트래킹 적용", "PASS", value="6 params", stage=stage)
        writer.stage_completed(stage)

    writer.run_completed("PASS")
    writer.log("런이 끝났어요. 수고했어요!")
    print(json.dumps({"run_id": args.run_id, "run_dir": str(writer.run_dir)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
