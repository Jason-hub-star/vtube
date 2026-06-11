# Cubism v2 쉬운 검수 패킷

- tier: `v2_min`
- generated_at: `2026-06-05T16:10:20.335427+00:00`
- 사람이 먼저 볼 것: gate별 contact sheet와 실패 후보 목록

## Contact Sheets
- G1 파츠 확인: `experiments/cubism-v2-validator-fixtures-001/review_packet/g1_part_taxonomy_contact_sheet.png`
- G2 구조 자동검사: `experiments/cubism-v2-validator-fixtures-001/review_packet/g2_structure_contact_sheet.png`

## Auto Checks
- fixture__positive_cmo3_structure: `PASS` - fixture structure gate expectation
- fixture__shallow_cmo3_structure: `REVISE` - fixture structure gate expectation

## Failure Candidates
- fixture__shallow_cmo3_structure: 얕은 rig 구조 / `REVISE` / bad_alpha, clipping_risk, missing_part
