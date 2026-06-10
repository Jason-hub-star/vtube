"""이미지 공통 유틸: 알파크롭 썸네일, 컨택트시트, 픽셀 diff. (build_contact_sheet 26벌 복붙의 단일 원본)"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFont


def make_thumb(src: Path, dest: Path, size: int = 256, crop_alpha: bool = True, margin: int = 48) -> Path | None:
    """알파 bbox 기준 자동 크롭 썸네일. 풀캔버스 파트 PNG를 사람이 볼 수 있게 만든다."""
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
            left = max(0, bbox[0] - margin)
            top = max(0, bbox[1] - margin)
            right = min(img.width, bbox[2] + margin)
            bottom = min(img.height, bbox[3] + margin)
            img = img.crop((left, top, right, bottom))
    img.thumbnail((size, size))
    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest)
    return dest


def build_contact_sheet(
    image_paths: list[Path],
    labels: list[str],
    out_path: Path,
    cols: int = 4,
    tile: tuple[int, int] = (360, 250),
) -> Path:
    """라벨 달린 격자 컨택트시트."""
    tile_w, tile_h = tile
    label_h = 28
    thumbs: list[Image.Image] = []
    try:
        font = ImageFont.truetype("Arial.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    for image_path, label in zip(image_paths, labels):
        with Image.open(image_path) as raw:
            image = raw.convert("RGB")
        image.thumbnail((tile_w, tile_h - label_h))
        canvas = Image.new("RGB", (tile_w, tile_h), "white")
        canvas.paste(image, ((tile_w - image.width) // 2, label_h))
        ImageDraw.Draw(canvas).text((10, 7), str(label)[:44], fill=(30, 41, 59), font=font)
        thumbs.append(canvas)
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tile_w, max(rows, 1) * tile_h), (244, 246, 248))
    for idx, thumb in enumerate(thumbs):
        sheet.paste(thumb, ((idx % cols) * tile_w, (idx // cols) * tile_h))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path)
    return out_path


def image_diff_metrics(base_path: Path, target_path: Path, threshold: int = 18) -> dict[str, Any]:
    """두 이미지의 변화량 수치 (changed_ratio/bbox 등). 모션·배치 검증용."""
    with Image.open(base_path) as base_raw, Image.open(target_path) as target_raw:
        base = base_raw.convert("RGBA")
        target = target_raw.convert("RGBA")
        if base.size != target.size:
            target = target.resize(base.size)
        gray = ImageChops.difference(base, target).convert("L")
        width, height = gray.size
        hist = gray.histogram()
        changed = sum(hist[threshold:])
        total_delta = sum(level * count for level, count in enumerate(hist))
        mask = gray.point(lambda px: 255 if px >= threshold else 0)
        bbox_raw = mask.getbbox()
        bbox = None
        if bbox_raw:
            x0, y0, x1, y1 = bbox_raw
            bbox = {"x": x0, "y": y0, "w": x1 - x0, "h": y1 - y0}
        pixel_count = width * height
        return {
            "image_size": [width, height],
            "changed_pixels": changed,
            "changed_ratio": round(changed / pixel_count, 6),
            "mean_delta": round(total_delta / pixel_count, 6),
            "max_delta": max((level for level, count in enumerate(hist) if count), default=0),
            "changed_bbox": bbox,
        }
