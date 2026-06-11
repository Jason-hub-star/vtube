# Part Localization Template Validation

- status: `REVISE_LOCALIZATION_SPLIT_NEEDS_SEMANTIC_MASKING`
- manual overrides: `37`
- template parts: `37`
- localized split: `PASS_LOCALIZATION_TEMPLATE_SPLIT_APPLIED`
- G1.5 semantic check: `REVISE_G1_5_SEMANTIC_PURITY_GATE`
- neutral after bad ratio: `0.088469`
- eye/mouth after status: `PASS`
- Mini Cubism localized project: `PASS`

## Interpretation

- 위치 라벨은 분리 위치를 잡는 데 효과가 있다.
- 하지만 단순 ROI crop만으로는 밑색/숨은 영역/큰 파츠 품질이 부족하다.
- 다음 단계는 localization template를 seed로 쓰고, semantic owner map + underpaint repair를 다시 적용하는 것이다.

## Artifacts

- `experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_split_contact_sheet.png`
- `experiments/cubism-v2-new-character-001/material_pack_v0/reports/semantic_purity_localization_split/semantic_purity_gate_report.json`
- `experiments/cubism-v2-new-character-001/material_pack_v0/mini_cubism_project_material_localized_v1/reports/validation_report.json`
