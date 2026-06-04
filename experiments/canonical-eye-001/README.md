# CANON-EYE-001 Canonical Eye Geometry Extraction

작성일: 2026-06-02

## 목적

실패한 full eye sheet grouping 대신, canonical 원본 눈에서 iris center, eye ROI, eye shape mask를 추출할 수 있는지 확인한다.

## 실행

```bash
python3 /Users/family/jason/Vtube/experiments/canonical-eye-001/scripts/canonical_eye_geometry.py
```

## 결과

```text
iris_center_delta: PASS
eye_roi_bbox: PASS
shape_mask_saved: PASS
decision: keep
```

## Evidence

```text
masks/left_eye_roi.png
masks/right_eye_roi.png
overlays/canonical_eye_geometry_overlay.png
reports/canonical_eye_geometry_report.json
reports/qa_report.md
```

## 결론

canonical eye geometry는 향후 눈/깜빡임 작업의 기준으로 유지한다. generated eye sheet의 full-eye 조립은 계속 폐기 상태다.
