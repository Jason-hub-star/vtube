#!/usr/bin/env python3
"""See-through 분해 진행을 관제탑 이벤트로 중계하는 브리지.

ComfyUI 큐/로그와 출력 디렉토리를 폴링해서 autorig_events 런으로 변환한다.
분해가 끝나면(레이어 산출 or 큐 비움) run_completed 후 종료.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autorig_events import EventWriter  # noqa: E402

COMFY = "http://127.0.0.1:8188"


def queue_state() -> tuple[int, int]:
    try:
        with urllib.request.urlopen(f"{COMFY}/queue", timeout=5) as response:
            q = json.loads(response.read())
        return len(q.get("queue_running", [])), len(q.get("queue_pending", []))
    except Exception:
        return -1, -1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="seethrough-002")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--log", type=Path, default=Path("/tmp/comfyui.log"))
    parser.add_argument("--timeout", type=float, default=5400)
    args = parser.parse_args()

    ev = EventWriter(args.run_id)
    ev.run_started("See-through 마스터 분해 (character-002, 640)", budget_seconds=int(args.timeout), stages=["P0", "P1", "P2"])
    ev.stage_started("P1", "레이어 분해 추론 (MPS)")
    ev.log("ComfyUI에서 분해 추론이 돌고 있어요. 산출 레이어가 생기면 피드에 떠요.")

    seen: set[str] = set()
    last_log_size = 0
    started = time.time()
    idle_after_output = 0
    while time.time() - started < args.timeout:
        running, pending = queue_state()
        # 로그의 새 진행 줄을 이벤트로
        if args.log.exists():
            size = args.log.stat().st_size
            if size > last_log_size:
                tail = args.log.read_text(errors="ignore")[last_log_size:]
                last_log_size = size
                for line in tail.splitlines():
                    if "[SeeThrough]" in line or "Prompt executed" in line or "%" in line[:6]:
                        ev.log(line.strip()[:200])
        # 새 산출 파일을 아티팩트로
        if args.output_dir.exists():
            for png in sorted(args.output_dir.rglob("*.png")):
                if str(png) in seen:
                    continue
                seen.add(str(png))
                dest = ev.run_dir / "artifacts" / png.name
                try:
                    dest.write_bytes(png.read_bytes())
                    ev.artifact_created(f"artifacts/{png.name}", label=png.stem, stage="P1")
                except Exception:
                    pass
        progress = min(0.95, (time.time() - started) / max(args.timeout * 0.4, 600))
        ev.stage_progress("P1", progress, note=f"큐 running={running} pending={pending}, 레이어 {len(seen)}장")
        if seen and running == 0 and pending == 0:
            idle_after_output += 1
            if idle_after_output >= 3:
                break
        else:
            idle_after_output = 0
        time.sleep(20)

    if seen:
        ev.stage_completed("P1")
        ev.qa_result("분해 레이어 수", "PASS", value=len(seen), stage="P1")
        ev.run_completed("PASS")
        ev.log(f"분해 완료 — 레이어 {len(seen)}장. 다음은 2048 정규화예요.")
    else:
        ev.stage_failed("P1", "타임아웃 내 산출 레이어 없음")
        ev.run_failed("no layers produced")
    print(f"layers={len(seen)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
