#!/usr/bin/env python3
"""Vtube 자산 대시보드 생성기.

current_candidates.json을 기반으로 썸네일이 보이는 정적 HTML 대시보드를 만든다.
- 64-part 후보: 알파 bbox 크롭 썸네일 (풀캔버스라 크롭 없이는 안 보임)
- 소스/컨택트 시트/리그 프로젝트 포함
- 출력: asset_dashboard/index.html (file:// 로 바로 열림, 클릭 시 원본)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from html import escape
from pathlib import Path

from PIL import Image

ROOT = Path("/Users/family/jason/Vtube")
MANIFEST = ROOT / "experiments/cubism-v2-new-character-002/reports/autorig_current_candidates/current_candidates.json"
OUT = ROOT / "asset_dashboard"
THUMBS = OUT / "thumbs"
THUMB_SIZE = 256
CROP_MARGIN = 48

GROUP_ORDER = ["body", "face_base", "eye_L", "eye_R", "brow", "mouth", "hair", "clothing"]
GROUP_KO = {
    "body": "몸", "face_base": "얼굴 베이스", "eye_L": "왼눈", "eye_R": "오른눈",
    "brow": "눈썹", "mouth": "입", "hair": "머리카락", "clothing": "의상",
}

# 전신 합성 시 밴드 쌓기 순서 (아래가 먼저 깔림)
FULL_BAND_ORDER = [
    "hair_back", "body_back", "body_mid", "body_front", "clothing_mid", "clothing_front",
    "face_back", "face_mid", "face_front", "eye_back", "eye_mid", "eye_front",
    "brow_front", "mouth_back", "mouth_mid", "mouth_front", "hair_side", "hair_front",
]
SUFFIX_ORDER = {"back": 0, "mid": 1, "front": 2}
# 중립(뜬 눈/기본) 조립에서 제외할 키포즈성 레이어
NEUTRAL_EXCLUDE_TOKENS = ("closed",)

CONTACT_SHEETS = [
    ("64-part 매니페스트", "experiments/cubism-v2-new-character-002/reports/v22_64part_candidate_manifest/v22_64part_candidate_manifest_contact_sheet.png"),
    ("B2 눈 오버레이 QA", "experiments/cubism-v2-new-character-002/reports/v22_b2_eye_pack/v22_b2_overlay_qa_on_b1_clean_base.png"),
    ("B3 입 개정 오버레이 QA", "experiments/cubism-v2-new-character-002/reports/v22_b3_mouth_pack_revision_v1/v22_b3_revision_v1_overlay_qa_on_b1_clean_base.png"),
    ("B4/B5 보정 오버레이 QA", "experiments/cubism-v2-new-character-002/reports/v22_b4_b5_anchor_corrected_auto_draft/v22_b4_b5_auto_draft_overlay_qa.png"),
    ("EyeOpen 0.27 성공 패턴", "experiments/cubism-v2-new-character-002/reports/model_edit_v7_smooth_mouth_preview/eye_open_027_success_packet/eye_open_027_contact_sheet.png"),
]


def make_thumb(src: Path, name: str, crop_alpha: bool) -> str | None:
    try:
        img = Image.open(src)
        img.load()
    except Exception:
        return None
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    if crop_alpha:
        bbox = img.getchannel("A").getbbox()
        if bbox:
            left = max(0, bbox[0] - CROP_MARGIN)
            top = max(0, bbox[1] - CROP_MARGIN)
            right = min(img.width, bbox[2] + CROP_MARGIN)
            bottom = min(img.height, bbox[3] + CROP_MARGIN)
            img = img.crop((left, top, right, bottom))
    img.thumbnail((THUMB_SIZE, THUMB_SIZE))
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
    out = THUMBS / f"{safe}.png"
    img.save(out)
    return f"thumbs/{out.name}"


def card(thumb: str | None, title: str, sub: str, href: str, badge: str = "", badge_class: str = "") -> str:
    img = (
        f'<img src="{escape(thumb)}" loading="lazy" alt="">' if thumb
        else '<div class="noimg">no preview</div>'
    )
    badge_html = f'<span class="badge {badge_class}">{escape(badge)}</span>' if badge else ""
    return (
        f'<a class="card" href="{escape(href)}" target="_blank">'
        f'<div class="imgbox">{img}</div>'
        f'<div class="meta"><div class="title">{escape(title)}{badge_html}</div>'
        f'<div class="sub">{escape(sub)}</div></div></a>'
    )


def band_sort_key(entry: dict, full: bool) -> tuple:
    band = entry["draw_order_band"]
    if full:
        idx = FULL_BAND_ORDER.index(band) if band in FULL_BAND_ORDER else 99
        return (idx,)
    suffix = band.rsplit("_", 1)[-1]
    return (SUFFIX_ORDER.get(suffix, 1),)


def compose(entries: list[dict], out_path: Path, full: bool) -> Path | None:
    """그룹 파트들을 draw order대로 알파 합성한다. 검수는 낱장이 아니라 이 단위로 한다."""
    usable = [
        e for e in entries
        if not any(token in e["id"] for token in NEUTRAL_EXCLUDE_TOKENS) and (ROOT / e["path"]).exists()
    ]
    if not usable:
        return None
    usable.sort(key=lambda e: band_sort_key(e, full))
    canvas = None
    for entry in usable:
        try:
            layer = Image.open(ROOT / entry["path"]).convert("RGBA")
        except Exception:
            continue
        if canvas is None:
            canvas = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        canvas.alpha_composite(layer)
    if canvas is None:
        return None
    out_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out_path)
    return out_path


def main() -> None:
    data = json.loads(MANIFEST.read_text())
    THUMBS.mkdir(parents=True, exist_ok=True)
    composites_dir = OUT / "composites"

    sections: list[str] = []

    # 1. 소스
    cards = []
    for key, rel in data["sources"].items():
        thumb = make_thumb(ROOT / rel, f"src_{key}", crop_alpha=False)
        cards.append(card(thumb, key, rel, f"../{rel}"))
    sections.append(f'<h2>소스 (character-002)</h2><div class="grid">{"".join(cards)}</div>')

    # 2. 조립 프리뷰 — 검수는 이 단위로 한다 (낱장으로는 품질 판정 불가)
    by_group: dict[str, list[dict]] = {}
    for e in data["entries"]:
        by_group.setdefault(e["group"], []).append(e)
    cards = []
    full_path = compose(data["entries"], composites_dir / "full_assembly.png", full=True)
    if full_path:
        thumb = make_thumb(full_path, "comp_full", crop_alpha=True)
        cards.append(card(thumb, "전신 조립", "전체 64파트 합성 (중립)", f"composites/{full_path.name}"))
    for g in GROUP_ORDER:
        entries = by_group.get(g, [])
        comp_path = compose(entries, composites_dir / f"group_{g}.png", full=False)
        if comp_path:
            thumb = make_thumb(comp_path, f"comp_{g}", crop_alpha=True)
            cards.append(card(thumb, f"{GROUP_KO.get(g, g)} 조립", f"{g} · {len(entries)}파트 합성", f"composites/{comp_path.name}"))
    sections.append(
        '<h2>조립 프리뷰 <span class="hint">검수는 이 단위로 — 눈은 흰자+홍채+동공+하이라이트가 합쳐진 상태로 판정 (closed 키포즈 레이어 제외)</span></h2>'
        f'<div class="grid wide">{"".join(cards)}</div>'
    )

    # 3. 64-part 현재 후보 (그룹별 낱장 — 위치/추출 디버그용)
    n_override = data["self_review"]["overridden_count"]
    sections.append(
        f'<h2>64-part 현재 후보 <span class="hint">({data["self_review"]["total"]}/64, '
        f'최신 보정본 오버라이드 {n_override}개 · 출처: current_candidates.json)</span></h2>'
    )
    for g in GROUP_ORDER:
        cards = []
        for e in by_group.get(g, []):
            rel = e["path"]
            thumb = make_thumb(ROOT / rel, f"part_{e['id']}", crop_alpha=True)
            overridden = e["provenance"] != "base_manifest"
            cards.append(card(
                thumb, e["label_ko"], e["id"], f"../{rel}",
                badge=e["provenance"] if overridden else e["source_batch"],
                badge_class="accent" if overridden else "",
            ))
        sections.append(
            f'<h3>{GROUP_KO.get(g, g)} <span class="hint">{g} · {len(by_group.get(g, []))}파트</span></h3>'
            f'<div class="grid">{"".join(cards)}</div>'
        )

    # 3. 컨택트 시트 / QA 증거
    cards = []
    for title, rel in CONTACT_SHEETS:
        p = ROOT / rel
        if not p.exists():
            continue
        thumb = make_thumb(p, f"sheet_{title}", crop_alpha=False)
        cards.append(card(thumb, title, rel, f"../{rel}"))
    sections.append(f'<h2>컨택트 시트 / QA 증거</h2><div class="grid wide">{"".join(cards)}</div>')

    # 4. 리그 프로젝트 (mini_rig.json)
    cards = []
    for rig in sorted(ROOT.glob("experiments/**/mini_rig.json")):
        if "external_repos" in str(rig):
            continue
        try:
            r = json.loads(rig.read_text())
            parts = r.get("parts") or r.get("layers") or []
            sub = f"parts={len(parts)}" if isinstance(parts, list) else "rig json"
        except Exception:
            sub = "rig json"
        rel = rig.relative_to(ROOT)
        cards.append(card(None, rig.parent.name, f"{sub} · {rel}", f"../{rel}"))
    sections.append(f'<h2>리그 프로젝트 (자체 rig JSON · {len(cards)}개)</h2><div class="grid">{"".join(cards)}</div>')

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    html = f"""<!DOCTYPE html>
<html lang="ko"><head><meta charset="utf-8">
<title>Vtube 자산 대시보드</title>
<style>
  :root {{ color-scheme: dark; }}
  body {{ background:#14151a; color:#e8e8ec; font-family:-apple-system,'Apple SD Gothic Neo',sans-serif; margin:24px; }}
  h1 {{ font-size:22px; }} h2 {{ font-size:17px; margin:28px 0 10px; border-bottom:1px solid #2c2e36; padding-bottom:6px; }}
  h3 {{ font-size:14px; margin:18px 0 8px; color:#b9bcc7; }}
  .hint {{ color:#7b7f8c; font-weight:normal; font-size:12px; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:10px; }}
  .grid.wide {{ grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); }}
  .card {{ background:#1d1f26; border:1px solid #2c2e36; border-radius:10px; overflow:hidden; text-decoration:none; color:inherit; display:flex; flex-direction:column; }}
  .card:hover {{ border-color:#5b8cff; }}
  .imgbox {{ aspect-ratio:1; display:flex; align-items:center; justify-content:center;
    background:repeating-conic-gradient(#23252d 0% 25%, #1a1c22 0% 50%) 0 0/16px 16px; }}
  .imgbox img {{ max-width:100%; max-height:100%; object-fit:contain; }}
  .noimg {{ color:#565a66; font-size:11px; }}
  .meta {{ padding:8px 10px; }}
  .title {{ font-size:12.5px; font-weight:600; display:flex; gap:6px; align-items:center; flex-wrap:wrap; }}
  .sub {{ font-size:10.5px; color:#7b7f8c; margin-top:3px; word-break:break-all; }}
  .badge {{ font-size:9.5px; background:#2c2e36; color:#9aa0ad; border-radius:99px; padding:1px 7px; }}
  .badge.accent {{ background:#23406e; color:#9cc0ff; }}
</style></head><body>
<h1>Vtube 자산 대시보드 <span class="hint">generated {generated} · scripts/build_asset_dashboard.py</span></h1>
<p class="hint">카드를 클릭하면 원본 PNG가 열려요. 파트 썸네일은 알파 bbox 기준 자동 크롭. 파란 배지 = 최신 보정본으로 오버라이드된 파트.</p>
{"".join(sections)}
</body></html>"""
    (OUT / "index.html").write_text(html)
    print(f"wrote {OUT/'index.html'}")
    print(f"thumbs: {len(list(THUMBS.glob('*.png')))}")


if __name__ == "__main__":
    main()
