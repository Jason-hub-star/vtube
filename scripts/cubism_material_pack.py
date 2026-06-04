#!/usr/bin/env python3
"""Build and validate Cubism-import material packs for Vtube."""

from __future__ import annotations

import argparse
import json
import shutil
import struct
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image, ImageFilter


CANVAS = (2048, 2048)
ROOT = Path("/Users/family/jason/Vtube")
PACK_ID = "cubism-material-pack-001"
DEFAULT_PACK = ROOT / "experiments" / PACK_ID
ANCHOR_REPORT = ROOT / "experiments/production-canvas-2048-001/reports/anchor_2048_report.json"
CANONICAL = ROOT / "experiments/production-canvas-2048-001/canonical/canonical_front_2048.png"
MOUTH_REPORT = ROOT / "experiments/mouth-apply-delta-001/reports/mouth_apply_delta_report.json"
BLINK_REPORT = ROOT / "experiments/blink-apply-review-001/reports/blink_apply_review_report.json"


@dataclass(frozen=True)
class BBox:
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h

    def as_list(self) -> list[int]:
        return [self.x, self.y, self.w, self.h]

    def clamp(self) -> "BBox":
        x0 = max(0, self.x)
        y0 = max(0, self.y)
        x1 = min(CANVAS[0], self.right)
        y1 = min(CANVAS[1], self.bottom)
        return BBox(x0, y0, max(0, x1 - x0), max(0, y1 - y0))

    def pad(self, px: int, py: int) -> "BBox":
        return BBox(self.x - px, self.y - py, self.w + px * 2, self.h + py * 2).clamp()

    def intersection_area(self, other: "BBox") -> int:
        x0 = max(self.x, other.x)
        y0 = max(self.y, other.y)
        x1 = min(self.right, other.right)
        y1 = min(self.bottom, other.bottom)
        return max(0, x1 - x0) * max(0, y1 - y0)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def bbox_from_alpha(path: Path, threshold: int = 10) -> BBox | None:
    img = Image.open(path).convert("RGBA")
    alpha = np.array(img)[:, :, 3]
    ys, xs = np.where(alpha > threshold)
    if len(xs) == 0:
        return None
    x0, x1 = int(xs.min()), int(xs.max()) + 1
    y0, y1 = int(ys.min()), int(ys.max()) + 1
    return BBox(x0, y0, x1 - x0, y1 - y0)


def alpha_coverage(path: Path, bbox: BBox | None) -> float:
    if bbox is None or bbox.w == 0 or bbox.h == 0:
        return 0.0
    img = Image.open(path).convert("RGBA")
    alpha = np.array(img.crop((bbox.x, bbox.y, bbox.right, bbox.bottom)))[:, :, 3]
    return round(float(np.count_nonzero(alpha > 10) / alpha.size), 6)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def full_canvas_layer(src: Image.Image, bbox: BBox, dst: Path, blur: float = 0.0) -> None:
    layer = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    crop = src.crop((bbox.x, bbox.y, bbox.right, bbox.bottom))
    if blur:
        crop = crop.filter(ImageFilter.GaussianBlur(blur))
    layer.paste(crop, (bbox.x, bbox.y), crop)
    dst.parent.mkdir(parents=True, exist_ok=True)
    layer.save(dst)


def alpha_slice(src_path: Path, bbox: BBox, dst: Path) -> None:
    src = Image.open(src_path).convert("RGBA")
    layer = Image.new("RGBA", CANVAS, (0, 0, 0, 0))
    crop = src.crop((bbox.x, bbox.y, bbox.right, bbox.bottom))
    layer.paste(crop, (bbox.x, bbox.y), crop)
    dst.parent.mkdir(parents=True, exist_ok=True)
    layer.save(dst)


def rect_from_list(values: list[int]) -> BBox:
    return BBox(int(values[0]), int(values[1]), int(values[2]), int(values[3]))


def manifest_entry(
    *,
    pack: Path,
    layer_name: str,
    role: str,
    side: str | None,
    source_path: Path,
    output_path: Path,
    draw_order: int,
    status: str,
    include_in_import_psd: bool,
    notes: str,
) -> dict:
    bbox = bbox_from_alpha(output_path)
    return {
        "layer_name": layer_name,
        "role": role,
        "side": side,
        "source_path": str(source_path),
        "output_path": str(output_path),
        "canvas_size": list(CANVAS),
        "bbox": bbox.as_list() if bbox else None,
        "alpha_coverage": alpha_coverage(output_path, bbox),
        "draw_order": draw_order,
        "status": status,
        "include_in_import_psd": include_in_import_psd,
        "notes": notes,
        "relative_output_path": str(output_path.relative_to(pack)),
    }


def production_layer_specs(anchor: dict, pack: Path) -> list[dict]:
    metrics = anchor["metrics"]
    subject = rect_from_list(metrics["subject_bbox"])
    face = rect_from_list(metrics["face_roi"])
    left_eye = rect_from_list(metrics["left_eye_roi"])
    right_eye = rect_from_list(metrics["right_eye_roi"])
    mouth = rect_from_list(metrics["mouth_roi"])

    mid_x = subject.x + subject.w // 2
    lower_y = face.bottom - 20
    eye_pad_y = 18

    return [
        {"name": "back_hair", "role": "back_hair", "side": None, "bbox": BBox(subject.x, subject.y, subject.w, int(subject.h * 0.52)).clamp(), "draw": 10},
        {"name": "body", "role": "body", "side": None, "bbox": BBox(subject.x, lower_y, subject.w, subject.bottom - lower_y).clamp(), "draw": 20},
        {"name": "clothes", "role": "clothes", "side": None, "bbox": BBox(subject.x, int(subject.y + subject.h * 0.56), subject.w, int(subject.h * 0.44)).clamp(), "draw": 30},
        {"name": "neck", "role": "neck", "side": None, "bbox": BBox(mid_x - 130, face.bottom - 90, 260, 230).clamp(), "draw": 40},
        {"name": "face_base", "role": "face", "side": None, "bbox": face.pad(40, 30), "draw": 50},
        {"name": "L_eye_white", "role": "eye_white", "side": "L", "bbox": left_eye, "draw": 60},
        {"name": "R_eye_white", "role": "eye_white", "side": "R", "bbox": right_eye, "draw": 61},
        {"name": "L_iris", "role": "iris", "side": "L", "bbox": BBox(left_eye.x + 55, left_eye.y + 28, 92, 88).clamp(), "draw": 70},
        {"name": "R_iris", "role": "iris", "side": "R", "bbox": BBox(right_eye.x + 55, right_eye.y + 28, 92, 88).clamp(), "draw": 71},
        {"name": "L_pupil", "role": "pupil", "side": "L", "bbox": BBox(left_eye.x + 78, left_eye.y + 48, 46, 46).clamp(), "draw": 80},
        {"name": "R_pupil", "role": "pupil", "side": "R", "bbox": BBox(right_eye.x + 78, right_eye.y + 48, 46, 46).clamp(), "draw": 81},
        {"name": "L_highlight", "role": "highlight", "side": "L", "bbox": BBox(left_eye.x + 95, left_eye.y + 33, 36, 34).clamp(), "draw": 90},
        {"name": "R_highlight", "role": "highlight", "side": "R", "bbox": BBox(right_eye.x + 95, right_eye.y + 33, 36, 34).clamp(), "draw": 91},
        {"name": "L_upper_lash", "role": "upper_lash", "side": "L", "bbox": BBox(left_eye.x, left_eye.y, left_eye.w, 52 + eye_pad_y).clamp(), "draw": 100},
        {"name": "R_upper_lash", "role": "upper_lash", "side": "R", "bbox": BBox(right_eye.x, right_eye.y, right_eye.w, 52 + eye_pad_y).clamp(), "draw": 101},
        {"name": "L_lower_lash", "role": "lower_lash", "side": "L", "bbox": BBox(left_eye.x, left_eye.y + 72, left_eye.w, 58).clamp(), "draw": 110},
        {"name": "R_lower_lash", "role": "lower_lash", "side": "R", "bbox": BBox(right_eye.x, right_eye.y + 72, right_eye.w, 58).clamp(), "draw": 111},
        {"name": "L_brow", "role": "brow", "side": "L", "bbox": BBox(left_eye.x - 10, left_eye.y - 90, left_eye.w + 20, 70).clamp(), "draw": 120},
        {"name": "R_brow", "role": "brow", "side": "R", "bbox": BBox(right_eye.x - 10, right_eye.y - 90, right_eye.w + 20, 70).clamp(), "draw": 121},
        {"name": "mouth_line", "role": "mouth_line", "side": None, "bbox": mouth.pad(12, 8), "draw": 130},
        {"name": "mouth_inner", "role": "mouth_inner", "side": None, "bbox": BBox(mouth.x + 28, mouth.y + 20, mouth.w - 56, mouth.h - 36).clamp(), "draw": 131},
        {"name": "teeth", "role": "teeth", "side": None, "bbox": BBox(mouth.x + 38, mouth.y + 18, mouth.w - 76, 28).clamp(), "draw": 132},
        {"name": "tongue", "role": "tongue", "side": None, "bbox": BBox(mouth.x + 42, mouth.y + 62, mouth.w - 84, 34).clamp(), "draw": 133},
        {"name": "L_side_hair", "role": "side_hair", "side": "L", "bbox": BBox(subject.x, face.y, face.x - subject.x + 90, int(subject.h * 0.7)).clamp(), "draw": 140},
        {"name": "R_side_hair", "role": "side_hair", "side": "R", "bbox": BBox(face.right - 90, face.y, subject.right - face.right + 90, int(subject.h * 0.7)).clamp(), "draw": 141},
        {"name": "front_hair", "role": "front_hair", "side": None, "bbox": BBox(face.x - 90, subject.y, face.w + 180, int(face.h * 0.45)).clamp(), "draw": 150},
        {"name": "face_underpaint", "role": "underpaint", "side": None, "bbox": face.pad(30, 30), "draw": 5, "blur": 1.2},
    ]


def selected_wide_mouth_path() -> Path | None:
    path = ROOT / "experiments/mouth-apply-delta-001/layers/set_a_stylematch_wide_open_corrected_full.png"
    return path if path.exists() else None


def build_production_layers(pack: Path) -> list[dict]:
    anchor = load_json(ANCHOR_REPORT)
    canonical = Image.open(CANONICAL).convert("RGBA")
    layers_dir = pack / "production_layers"
    entries: list[dict] = []
    wide_mouth = selected_wide_mouth_path()

    for spec in production_layer_specs(anchor, pack):
        output = layers_dir / f"{spec['name']}.png"
        source = CANONICAL
        if spec["role"] in {"mouth_inner", "teeth", "tongue"} and wide_mouth:
            alpha_slice(wide_mouth, spec["bbox"], output)
            source = wide_mouth
        else:
            full_canvas_layer(canonical, spec["bbox"], output, blur=float(spec.get("blur", 0.0)))
        status = "OBSERVED" if spec["role"] in {"mouth_inner", "teeth", "tongue"} else "REVISE"
        entries.append(
            manifest_entry(
                pack=pack,
                layer_name=spec["name"],
                role=spec["role"],
                side=spec["side"],
                source_path=source,
                output_path=output,
                draw_order=spec["draw"],
                status=status,
                include_in_import_psd=True,
                notes="Bootstrap production candidate; requires Cubism import and rigger visual review.",
            )
        )
    return entries


def copy_reference_pack(pack: Path) -> list[dict]:
    entries: list[dict] = []
    ref = pack / "reference_pack"
    mouth_report = load_json(MOUTH_REPORT)
    blink_report = load_json(BLINK_REPORT)

    for candidate in mouth_report.get("candidates", []):
        src = Path(candidate["corrected_layer"])
        dst = ref / "mouth" / src.name
        copy_file(src, dst)
        entries.append(
            manifest_entry(
                pack=pack,
                layer_name=src.stem,
                role="mouth_keypose_reference",
                side=None,
                source_path=src,
                output_path=dst,
                draw_order=0,
                status="REFERENCE_ONLY",
                include_in_import_psd=False,
                notes=f"Reference for {candidate.get('expression')} / ParamMouthOpenY and ParamMouthForm, not a production frame layer.",
            )
        )
        overlay = Path(candidate["corrected_overlay"])
        if overlay.exists():
            copy_file(overlay, ref / "overlays" / overlay.name)

    for stage in blink_report.get("stages", []):
        src = Path(stage["corrected_layer"])
        dst = ref / "blink" / src.name
        copy_file(src, dst)
        entries.append(
            manifest_entry(
                pack=pack,
                layer_name=src.stem,
                role="blink_keypose_reference",
                side=None,
                source_path=src,
                output_path=dst,
                draw_order=0,
                status="REFERENCE_ONLY",
                include_in_import_psd=False,
                notes=f"Reference for {stage.get('stage')} / ParamEyeLOpen and ParamEyeROpen, not production blink runtime.",
            )
        )
        overlay = Path(stage["corrected_overlay"])
        if overlay.exists():
            copy_file(overlay, ref / "overlays" / overlay.name)

    for report in [
        MOUTH_REPORT,
        ROOT / "experiments/mouth-apply-delta-001/reports/mouth_shortlist_report.json",
        ROOT / "experiments/mouth-apply-delta-001/reports/qa_report.md",
        BLINK_REPORT,
        ROOT / "experiments/blink-stage-001/reports/blink_stage_review.json",
        ROOT / "experiments/blink-stage-001/reports/qa_report.md",
    ]:
        if report.exists():
            copy_file(report, ref / "reports" / report.name)
    return entries


def _pack_uint16(value: int) -> bytes:
    return struct.pack(">H", value)


def _pack_int16(value: int) -> bytes:
    return struct.pack(">h", value)


def _pack_uint32(value: int) -> bytes:
    return struct.pack(">I", value)


def _pascal_name(name: str) -> bytes:
    raw = name.encode("ascii", errors="replace")[:255]
    data = bytes([len(raw)]) + raw
    pad = (4 - (len(data) % 4)) % 4
    return data + (b"\0" * pad)


def write_layered_psd(path: Path, layer_entries: Iterable[dict]) -> str:
    try:
        write_layered_psd_psd_tools(path, layer_entries)
        return "psd-tools"
    except ImportError as exc:
        raise RuntimeError(
            "psd-tools is required for Cubism-compatible PSD generation. "
            "Install with: python3 -m pip install -r /Users/family/jason/Vtube/requirements-cubism-psd.txt"
        ) from exc


def write_layered_psd_psd_tools(path: Path, layer_entries: Iterable[dict]) -> None:
    from psd_tools import PSDImage

    layer_entries = sorted(layer_entries, key=lambda item: item["draw_order"])
    psd = PSDImage.new("RGB", CANVAS, color=(0, 0, 0))
    for entry in layer_entries:
        src = Path(entry["output_path"])
        bbox = bbox_from_alpha(src)
        if bbox is None:
            continue
        img = Image.open(src).convert("RGBA").crop((bbox.x, bbox.y, bbox.right, bbox.bottom))
        layer = psd.create_pixel_layer(img, name=entry["layer_name"], top=bbox.y, left=bbox.x)
        psd.append(layer)
    path.parent.mkdir(parents=True, exist_ok=True)
    psd.save(path)


def write_layered_psd_raw(path: Path, layer_entries: Iterable[dict]) -> None:
    layer_entries = sorted(layer_entries, key=lambda item: item["draw_order"])
    layer_records: list[bytes] = []
    channel_payloads: list[bytes] = []
    composite = Image.new("RGBA", CANVAS, (0, 0, 0, 0))

    for entry in layer_entries:
        img = Image.open(entry["output_path"]).convert("RGBA")
        bbox = bbox_from_alpha(Path(entry["output_path"]))
        if bbox is None:
            continue
        crop = img.crop((bbox.x, bbox.y, bbox.right, bbox.bottom))
        arr = np.array(crop)
        channels = [
            (0, arr[:, :, 0].tobytes()),
            (1, arr[:, :, 1].tobytes()),
            (2, arr[:, :, 2].tobytes()),
            (-1, arr[:, :, 3].tobytes()),
        ]
        record = bytearray()
        record += _pack_uint32(bbox.y)
        record += _pack_uint32(bbox.x)
        record += _pack_uint32(bbox.bottom)
        record += _pack_uint32(bbox.right)
        record += _pack_uint16(len(channels))
        payload = bytearray()
        for channel_id, data in channels:
            record += _pack_int16(channel_id)
            record += _pack_uint32(2 + len(data))
            payload += _pack_uint16(0)
            payload += data
        record += b"8BIM"
        record += b"norm"
        record += bytes([255, 0, 0, 0])
        extra = bytearray()
        extra += _pack_uint32(0)
        extra += _pack_uint32(0)
        extra += _pascal_name(entry["layer_name"])
        record += _pack_uint32(len(extra))
        record += extra
        layer_records.append(bytes(record))
        channel_payloads.append(bytes(payload))
        composite.alpha_composite(img)

    layer_info = bytearray()
    layer_info += _pack_int16(len(layer_records))
    for record in layer_records:
        layer_info += record
    for payload in channel_payloads:
        layer_info += payload
    if len(layer_info) % 2:
        layer_info += b"\0"

    layer_mask_body = bytearray()
    layer_mask_body += _pack_uint32(len(layer_info))
    layer_mask_body += layer_info
    layer_mask_body += _pack_uint32(0)

    comp = np.array(composite.convert("RGB"))
    composite_data = _pack_uint16(0) + comp[:, :, 0].tobytes() + comp[:, :, 1].tobytes() + comp[:, :, 2].tobytes()

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.write(b"8BPS")
        handle.write(_pack_uint16(1))
        handle.write(b"\0" * 6)
        handle.write(_pack_uint16(3))
        handle.write(_pack_uint32(CANVAS[1]))
        handle.write(_pack_uint32(CANVAS[0]))
        handle.write(_pack_uint16(8))
        handle.write(_pack_uint16(3))
        handle.write(_pack_uint32(0))
        handle.write(_pack_uint32(0))
        handle.write(_pack_uint32(len(layer_mask_body)))
        handle.write(layer_mask_body)
        handle.write(composite_data)


def psd_metadata(path: Path) -> dict:
    if not path.exists():
        return {"exists": False}
    data = path.read_bytes()
    if data[:4] != b"8BPS":
        return {"exists": True, "valid_header": False}
    channels = struct.unpack(">H", data[12:14])[0]
    height = struct.unpack(">I", data[14:18])[0]
    width = struct.unpack(">I", data[18:22])[0]
    depth = struct.unpack(">H", data[22:24])[0]
    color_mode = struct.unpack(">H", data[24:26])[0]
    offset = 26
    color_mode_len = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4 + color_mode_len
    resources_len = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4 + resources_len
    layer_mask_len = struct.unpack(">I", data[offset : offset + 4])[0]
    offset += 4
    layer_count = 0
    if layer_mask_len >= 6:
        layer_info_len = struct.unpack(">I", data[offset : offset + 4])[0]
        if layer_info_len >= 2:
            layer_count = abs(struct.unpack(">h", data[offset + 4 : offset + 6])[0])
    return {
        "exists": True,
        "valid_header": True,
        "channels": channels,
        "width": width,
        "height": height,
        "depth": depth,
        "color_mode": "RGB" if color_mode == 3 else color_mode,
        "layer_mask_section_length": layer_mask_len,
        "layer_count": layer_count,
    }


def param_map_payload(pack: Path) -> dict:
    ref = pack / "reference_pack"
    return {
        "experiment_id": PACK_ID,
        "date": str(date.today()),
        "parameters": {
            "ParamEyeLOpen": {
                "open": {"value": 1.0, "reference": str(CANONICAL)},
                "half": {"value": 0.5, "reference": str(ref / "blink/blink_half_corrected_full.png")},
                "mostly_closed": {"value": 0.2, "reference": str(ref / "blink/blink_mostly_closed_corrected_full.png")},
                "closed": {"value": 0.0, "reference": str(ref / "blink/blink_closed_corrected_full.png")},
            },
            "ParamEyeROpen": {
                "open": {"value": 1.0, "reference": str(CANONICAL)},
                "half": {"value": 0.5, "reference": str(ref / "blink/blink_half_corrected_full.png")},
                "mostly_closed": {"value": 0.2, "reference": str(ref / "blink/blink_mostly_closed_corrected_full.png")},
                "closed": {"value": 0.0, "reference": str(ref / "blink/blink_closed_corrected_full.png")},
            },
            "ParamMouthOpenY": {
                "neutral_smile": {"value": 0.0, "reference_glob": str(ref / "mouth/*neutral_smile*_corrected_full.png")},
                "small_open": {"value": 0.3, "reference_glob": str(ref / "mouth/*small_open*_corrected_full.png")},
                "o_vowel": {"value": 0.5, "reference_glob": str(ref / "mouth/*o_vowel*_corrected_full.png")},
                "wide_or_happy_open": {"value": 0.85, "reference_glob": str(ref / "mouth/*open*_corrected_full.png")},
            },
            "ParamMouthForm": {
                "smile": {"value": 1.0, "reference_glob": str(ref / "mouth/*smile*_corrected_full.png")},
                "round": {"value": -1.0, "reference_glob": str(ref / "mouth/*o_vowel*_corrected_full.png")},
                "neutral": {"value": 0.0, "reference": str(CANONICAL)},
            },
        },
        "notes": [
            "References are key-pose guides for Cubism keyforms, not production frame-swap layers.",
            "Blink remains REVISE/REFERENCE_ONLY until a passing Cubism visual review exists.",
        ],
    }


def build_pack(args: argparse.Namespace) -> None:
    pack = Path(args.pack)
    pack.mkdir(parents=True, exist_ok=True)
    entries = build_production_layers(pack)
    entries.extend(copy_reference_pack(pack))
    entries.sort(key=lambda item: (not item["include_in_import_psd"], item["draw_order"], item["layer_name"]))
    save_json(pack / "layer_manifest.json", {"experiment_id": PACK_ID, "date": str(date.today()), "layers": entries})
    save_json(pack / "param_map.json", param_map_payload(pack))
    writer = write_layered_psd(pack / "import_ready_candidate.psd", [e for e in entries if e["include_in_import_psd"]])
    save_json(pack / "reports/psd_writer_report.json", {"date": str(date.today()), "writer": writer})
    export_handoff_file(pack)
    validate_pack(argparse.Namespace(pack=str(pack), promote=True))


REQUIRED_ROLES = {
    "face",
    "neck",
    "body",
    "clothes",
    "front_hair",
    "side_hair",
    "back_hair",
    "eye_white",
    "iris",
    "pupil",
    "highlight",
    "upper_lash",
    "lower_lash",
    "brow",
    "mouth_line",
    "mouth_inner",
    "teeth",
    "tongue",
    "underpaint",
}


def validate_manifest(pack: Path, manifest: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    layers = manifest.get("layers", [])
    seen: set[str] = set()
    production = [layer for layer in layers if layer.get("include_in_import_psd")]
    prod_roles = {layer.get("role") for layer in production}

    required_fields = {
        "layer_name",
        "role",
        "side",
        "source_path",
        "output_path",
        "canvas_size",
        "bbox",
        "alpha_coverage",
        "draw_order",
        "status",
        "include_in_import_psd",
    }
    for layer in layers:
        missing = required_fields - set(layer)
        if missing:
            errors.append(f"{layer.get('layer_name', '<unknown>')}: missing fields {sorted(missing)}")
        name = layer.get("layer_name")
        if name in seen:
            errors.append(f"duplicate layer_name: {name}")
        seen.add(name)
        if layer.get("status") in {"FAIL", "DISCARDED"} and layer.get("include_in_import_psd"):
            errors.append(f"{name}: FAIL/DISCARDED cannot be included in import PSD")
        if layer.get("role", "").endswith("_reference") and layer.get("include_in_import_psd"):
            errors.append(f"{name}: reference layer cannot be included in import PSD")
        if layer.get("include_in_import_psd") and not layer.get("bbox"):
            errors.append(f"{name}: production layer has empty alpha")
        if layer.get("canvas_size") != list(CANVAS):
            errors.append(f"{name}: canvas_size must be {CANVAS}")

    missing_roles = REQUIRED_ROLES - prod_roles
    if missing_roles:
        errors.append(f"missing required production roles: {sorted(missing_roles)}")

    orders = [layer["draw_order"] for layer in production]
    if orders != sorted(orders):
        errors.append("production layer draw_order is not ascending")

    anchor = load_json(ANCHOR_REPORT)["metrics"]
    rois = {
        "L": rect_from_list(anchor["left_eye_roi"]),
        "R": rect_from_list(anchor["right_eye_roi"]),
        "mouth": rect_from_list(anchor["mouth_roi"]),
    }
    for layer in production:
        bbox = rect_from_list(layer["bbox"]) if layer.get("bbox") else None
        if not bbox:
            continue
        role = layer["role"]
        side = layer.get("side")
        if role in {"eye_white", "iris", "pupil", "highlight", "upper_lash", "lower_lash"} and side in {"L", "R"}:
            if bbox.intersection_area(rois[side]) == 0:
                warnings.append(f"{layer['layer_name']}: does not overlap {side} eye ROI")
        if role.startswith("mouth") or role in {"teeth", "tongue"}:
            if bbox.intersection_area(rois["mouth"]) == 0:
                warnings.append(f"{layer['layer_name']}: does not overlap mouth ROI")

    return errors, warnings


def cubism_smoke_payload(pack: Path) -> dict | None:
    smoke = pack / "reports/cubism_import_smoke.json"
    if not smoke.exists():
        return None
    return load_json(smoke)


def validate_pack(args: argparse.Namespace) -> None:
    pack = Path(args.pack)
    manifest_path = pack / "layer_manifest.json"
    manifest = load_json(manifest_path)
    writer_report_path = pack / "reports/psd_writer_report.json"
    writer_report = load_json(writer_report_path) if writer_report_path.exists() else {"writer": "unknown"}
    errors, warnings = validate_manifest(pack, manifest)
    psd_meta = psd_metadata(pack / "import_ready_candidate.psd")
    if not psd_meta.get("exists"):
        errors.append("import_ready_candidate.psd is missing")
    else:
        for key, expected in [("channels", 3), ("width", 2048), ("height", 2048), ("depth", 8), ("color_mode", "RGB")]:
            if psd_meta.get(key) != expected:
                errors.append(f"PSD metadata {key}={psd_meta.get(key)!r}, expected {expected!r}")
        if int(psd_meta.get("layer_count", 0)) <= 1:
            errors.append("PSD layer_count must be greater than 1")

    smoke = cubism_smoke_payload(pack)
    cubism_status = "PENDING"
    if smoke:
        success = bool(smoke.get("cubism_import_success")) and not bool(smoke.get("layers_flattened"))
        cubism_status = "PASS" if success else "FAIL"
        if success and getattr(args, "promote", False):
            copy_file(pack / "import_ready_candidate.psd", pack / "import_ready.psd")
        elif not success:
            errors.append("Cubism import smoke did not pass")

    status = "PASS_WITH_CUBISM_IMPORT" if not errors and cubism_status == "PASS" else "PASS_PENDING_CUBISM_IMPORT" if not errors else "FAIL"
    report = {
        "experiment_id": PACK_ID,
        "date": str(date.today()),
        "status": status,
        "checks": {
            "manifest_schema": "PASS" if not [e for e in errors if "missing fields" in e] else "FAIL",
            "duplicate_layer_names": "PASS" if not [e for e in errors if e.startswith("duplicate")] else "FAIL",
            "required_production_roles": "PASS" if not [e for e in errors if e.startswith("missing required")] else "FAIL",
            "reference_layers_excluded_from_import_psd": "PASS" if not [e for e in errors if "reference layer" in e] else "FAIL",
            "psd_metadata": "PASS" if psd_meta.get("valid_header") and psd_meta.get("layer_count", 0) > 1 else "FAIL",
            "cubism_import_smoke": cubism_status,
        },
        "psd_metadata": psd_meta,
        "psd_writer": writer_report,
        "errors": errors,
        "warnings": warnings,
        "acceptance": {
            "import_ready_psd_promoted": (pack / "import_ready.psd").exists(),
            "acceptance_gate": "Cubism Editor actual import must pass before import_ready.psd is trusted.",
        },
    }
    save_json(pack / "reports/validation_report.json", report)
    write_qa_report(pack, report)
    if errors:
        raise SystemExit(1)


def write_qa_report(pack: Path, report: dict) -> None:
    lines = [
        f"# {PACK_ID} QA Report",
        "",
        f"Date: {report['date']}",
        f"Status: {report['status']}",
        "",
        "## Checks",
        "",
    ]
    for key, value in report["checks"].items():
        lines.append(f"- `{key}`: {value}")
    lines.extend(["", "## PSD Metadata", "", "```json", json.dumps(report["psd_metadata"], indent=2), "```", ""])
    lines.extend(["## PSD Writer", "", "```json", json.dumps(report["psd_writer"], indent=2), "```", ""])
    if report["warnings"]:
        lines.extend(["## Warnings", ""])
        lines.extend([f"- {item}" for item in report["warnings"]])
        lines.append("")
    if report["errors"]:
        lines.extend(["## Errors", ""])
        lines.extend([f"- {item}" for item in report["errors"]])
        lines.append("")
    lines.extend(
        [
            "## Cubism Import Gate",
            "",
            (
                "Cubism Editor actual import passed, and `import_ready.psd` may be used for the next Cubism rigging step."
                if report["checks"].get("cubism_import_smoke") == "PASS"
                else "This pack is not accepted as `import_ready.psd` until Cubism Editor actual import succeeds and the layers are not flattened."
            ),
            "",
            "Record manual smoke evidence in `reports/cubism_import_smoke.json` with:",
            "",
            "```json",
            json.dumps(
                {
                    "cubism_import_success": True,
                    "layers_flattened": False,
                    "reviewer": "name",
                    "notes": "Layer list visible in Cubism Editor.",
                },
                indent=2,
            ),
            "```",
            "",
        ]
    )
    (pack / "qa_report.md").write_text("\n".join(lines), encoding="utf-8")


def export_handoff_file(pack: Path) -> None:
    text = f"""# Cubism Rigger Handoff

Date: {date.today()}

## Goal

Import `import_ready_candidate.psd` into Live2D Cubism Editor and verify whether it can be promoted to `import_ready.psd`.

## Files

- `import_ready_candidate.psd`: Python-generated PSD candidate. Do not trust until Cubism import smoke passes.
- `production_layers/`: PNG fallback layers for manual PSD assembly in Photoshop, Clip Studio Paint, or Krita.
- `reference_pack/mouth/`: mouth key-pose references for `ParamMouthOpenY` and `ParamMouthForm`.
- `reference_pack/blink/`: blink key-pose references for `ParamEyeLOpen` and `ParamEyeROpen`.
- `layer_manifest.json`: layer roles, draw order, bbox, and `include_in_import_psd` flags.
- `param_map.json`: key-pose mapping.

## Cubism Checklist

1. Open `import_ready_candidate.psd` in Cubism Editor.
2. Confirm layers are visible as separate parts, not flattened.
3. Confirm only production layers are imported; mouth/blink references must stay outside the PSD.
4. Run automatic mesh generation for broad parts.
5. Manually mesh mouth, eyelashes, brows, and deform-heavy eye parts.
6. Create Deformer hierarchy for face, eyes, mouth, hair, and body.
7. Key `ParamEyeLOpen`, `ParamEyeROpen`, `ParamMouthOpenY`, and `ParamMouthForm` using `reference_pack/`.
8. Edit texture atlas.
9. Export `.moc3`, `.model3.json`, textures, and optional `.physics3.json` from Cubism Editor.

## Smoke Evidence

After testing in Cubism Editor, create `reports/cubism_import_smoke.json`:

```json
{{
  "cubism_import_success": true,
  "layers_flattened": false,
  "reviewer": "name",
  "notes": "Layer list visible in Cubism Editor."
}}
```

Then rerun:

```bash
python3 /Users/family/jason/Vtube/scripts/validate_cubism_psd_inputs.py --pack {pack}
```
"""
    (pack / "rigger_handoff.md").write_text(text, encoding="utf-8")


def export_handoff(args: argparse.Namespace) -> None:
    export_handoff_file(Path(args.pack))


def add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pack", default=str(DEFAULT_PACK), help="Cubism material pack output directory")


def main_build() -> None:
    parser = argparse.ArgumentParser(description="Build Cubism material pack")
    add_common_args(parser)
    parser.add_argument("--character-id", default="vtube_001", help="Character identifier for future pack variants")
    build_pack(parser.parse_args())


def main_validate() -> None:
    parser = argparse.ArgumentParser(description="Validate Cubism material pack")
    add_common_args(parser)
    parser.add_argument("--promote", action="store_true", help="Promote candidate PSD to import_ready.psd when Cubism smoke passes")
    validate_pack(parser.parse_args())


def main_handoff() -> None:
    parser = argparse.ArgumentParser(description="Export Cubism rigger handoff markdown")
    add_common_args(parser)
    export_handoff(parser.parse_args())
