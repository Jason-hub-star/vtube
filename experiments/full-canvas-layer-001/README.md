# FCANVAS-001 Full-Canvas Mouth Layer Smoke

작성일: 2026-06-02

## 목적

mouth crop 후보를 canonical과 같은 `1536x1024` 투명 캔버스 레이어로 변환해, previewer가 crop/scale/place 없이 그대로 overlay할 수 있는지 확인한다.

## 실행

```bash
python3 /Users/family/jason/Vtube/experiments/full-canvas-layer-001/scripts/full_canvas_mouth_layer_smoke.py
```

## 결과

```text
full_canvas_layer: PASS
no_runtime_place_needed: PASS
visual_quality: REVISE
decision: keep
```

## Evidence

```text
layers/mouth_open_full.png
overlays/mouth_open_full_overlay.png
reports/full_canvas_layer_report.json
reports/qa_report.md
```

## 결론

full-canvas mouth layer 방식은 previewer 입력 구조로 유지한다. 단, 미술 품질은 mouth style scoring과 human review를 통과해야 한다.
