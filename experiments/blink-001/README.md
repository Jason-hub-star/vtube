# BLINK-001 Canonical-ROI Closed Lid Smoke

작성일: 2026-06-02

## 목적

full eye replacement 없이, sheet에서 나온 closed-lid 후보만 canonical eye ROI 안에 배치할 수 있는지 확인한다.

## 실행

```bash
python3 /Users/family/jason/Vtube/experiments/blink-001/scripts/blink_closed_lid_smoke.py
```

## 결과

```text
closed_lid_inside_roi: PASS
no_full_eye_replacement: PASS
visual_alignment: FAIL
decision: discard
```

## Evidence

```text
layers/closed_lid_full.png
overlays/closed_lid_overlay.png
reports/blink_report.json
reports/qa_report.md
```

## 결론

sheet closed-lid 후보는 canonical 눈 모양을 따르지 못해 폐기한다. blink는 canonical edit/inpaint 또는 수동 layer split 경로로 재설계한다.
