# Cubism v2 쉬운 검수 패킷

- tier: `v2_min`
- generated_at: `2026-06-05T16:05:29.681579+00:00`
- 사람이 먼저 볼 것: gate별 contact sheet와 실패 후보 목록

## Contact Sheets
- G0 캐릭터 고르기: `experiments/cubism-v2-review-001/review_packet/g0_concept_contact_sheet.png`
- G1 파츠 확인: `experiments/cubism-v2-review-001/review_packet/g1_part_taxonomy_contact_sheet.png`
- G2 구조 자동검사: `experiments/cubism-v2-review-001/review_packet/g2_structure_contact_sheet.png`
- G3 움직임 확인: `experiments/cubism-v2-review-001/review_packet/g3_motion_visual_contact_sheet.png`

## Auto Checks
- g2__cubism_structure_auto_check: `REVISE` - 그림 문제가 아니라 Cubism에서 deformer/keyform/physics 보강이 필요합니다.

## Failure Candidates
- g2__cubism_structure_auto_check: 구조 자동검사 / `REVISE` / bad_alpha, clipping_risk, missing_part
