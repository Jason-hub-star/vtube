#!/usr/bin/env python3
"""AUTORIG 생성: gpt-image-2 API로 마스터 + 시트 3장 (입/눈표정/액센트).

Codex 구독 종료 대체 — Codex CLI의 이미지 생성과 동일 모델(gpt-image-2)을 API로 직접 호출.
"동일 세션" 정체성 유지의 API 등가물 = 시트 3장을 images/edits에 마스터를 참조로 넣어 생성.

AUTORIG-TEMPLATE-001: 캐릭터 외형·표정 성격은 characters/<id>.yaml(--character-spec)에서 주입.
프롬프트 *템플릿*(구조 고정)은 여기 유지, 캐릭터 *변수*만 스펙에서 치환 → 캐릭터 추가 시 코드 불변.

- 키: ~/.config/vtube/openai_api_key (저장소 밖, 600) — 코드/로그/산출물에 키 비노출.
- 프롬프트: docs/ref/AUTORIG-MASTER-SPEC.md §2(마스터)/§3(입)/§3.2(눈표정)/§3.3(액센트).
- IP 폴백: 스펙 ip_named 거부 시 ip_desc(외형 서술형)로 1회 자동 재시도.
- 1024² high 생성 → LANCZOS 2048 업스케일 (스펙 §1 조건 7 — 결정론 업스케일 허용).
- 비용: 요청별 usage 토큰과 달러 추정을 generation_log.json에 기록.

사용:
  python3 scripts/generate_master_sheets.py --character-spec characters/autorig-character-004.yaml
  python3 scripts/generate_master_sheets.py --only mouth --master <기존 마스터.png>
  python3 scripts/generate_master_sheets.py --print-prompts   # 생성 없이 프롬프트만 출력(무회귀/0-코드 검증)
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.character_spec import load_spec  # noqa: E402
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

KEY_PATH = Path.home() / ".config/vtube/openai_api_key"
API = "https://api.openai.com/v1"
MODEL = "gpt-image-2"
CANVAS = 2048
# 2026-06 단가 ($/1M tokens): text in 5, image in 8, image out 30 — 추정용 (청구는 OpenAI 콘솔이 SSOT)
PRICE = {"text_in": 5.0, "image_in": 8.0, "image_out": 30.0}
DEFAULT_SPEC = ROOT / "characters/autorig-character-004.yaml"

# ── 프롬프트 템플릿 (구조 고정) — 캐릭터 변수는 {who}/{style}로 스펙에서 주입 ────────────
MASTER_TEMPLATE = (
    "Generate a 2048x2048 front-facing upper-body anime illustration of {who}, "
    "single character centered, fully clothed in a modest outfit, simple flat light "
    "background, the neck fully visible (no high collar), wearing a thin dark choker, "
    "bangs not covering the eyes, eyes wide open, "
    "mouth closed with a clearly drawn dark smile line, "
    "hair in distinct left/center/right masses, "
    "ribbons and skirt hem drawn as distinct separable shapes with clear outlines "
    "(not blended into the dress body), anime illustration, clean lineart"
)

# 레퍼런스 시드용 (--reference) — 기존 캐릭터 그림을 images/edits로 차렷 정면 마스터로 정리.
# 정체성(머리·의상·색)은 시드가 고정, 자세만 분해하기 좋게 교정(양팔 차렷·손 펴짐·몸 안 가림).
MASTER_EDIT_TEMPLATE = (
    "Using this exact same character (keep the identical hairstyle, hair color, eyes, outfit, "
    "colors and accessories), redraw as a 2048x2048 front-facing UPPER-BODY anime illustration "
    "(head down to the hips) on a plain pure-white background. Single character centered, facing "
    "forward, BOTH ARMS relaxed straight down at the sides — hands NOT on the hips, NOT crossing "
    "or covering the torso, arms clearly separated from the body so the torso outline is fully "
    "visible. Neck fully visible (no high collar covering it), bangs not covering the eyes, eyes "
    "open. The mouth is CLOSED but drawn as a DISTINCT, clearly visible solid dark smile line "
    "(a definite dark mouth line with a gentle upward curve — NOT faint, NOT a barely-visible thin "
    "line); the closed mouth must read clearly against the skin. Hair in distinct left/center/right "
    "masses. Keep the outfit and all colors identical to the reference. Clean lineart, flat anime style."
)

# ★ {style} = 스펙 expression_style — 캐릭터 표정 성격이 입 개방 정도를 결정 (사후 튜닝 삽질 차단)
MOUTH_TEMPLATE = (
    "Using this exact character, generate a 2048x2048 sheet on pure magenta #FF00FF "
    "background, 2x2 grid of the character's mouth region. Character personality: {style}. "
    "Reflect that personality in how much the mouth opens. Make the four cells clearly "
    "different in openness. "
    "CRITICAL: in EVERY cell the mouth corners stay raised following the exact same gentle "
    "upward smile curve as the closed reference mouth, and the UPPER edge of the mouth opening "
    "curves upward at the corners matching that smile line — never a flat horizontal oval. "
    "Identical lip width and corner x-positions across all cells. "
    "Top-left: mouth closed, gentle smile (same as reference). "
    "Top-right: slightly open, a thin dark opening under the smile line. "
    "Bottom-left: half open, clearly showing the upper teeth, corners still smiling. "
    "Bottom-right: clearly open showing upper teeth, dark interior fill and a small tongue, "
    "the upper edge still curving up at the corners like the smile. "
    "In the bottom-right cell keep separable parts: a distinct unbroken upper lip stroke that "
    "follows the upward smile curve, a distinct lower lip stroke, dark solid interior fill, "
    "clearly colored teeth, clearly colored tongue. Same art style, same skin tone. "
    "Mouth region only — do not draw the chin or the face outline."
)

EYES_TEMPLATE = (
    "Using this exact character, generate a 2048x2048 sheet on pure magenta #FF00FF "
    "background, 2x3 grid (2 rows, 3 columns) of the character's both-eyes region including "
    "eyebrows, identical eye positions, sizes and spacing in every cell. "
    "Character personality: {style}. "
    "row1-col1 both eyes closed in happy smiling arcs (^^), "
    "row1-col2 left eye closed in a smiling arc and right eye open exactly as the reference, "
    "row1-col3 both eyes wide open in surprise with small pupils, "
    "row2-col1 both eyes half-lidded and unimpressed (jito-me), "
    "row2-col2 both eyes squeezed tightly shut (><), "
    "row2-col3 both eyes open with heart-shaped pupils. "
    "Same art style, same colors. Eyes region only — do not draw the nose, hair or face outline."
)

ACCENT_TEMPLATE = (  # 캐릭터 무관 (스킨톤만 참조에서 따라감)
    "Using this exact character's art style, generate a 2048x2048 sheet on pure magenta "
    "#FF00FF background, 2x2 grid: top-left a pair of soft pink anime blush patches matching "
    "the character's skin tone, top-right a vertical dark-blue gloom shading patch (forehead "
    "shadow), bottom-left a single large anime tear drop, bottom-right a single anime sweat "
    "drop. Flat painterly style matching the reference, each item centered in its cell."
)

JOB_KINDS = ["master", "mouth", "eyes", "accent"]


def build_prompts(spec: dict) -> dict[str, str]:
    """스펙 변수를 템플릿에 주입해 캐릭터별 프롬프트 4종을 만든다."""
    style = spec["expression_style"]
    return {
        "master": MASTER_TEMPLATE.format(who=spec["ip_named"]),
        "master_edit": MASTER_EDIT_TEMPLATE,
        "mouth": MOUTH_TEMPLATE.format(style=style),
        "eyes": EYES_TEMPLATE.format(style=style),
        "accent": ACCENT_TEMPLATE,
    }


def api_key() -> str:
    if not KEY_PATH.exists():
        raise SystemExit(f"API 키 파일 없음: {KEY_PATH}")
    return KEY_PATH.read_text().strip()


def estimate_usd(usage: dict) -> float:
    text_in = usage.get("input_tokens_details", {}).get("text_tokens", 0)
    image_in = usage.get("input_tokens_details", {}).get("image_tokens", 0)
    out = usage.get("output_tokens", 0)
    return round((text_in * PRICE["text_in"] + image_in * PRICE["image_in"] + out * PRICE["image_out"]) / 1e6, 4)


def call_images(key: str, kind: str, prompt: str, quality: str, master_png: Path | None) -> tuple[bytes, dict]:
    """generations(마스터) 또는 edits(시트 — 마스터 참조). 반환: (png bytes, usage)."""
    headers = {"Authorization": f"Bearer {key}"}
    common = {"model": MODEL, "prompt": prompt, "size": "1024x1024", "quality": quality, "n": 1}
    if master_png is None:
        resp = requests.post(f"{API}/images/generations", headers=headers, json=common, timeout=600)
    else:
        with open(master_png, "rb") as f:
            resp = requests.post(
                f"{API}/images/edits", headers=headers,
                data={k: str(v) for k, v in common.items()},
                files={"image": (master_png.name, f, "image/png")}, timeout=600)
    if resp.status_code != 200:
        raise RuntimeError(f"{kind}: HTTP {resp.status_code} {resp.text[:300]}")
    body = resp.json()
    return base64.b64decode(body["data"][0]["b64_json"]), body.get("usage", {})


def generate_one(key: str, kind: str, prompt: str, quality: str, master_png: Path | None,
                 out_dir: Path, log: list[dict], spec: dict) -> Path:
    """1장 생성 (+IP 폴백 1회) → raw 저장 + 2048 업스케일 저장."""
    attempts = [prompt]
    if spec["ip_named"] in prompt:
        attempts.append(prompt.replace(spec["ip_named"], spec["ip_desc"]))  # IP 거부 폴백
    last_err = None
    for i, p in enumerate(attempts):
        try:
            png, usage = call_images(key, kind, p, quality, master_png)
            raw = out_dir / f"{kind}_raw_1024.png"
            raw.write_bytes(png)
            img = Image.open(raw).convert("RGBA").resize((CANVAS, CANVAS), Image.Resampling.LANCZOS)
            final = out_dir / f"{kind}.png"
            img.save(final)
            log.append({"kind": kind, "attempt": i, "fallback_used": i > 0, "quality": quality,
                        "usage": usage, "estimated_usd": estimate_usd(usage), "out": rel(final)})
            print(f"[{kind}] OK (attempt {i}, ~${estimate_usd(usage)}) -> {rel(final)}")
            return final
        except RuntimeError as e:
            last_err = e
            if "HTTP 400" in str(e) and i + 1 < len(attempts):
                print(f"[{kind}] 거부 감지 — 서술형 폴백 재시도")
                continue
            raise
    raise last_err  # pragma: no cover


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--character-spec", type=Path, default=DEFAULT_SPEC,
                        help="characters/<id>.yaml (외형·표정 성격·색 힌트)")
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="기본: experiments/<spec.id>/generated")
    parser.add_argument("--only", choices=JOB_KINDS, default=None)
    parser.add_argument("--master", type=Path, default=None, help="기존 마스터 재사용 (시트만 재생성 시)")
    parser.add_argument("--reference", type=Path, default=None,
                        help="레퍼런스 PNG 시드 — 마스터를 images/edits로 차렷 정면 정리 생성(정체성 유지)")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="high")
    parser.add_argument("--dry-run", action="store_true", help="low 품질 마스터 1장만 — API 왕복·비용 로그 검증")
    parser.add_argument("--print-prompts", action="store_true",
                        help="생성 없이 프롬프트만 출력 (무회귀/신규 캐릭터 0-코드 검증)")
    args = parser.parse_args()

    spec = load_spec(args.character_spec)
    prompts = build_prompts(spec)
    if args.print_prompts:
        for kind in JOB_KINDS:
            if args.only and kind != args.only:
                continue
            print(f"===== {kind} =====\n{prompts[kind]}\n")
        return 0

    out_dir = args.out_dir or (ROOT / "experiments" / spec["id"] / "generated")
    out_dir = out_dir if out_dir.is_absolute() else ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    key = api_key()
    quality = "low" if args.dry_run else args.quality

    log: list[dict] = []
    master_path = args.master if args.master and args.master.is_absolute() else (ROOT / args.master if args.master else None)
    reference = args.reference if (args.reference is None or args.reference.is_absolute()) else ROOT / args.reference
    if reference is not None and not reference.exists():
        raise SystemExit(f"--reference 없음: {reference}")
    try:
        for kind in JOB_KINDS:
            if args.only and kind != args.only:
                continue
            if args.dry_run and kind != "master":
                continue
            if kind == "master":
                if master_path is None:
                    # 레퍼런스 시드면 images/edits로 차렷 정면 정리, 아니면 텍스트 from-scratch
                    if reference is not None:
                        master_path = generate_one(key, "master", prompts["master_edit"], quality, reference, out_dir, log, spec)
                    else:
                        master_path = generate_one(key, "master", prompts["master"], quality, None, out_dir, log, spec)
            else:
                if master_path is None or not master_path.exists():
                    raise SystemExit("시트 생성에는 마스터가 필요합니다 (--master 또는 master 선행 생성)")
                # 참조는 raw 1024 우선 (입력 토큰 절약), 없으면 지정 마스터
                ref = out_dir / "master_raw_1024.png"
                generate_one(key, kind, prompts[kind], quality,
                             ref if ref.exists() else master_path, out_dir, log, spec)
    finally:
        if log:
            total = round(sum(r["estimated_usd"] for r in log), 4)
            write_json(out_dir / "generation_log.json", {
                "generated_at": now_iso(), "model": MODEL, "quality": quality,
                "character": spec["name"], "character_spec": rel(args.character_spec),
                "requests": log, "total_estimated_usd": total})
            print(f"총 추정 비용: ${total} ({len(log)}건) — 로그: {rel(out_dir / 'generation_log.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
