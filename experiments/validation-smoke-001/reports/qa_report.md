# validation-smoke-001 QA Report

## Result

- mouth crop/mask: PASS
- eye crop/mask: PASS
- canonical composite smoke: PASS
- decision: keep-testing

## Counts

- mouth crops: 14 total, 14 accepted
- eye crops: 18 total, 18 accepted
- composites: 5

## Evidence

- JSON: `/Users/family/jason/Vtube/experiments/validation-smoke-001/reports/crop_mask_composite_report.json`
- crops: `/Users/family/jason/Vtube/experiments/validation-smoke-001/crops`
- composites: `/Users/family/jason/Vtube/experiments/validation-smoke-001/composites`

## Notes

- This is a crop/mask and placement smoke test, not final character-quality validation.
- Mouth candidates are usable for further alignment tests. `mouth_composite_01.png` proves alpha crop and canonical placement are technically possible, but scale/position and expression style still need manual or automatic tuning.
- Eye candidates need stricter semantic classification before production use. `eye_pair_composite_01.png` proves crop/mask and overlay are technically possible, but the selected components do not yet replace the canonical eye cleanly.
- Next useful test: classify eye sheet components into `eye_white`, `iris`, `pupil`, `lash`, and `closed_lid`, then composite only matching subparts instead of whole components.
