#!/usr/bin/env python3
"""AUTORIG 원커맨드 파이프라인 — "자동화파이프라인 시작".

재료 2장(마스터 + 입 4상태 시트)을 받으면 P0~H2 전 단계를 자동 수행한다.
검증된 단계 스크립트들을 subprocess로 호출하고(재작성 금지), autorig_events로
관제탑(8095)에 실시간 송출, 게이트(H1.5/H2)에서 주인님 판정을 대기한다.

사용:
  python3 scripts/run_autorig_pipeline.py \
    --master experiments/<exp>/true_master_2048.png \
    --mouth-sheet experiments/<exp>/raw_sheets/mouth_states.png \
    --experiment-id autorig-character-003

전제: ComfyUI가 http://127.0.0.1:8188 에서 실행 중 (미기동 시 안내 후 중단).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from autorig_events import EventWriter  # noqa: E402
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

STAGES = ["P0", "P1", "P2", "H1_5", "P3", "P4", "P5", "H2"]
COMFY_URL = "http://127.0.0.1:8188"
COMFY_OUTPUT = ROOT / "experiments/see-through-layer-decomp-001/external_repos/ComfyUI/output"
PREVIEW_PORT = 8062
DRIVE_PORT = 8063


def sh(writer: EventWriter, stage: str, label: str, cmd: list[str], timeout: int = 3600) -> str:
    writer.log(f"{label}: {' '.join(cmd[:6])} ...")
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    tail = (proc.stdout + proc.stderr)[-2000:]
    if proc.returncode != 0:
        writer.stage_failed(stage, f"{label} 실패 (exit {proc.returncode}): {tail[-400:]}")
        raise SystemExit(f"[{stage}] {label} 실패:\n{tail}")
    return proc.stdout


def comfy_alive() -> bool:
    try:
        with urllib.request.urlopen(f"{COMFY_URL}/system_stats", timeout=5):
            return True
    except Exception:
        return False


def latest_layers_json(output_dir: Path, prefix: str) -> Path:
    candidates = sorted(output_dir.glob(f"{prefix}*_layers.json"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        raise SystemExit(f"분해 산출 layers.json 없음: {output_dir}/{prefix}*")
    return candidates[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", type=Path, required=True, help="2048 마스터 PNG")
    parser.add_argument("--mouth-sheet", type=Path, required=True, help="입 4상태 시트 (interior 셀 포함)")
    parser.add_argument("--experiment-id", required=True, help="예: autorig-character-003")
    parser.add_argument("--resolution", type=int, default=640)
    parser.add_argument("--steps", type=int, default=12)
    parser.add_argument("--skip-gates", action="store_true", help="게이트 자동 통과 (드라이런/스모크용)")
    parser.add_argument("--reuse-decomposition", type=Path, default=None,
                        help="기존 분해 layers.json 재사용 — P1(~20분) 생략 (리허설/재실행용)")
    args = parser.parse_args()

    exp = ROOT / "experiments" / args.experiment_id
    exp.mkdir(parents=True, exist_ok=True)
    run_id = f"{args.experiment_id}_{time.strftime('%Y%m%d_%H%M%S')}"
    writer = EventWriter(run_id)
    t_start = time.time()
    writer.run_started(f"AUTORIG 풀런 — {args.experiment_id}", budget_seconds=3600, stages=STAGES)

    def gate(name: str, title: str, instructions: str, artifact: str = "") -> None:
        if args.skip_gates:
            writer.log(f"게이트 {name} 자동 통과 (--skip-gates)")
            return
        writer.gate_waiting(name, title, instructions=instructions, artifact=artifact)
        print(f"\n⏸  게이트 {name}: 관제탑(http://127.0.0.1:8095)에서 판정해주세요 — {title}")
        decision = writer.wait_for_gate(name, timeout=86400)
        if not decision or decision.get("decision") not in ("approve", "pass", "ok"):
            writer.run_failed(f"게이트 {name} 불합격: {decision}")
            raise SystemExit(f"게이트 {name} 불합격")

    try:
        # ---- P0 마스터 검증 -------------------------------------------------
        writer.stage_started("P0", "마스터 검증")
        sh(writer, "P0", "validate_master_image", [
            "python3", "scripts/validate_master_image.py", "--master", str(args.master),
            "--out", str(exp / "reports" / "p0_master_validation.json")])
        writer.qa_result("p0_master", "PASS", stage="P0")
        writer.stage_completed("P0")

        # ---- P1 분해 --------------------------------------------------------
        writer.stage_started("P1", "See-through 분해 (~20분)")
        if args.reuse_decomposition is not None:
            writer.log(f"분해 재사용: {args.reuse_decomposition}")
            writer.stage_completed("P1")
        elif not comfy_alive():
            writer.stage_failed("P1", "ComfyUI 미기동")
            raise SystemExit(f"ComfyUI가 꺼져 있어요. 먼저 실행해주세요: {COMFY_URL}")
        else:
            # 분해 입력은 추론 해상도로 리사이즈
            from PIL import Image  # noqa: PLC0415
            small = exp / f"master_{args.resolution}.png"
            Image.open(args.master).convert("RGB").resize((args.resolution, args.resolution), Image.LANCZOS).save(small)
            sh(writer, "P1", "seethrough", [
                "python3", "scripts/run_comfyui_seethrough_prompt.py",
                "--base-url", COMFY_URL, "--input-image", str(small),
                "--resolution", str(args.resolution), "--steps", str(args.steps),
                "--depth-resolution", "512",
                "--filename-prefix", f"{args.experiment_id}_seethrough",
                "--output-dir", str(COMFY_OUTPUT),
                "--experiment-dir", str(exp)], timeout=7200)
            writer.stage_completed("P1")

        # ---- P2 정규화 → 재스킨 → 어셈블리 → 분해 후 검증 -------------------
        writer.stage_started("P2", "정규화·재스킨·어셈블리")
        layers_json = args.reuse_decomposition or latest_layers_json(COMFY_OUTPUT, f"{args.experiment_id}_seethrough")
        sh(writer, "P2", "normalize", [
            "python3", "scripts/normalize_seethrough_outputs.py",
            "--experiment-id", args.experiment_id, "--experiment-dir", str(exp),
            "--layers-json", str(layers_json)])
        manifest = exp / "layer_manifest.json"
        reskin_dir = exp / "seethrough_true_reskinned"
        sh(writer, "P2", "reskin", [
            "python3", "scripts/reskin_seethrough_layers.py",
            "--manifest", str(manifest), "--original", str(args.master),
            "--out-dir", str(reskin_dir), "--haze-alpha", "28"])
        sh(writer, "P2", "assembly", [
            "python3", "scripts/compose_reskin_assembly.py",
            "--reskin-manifest", str(reskin_dir / "reskin_manifest.json"),
            "--out", str(exp / "reports" / "full_assembly" / "assembly.png")])
        sh(writer, "P2", "분해 후 레이어 검증", [
            "python3", "scripts/validate_master_image.py", "--master", str(args.master),
            "--manifest", str(manifest),
            "--out", str(exp / "reports" / "p2_layer_validation.json")])
        writer.artifact_created(rel(exp / "reports" / "full_assembly" / "assembly.png"), label="어셈블리", stage="P2")
        writer.stage_completed("P2")

        gate("H1_5", "배치·스타일 판정", "어셈블리가 원본과 동일 배치/스타일인지 확인해주세요.",
             artifact=rel(exp / "reports" / "full_assembly" / "assembly.png"))

        # ---- P3 추출 (입·내부·깜빡임·머리·목) --------------------------------
        writer.stage_started("P3", "상태 추출·베이크")
        mouth_line = reskin_dir / "mouth_line.png"
        sh(writer, "P3", "mouth_states", [
            "python3", "scripts/extract_mouth_states.py", "--sheet", str(args.mouth_sheet),
            "--mouth-line", str(mouth_line),
            "--assembly", str(exp / "reports" / "full_assembly" / "assembly.png"),
            "--out-dir", str(exp / "mouth_states")])
        bake_config = exp / "arap_blink_layers" / "arap_blink_config.json"
        bake_config.parent.mkdir(parents=True, exist_ok=True)
        write_json(bake_config, {
            "assembly": rel(exp / "reports" / "full_assembly" / "assembly.png"),
            "eye_white_L": rel(reskin_dir / "L_eye_white.png"),
            "eye_white_R": rel(reskin_dir / "R_eye_white.png"),
            "t_steps": [0.25, 0.5, 0.75, 1.0], "patch_pad": 26, "skin_band": 0.9})
        sh(writer, "P3", "arap_bake", [
            "python3", "scripts/bake_arap_blink_layers.py", "--config", str(bake_config),
            "--out-dir", str(exp / "arap_blink_layers")])
        sh(writer, "P3", "hair_split", [
            "python3", "scripts/split_hair_chunks.py", "--reskin-dir", str(reskin_dir),
            "--out-dir", str(exp / "hair_chunks")])
        sh(writer, "P3", "hidden_neck", [
            "python3", "scripts/build_hidden_neck.py", "--master", str(args.master),
            "--mouth-line", str(mouth_line), "--clothes", str(reskin_dir / "clothes.png"),
            "--face", str(reskin_dir / "face_base.png"), "--out-dir", str(exp / "hidden_neck")])
        writer.stage_completed("P3")

        # ---- P4 리그 빌드 ----------------------------------------------------
        writer.stage_started("P4", "자동 리깅")
        sh(writer, "P4", "build_rig", [
            "python3", "scripts/build_autorig_rig_v0.py",
            "--reskin-manifest", str(reskin_dir / "reskin_manifest.json"),
            "--arap-eye-dir", str(exp / "arap_blink_layers"),
            "--mouth-states-dir", str(exp / "mouth_states"),
            "--hair-chunks-dir", str(exp / "hair_chunks"),
            "--hidden-neck-dir", str(exp / "hidden_neck"),
            "--out-dir", str(exp / "rig_v0_project")])
        writer.artifact_created(rel(exp / "rig_v0_project" / "character.json"), label="rig", stage="P4")
        writer.stage_completed("P4")

        # ---- P5 검증 3종 ------------------------------------------------------
        writer.stage_started("P5", "자동 검증 (validator·mesh·perf)")
        sh(writer, "P5", "validator", [
            "python3", "scripts/validate_mini_cubism_project.py", "--project", str(exp / "rig_v0_project")])
        sh(writer, "P5", "mesh_verify", [
            "python3", "scripts/run_mesh_deform_verify.py", "--project", str(exp / "rig_v0_project"),
            "--out-dir", str(exp / "reports")])
        sh(writer, "P5", "perf", [
            "python3", "scripts/run_rig_perf_test.py", "--project", str(exp / "rig_v0_project"),
            "--out-dir", str(exp / "reports")])
        writer.qa_result("p5_all", "PASS", stage="P5")
        writer.stage_completed("P5")

        # ---- H2 최종 게이트 ----------------------------------------------------
        if not args.skip_gates:
            subprocess.Popen(["python3", "scripts/mini_cubism_preview_server.py",
                              "--project", str(exp / "rig_v0_project"), "--port", str(PREVIEW_PORT)], cwd=ROOT)
            subprocess.Popen(["python3", "scripts/run_mini_cubism_webcam_drive.py",
                              "--project", str(exp / "rig_v0_project"), "--port", str(DRIVE_PORT)], cwd=ROOT)
        gate("H2", "최종 움직임 판정",
             f"리깅 앱 http://127.0.0.1:{PREVIEW_PORT} / 웹캠 드라이브 http://127.0.0.1:{DRIVE_PORT}/drive — FACIAL-TEST-CHECKLIST 기준으로 확인해주세요.")

        elapsed = round(time.time() - t_start)
        write_json(exp / "reports" / "pipeline_run_report.json", {
            "generated_at": now_iso(), "run_id": run_id, "elapsed_seconds": elapsed,
            "elapsed_human": f"{elapsed // 60}분 {elapsed % 60}초", "stages": STAGES, "status": "PASS"})
        writer.log(f"총 소요: {elapsed // 60}분 {elapsed % 60}초 (목표 60분)")
        writer.run_completed("PASS")
        print(f"\n✅ 풀런 완료 — {elapsed // 60}분 {elapsed % 60}초 (run_id={run_id})")
        return 0
    except SystemExit:
        raise
    except Exception as error:  # noqa: BLE001
        writer.run_failed(str(error))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
