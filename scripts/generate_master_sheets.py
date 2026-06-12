#!/usr/bin/env python3
"""AUTORIG 004+ 생성: gpt-image-2 API로 마스터 + 시트 3장 (입/눈표정/액센트).

Codex 구독 종료 대체 — Codex CLI의 이미지 생성과 동일 모델(gpt-image-2)을 API로 직접 호출.
"동일 세션" 정체성 유지의 API 등가물 = 시트 3장을 images/edits에 마스터를 참조로 넣어 생성.

- 키: ~/.config/vtube/openai_api_key (저장소 밖, 600) — 코드/로그/산출물에 키 비노출.
- 프롬프트: docs/ref/AUTORIG-MASTER-SPEC.md §2(마스터)/§3(입)/§3.2(눈표정)/§3.3(액센트)
  + 조건 9(얇은 초커)/조건 10(리본·옷자락 분리 작화)/§3 wide 셀 부품 분리 조건.
- IP 폴백: 캐릭터 이름 직지정이 거부되면 외형 서술형 프롬프트로 1회 자동 재시도.
- 1024² high 생성 → LANCZOS 2048 업스케일 (스펙 §1 조건 7 — 결정론 업스케일 허용).
- 비용: 요청별 usage 토큰과 달러 추정을 generation_log.json에 기록.

사용:
  python3 scripts/generate_master_sheets.py --out-dir experiments/autorig-character-004/generated
  python3 scripts/generate_master_sheets.py --dry-run   # low 품질 마스터 1장으로 API 왕복 검증
  python3 scripts/generate_master_sheets.py --only mouth --master <기존 마스터.png>
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

import requests
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.vtube_io import ROOT, now_iso, rel, write_json  # noqa: E402

KEY_PATH = Path.home() / ".config/vtube/openai_api_key"
API = "https://api.openai.com/v1"
MODEL = "gpt-image-2"
CANVAS = 2048
# 2026-06 단가 ($/1M tokens): text in 5, image in 8, image out 30 — 추정용 (청구는 OpenAI 콘솔이 SSOT)
PRICE = {"text_in": 5.0, "image_in": 8.0, "image_out": 30.0}

# ── 위벨 (장송의 프리렌) — 이름 직지정(1차) / 서술형 폴백(IP 거부 시) ────────────
UEBEL_NAMED = "Übel from Sousou no Frieren (Frieren: Beyond Journey's End)"
UEBEL_DESC = (
    "an anime female mage character with layered dark-green hair (shoulder length, slightly "
    "messy, two long thin side strands), sharp green eyes with narrow pupils, a faint "
    "mischievous smile, wearing a modest black dress with white trim"
)

MASTER_PROMPT = (
    "Generate a 2048x2048 front-facing upper-body anime illustration of {who}, "
    "single character centered, fully clothed in a modest outfit, simple flat light "
    "background, the neck fully visible (no high collar), wearing a thin dark choker, "
    "bangs not covering the eyes, eyes wide open, "
    "mouth closed with a clearly drawn dark smile line, "
    "hair in distinct left/center/right masses, "
    "ribbons and skirt hem drawn as distinct separable shapes with clear outlines "
    "(not blended into the dress body), anime illustration, clean lineart"
)

MOUTH_PROMPT = (
    "Using this exact character, generate a 2048x2048 sheet on pure magenta #FF00FF "
    "background, 2x2 grid of the character's mouth region with identical lip width and "
    "corner positions: top-left mouth closed (same as reference), top-right slightly open, "
    "bottom-left half open showing teeth, bottom-right wide open showing teeth and tongue. "
    "In the bottom-right cell include the full mouth interior with separable parts: "
    "distinct unbroken upper lip stroke, distinct lower lip stroke, dark solid interior "
    "fill, clearly colored teeth, clearly colored tongue. Same art style, same skin tone. "
    "Mouth region only — do not draw the chin or the face outline."
)

EYES_PROMPT = (
    "Using this exact character, generate a 2048x2048 sheet on pure magenta #FF00FF "
    "background, 2x3 grid (2 rows, 3 columns) of the character's both-eyes region including "
    "eyebrows, identical eye positions, sizes and spacing in every cell: "
    "row1-col1 both eyes closed in happy smiling arcs (^^), "
    "row1-col2 left eye closed in a smiling arc and right eye open exactly as the reference, "
    "row1-col3 both eyes wide open in surprise with small pupils, "
    "row2-col1 both eyes half-lidded and unimpressed (jito-me), "
    "row2-col2 both eyes squeezed tightly shut (><), "
    "row2-col3 both eyes open with heart-shaped pupils. "
    "Same art style, same colors. Eyes region only — do not draw the nose, hair or face outline."
)

ACCENT_PROMPT = (
    "Using this exact character's art style, generate a 2048x2048 sheet on pure magenta "
    "#FF00FF background, 2x2 grid: top-left a pair of soft pink anime blush patches matching "
    "the character's skin tone, top-right a vertical dark-blue gloom shading patch (forehead "
    "shadow), bottom-left a single large anime tear drop, bottom-right a single anime sweat "
    "drop. Flat painterly style matching the reference, each item centered in its cell."
)

JOBS = [("master", None), ("mouth", MOUTH_PROMPT), ("eyes", EYES_PROMPT), ("accent", ACCENT_PROMPT)]


def api_key() -> str:
    if not KEY_PATH.exists():
        raise SystemExit(f"API 키 파일 없음: {KEY_PATH}")
    return KEY_PATH.read_text().strip()


def estimate_usd(usage: dict) -> float:
    text_in = usage.get("input_tokens_details", {}).get("text_tokens", 0)
    image_in = usage.get("input_tokens_details", {}).get("image_tokens", 0)
    out = usage.get("output_tokens", 0)
    return round((text_in * PRICE["text_in"] + image_in * PRICE["image_in"] + out * PRICE["image_out"]) / 1e6, 4)


def is_refusal(resp: requests.Response) -> bool:
    if resp.status_code != 400:
        return False
    msg = str(resp.json().get("error", {})).lower()
    return any(k in msg for k in ("moderation", "content_policy", "safety", "rejected"))


def call_images(key: str, kind: str, prompt: str, quality: str, master_png: Path | None) -> tuple[bytes, dict]:
    """generations(마스터) 또는 edits(시트 — 마스터 참조). 반환: (png bytes, usage)."""
    headers = {"Authorization": f"Bearer {key}"}
    common = {"model": MODEL, "prompt": prompt, "size": "1024x1024", "quality": quality, "n": 1}
    if master_png is None:
        resp = requests.post(f"{API}/images/generations", headers=headers, json=common, timeout=300)
    else:
        with open(master_png, "rb") as f:
            resp = requests.post(
                f"{API}/images/edits", headers=headers,
                data={k: str(v) for k, v in common.items()},
                files={"image": (master_png.name, f, "image/png")}, timeout=300)
    if resp.status_code != 200:
        raise RuntimeError(f"{kind}: HTTP {resp.status_code} {resp.text[:300]}")
    body = resp.json()
    return base64.b64decode(body["data"][0]["b64_json"]), body.get("usage", {})


def generate_one(key: str, kind: str, prompt: str, quality: str, master_png: Path | None,
                 out_dir: Path, log: list[dict]) -> Path:
    """1장 생성 (+IP 폴백 1회) → raw 저장 + 2048 업스케일 저장."""
    attempts = [prompt]
    if UEBEL_NAMED in prompt:
        attempts.append(prompt.replace(UEBEL_NAMED, UEBEL_DESC))  # IP 거부 폴백
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
    parser.add_argument("--out-dir", type=Path, default=Path("experiments/autorig-character-004/generated"))
    parser.add_argument("--only", choices=[k for k, _ in JOBS], default=None)
    parser.add_argument("--master", type=Path, default=None, help="기존 마스터 재사용 (시트만 재생성 시)")
    parser.add_argument("--quality", choices=["low", "medium", "high"], default="high")
    parser.add_argument("--dry-run", action="store_true", help="low 품질 마스터 1장만 — API 왕복·비용 로그 검증")
    args = parser.parse_args()
    out_dir = args.out_dir if args.out_dir.is_absolute() else ROOT / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    key = api_key()
    quality = "low" if args.dry_run else args.quality

    log: list[dict] = []
    master_path = args.master if args.master and args.master.is_absolute() else (ROOT / args.master if args.master else None)
    try:
        for kind, sheet_prompt in JOBS:
            if args.only and kind != args.only:
                continue
            if args.dry_run and kind != "master":
                continue
            if kind == "master":
                if master_path is None:
                    master_path = generate_one(key, "master", MASTER_PROMPT.format(who=UEBEL_NAMED),
                                               quality, None, out_dir, log)
            else:
                if master_path is None or not master_path.exists():
                    raise SystemExit("시트 생성에는 마스터가 필요합니다 (--master 또는 master 선행 생성)")
                # 참조는 raw 1024 우선 (입력 토큰 절약), 없으면 지정 마스터
                ref = out_dir / "master_raw_1024.png"
                generate_one(key, kind, sheet_prompt, quality,
                             ref if ref.exists() else master_path, out_dir, log)
    finally:
        if log:
            total = round(sum(r["estimated_usd"] for r in log), 4)
            write_json(out_dir / "generation_log.json", {
                "generated_at": now_iso(), "model": MODEL, "quality": quality,
                "character": "uebel (Sousou no Frieren)", "requests": log,
                "total_estimated_usd": total})
            print(f"총 추정 비용: ${total} ({len(log)}건) — 로그: {rel(out_dir / 'generation_log.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
