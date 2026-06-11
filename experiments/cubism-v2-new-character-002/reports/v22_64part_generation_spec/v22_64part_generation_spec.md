# Character 002 v22 64-Part Generation Spec

- status: `PASS_SPEC_READY_FOR_IMAGE_GENERATION_PLANNING`
- generated_at: `2026-06-09T09:36:22.238312+00:00`
- target: `v2_standard` / `64` parts
- default canvas: `2048x2048 RGBA full-canvas after normalization`
- production target: Live2D/Cubism PSD, real deformers/keyforms, CMO3/runtime validation
- not target: PNG frame-swap production

## Locked v21 Success Baseline

- current: `v21 supported-control Mini Cubism rig smoke`
- active controls: `ParamAngleX, ParamEyeBallX, ParamEyeBallY, ParamEyeLOpen, ParamEyeROpen, ParamMouthOpenY`
- hidden unsupported controls: `ParamHairFront`
- eye policy: natural close around 0.27; do not expose harder close as default visual target until new assets approve it
- mouth policy: clamp wide open around 0.85 until regenerated smile-open packet passes visual QA
- diagnostic scope: Mini Cubism PASS is local diagnostic evidence only, not real Cubism authoring success

## 64-Part Counts

- `body`: `10`
- `face_base`: `8`
- `eye_L`: `8`
- `eye_R`: `8`
- `brow`: `2`
- `mouth`: `8`
- `hair`: `16`
- `clothing`: `4`

## Generation Batches

### B0_source_identity

Lock one same-character source before any split asset is accepted.

Outputs:
- `new_character_002_source_front`
- `source_palette_reference`
- `source_identity_notes`

Rules:
- adult cute female character identity remains fixed across all following assets
- front or near-front upper-body pose with visible neck, shoulders, torso, eyes, mouth, and readable hair groups
- no labels, guides, text, props covering eyes/mouth/hair, or accessory changes between sheets

### B1_clean_base_underpaint

Create clean bases at generation time instead of patching baked pixels later.

Outputs:
- `face_base`
- `face_underpaint_L`
- `face_underpaint_R`
- `eye_L_underpaint`
- `eye_R_underpaint`
- `mouth_base_clean_reference`
- `body_underpaint`
- `neck_shadow_underpaint`
- `arm_L_underpaint`
- `arm_R_underpaint`
- `hair_back_underpaint`

Rules:
- face_base has no open-eye, iris, pupil, eye-white, lash, mouth-line, teeth, or tongue remnants
- underpaint preserves skin/hair gradients and occlusion, with no rectangular patch boundary
- do not promote procedural cover patches or late mask surgery as production clean base

### B2_eye_pack

Generate production eye parts and blink in-betweens as one coordinated eye packet.

Outputs:
- `eye_L_white`
- `eye_L_iris`
- `eye_L_pupil`
- `eye_L_highlight`
- `eye_L_upper_lash`
- `eye_L_lower_lash`
- `eye_L_closed_lid`
- `eye_R_white`
- `eye_R_iris`
- `eye_R_pupil`
- `eye_R_highlight`
- `eye_R_upper_lash`
- `eye_R_lower_lash`
- `eye_R_closed_lid`
- `eye_open_reference`
- `eye_half_closed_reference`
- `eye_mostly_closed_reference`
- `eye_closed_reference`

Rules:
- eye whites stay fixed for EyeBallX/Y; iris, pupil, and highlight move together from the same anchor
- split iris/pupil/highlight may pass only if they are generated as a coherent packet and anchor-locked
- if split details drift or create crossed eyes, fall back to a coherent iris-detail diagnostic asset and regenerate the production split
- EyeOpen visual clamp target starts from v21 pattern: natural close is around 0.27, not hard 0.0

### B3_mouth_pack

Generate mouth rig parts as a coordinated smile-open material packet.

Outputs:
- `mouth_line`
- `mouth_inner`
- `mouth_upper_lip_mask`
- `mouth_lower_lip_mask`
- `mouth_teeth`
- `mouth_tongue`
- `mouth_corner_L`
- `mouth_corner_R`
- `mouth_closed_smile_reference`
- `mouth_small_open_reference`
- `mouth_mid_teeth_reference`
- `mouth_wide_teeth_tongue_reference`

Rules:
- teeth/tongue/inner must be drawn naturally inside the same mouth opening, not pasted as separate centered overlays
- wide-open reference must be proportion-limited; reject oversized round mouth shapes
- ParamMouthOpenY max remains visually clamped around 0.85 until a better mouth packet is approved
- ParamMouthForm is not active in v21 diagnostic unless a real production mouth-form set is generated

### B4_hair_pack

Create independent front/back/side hair children so HairFront can become real.

Outputs:
- `hair_back_base`
- `hair_back_strand_L`
- `hair_back_strand_R`
- `hair_back_center`
- `hair_front_center`
- `hair_front_L`
- `hair_front_R`
- `hair_front_side_L`
- `hair_front_side_R`
- `hair_front_tip_L`
- `hair_front_tip_R`
- `hair_side_L_outer`
- `hair_side_L_inner`
- `hair_side_R_outer`
- `hair_side_R_inner`

Rules:
- ParamHairFront stays unsupported until real hair_front_* child parts exist and move independently
- front bangs must preserve face/eye occlusion consistency across clean base and eye packets
- side/back hair parts must leave underpaint coverage for angle and physics motion

### B5_body_clothing_pack

Complete torso, neck, shoulder, arm, and clothing layers for standard body motion.

Outputs:
- `torso_base`
- `neck`
- `shoulder_L`
- `shoulder_R`
- `arm_L_upper_simple`
- `arm_R_upper_simple`
- `collar_front`
- `collar_shadow`
- `chest_cloth_base`
- `chest_cloth_shadow`
- `brow_L`
- `brow_R`
- `nose`
- `cheek_L`
- `cheek_R`
- `face_shadow_L`
- `face_shadow_R`

Rules:
- keep first v2_standard scope simple: no complex hands, large props, heavy effects, or rich vowel set
- nose must remain visible as its own subtle part; do not lose it during face cleanup
- body and clothing parts must support breath and body-angle motion without visible holes

### B6_manifest_normalize_validate

Normalize and validate only after raw evidence is preserved.

Outputs:
- `raw_outputs/`
- `normalized_layers/`
- `generation_manifest.json`
- `layer_manifest.json`
- `technical_validation_report.json`
- `contact_sheet.png`
- `overlay_qa_report.md`
- `manual_anchor_overrides.json`

Rules:
- keep raw generated files; never delete rejected evidence
- normalize to full-canvas RGBA, default 2048x2048 unless the Cubism authoring plan explicitly chooses another allowed size
- all crop outputs need full-canvas placement plus ROI/anchor metadata

## Quality Gates

### G0_source_identity -> `PASS_READY_FOR_64PART_GENERATION`

- same character accepted by 주인님
- style/outfit accepted enough for production split
- hair, eyes, mouth, neck, shoulders, torso are readable

### G1_64part_completeness -> `PASS_64_PARTS_PRESENT`

- 64 required part IDs present in manifest
- group counts match v2_standard spec
- no duplicate IDs or missing underpaint placeholders

### G2_full_canvas_rgba -> `PASS_NORMALIZED_FULL_CANVAS`

- each PNG is RGBA
- each layer has shared full-canvas dimensions
- non-empty alpha and bbox metadata exist

### G3_technical_validators -> `PASS_READY_FOR_VISUAL_QA`

- validate_cubism_v2_keypose_pngs.py passes for required keypose PNGs
- 64-part manifest validator passes
- PSD input validator passes before import attempt

### G4_contact_sheet_visual_qa -> `PASS_HUMAN_VISUAL_QA_REQUIRED_OR_ACCEPTED`

- contact sheet shows no patch borders, baked residues, or identity drift
- eye size/location and mouth location are coherent
- mouth teeth/tongue/inner read naturally

### G5_overlay_qa -> `PASS_OVERLAY_QA_OR_REVISE`

- clean bases do not contain eye/mouth remnants
- closed-eye states do not reveal original open-eye pixels
- mouth open states do not reveal circular patch boundaries

### G6_manual_anchor_correction -> `PASS_ANCHOR_LOCKED_OR_REVISE`

- use drag/zoom editor when eye, mouth, or hair parts are visually misaligned
- save explicit override JSON with target anchors and applied deltas
- rebuild full-canvas layers from overrides, then rerun contact sheet

### G7_mini_cubism_diagnostic -> `PASS_DIAGNOSTIC_ONLY`

- Mini Cubism supported controls pass validator and pose sweep
- unsupported controls are hidden or marked contract-only
- diagnostic PASS is not promoted to real Cubism authoring success

### G8_real_cubism_authoring_readiness -> `READY_FOR_CUBISM_EDITOR_AUTHORING`

- PSD candidate uses psd-tools path and passes input validation
- actual Cubism Editor import smoke is captured
- CMO3 structure gate targets warp >=35, rotation >=8, keyform bindings >=120, physics groups >=4

## Success Patterns

- `same_character_material_pack_first`: source, clean bases, eyes, mouth, hair, and body are generated as one coordinated identity set / distinguishes from: not a pretty front image followed by late erasing/patching
- `clean_base_generated_not_patched`: face_base and underpaints have natural gradients and no baked eye/mouth pixels / distinguishes from: no rectangular skin patches or socket cover stains
- `eye_detail_anchor_locked`: eye whites are fixed; iris, pupil, and highlight share the same EyeBall delta and target anchor / distinguishes from: not partial original eye movement, moving whites, or split detail drift
- `mouth_generated_as_packet`: inner, teeth, tongue, lips, line, and corners belong to the same opening and scale / distinguishes from: not tiny centered mouth swaps or pasted helper overlays
- `real_hairfront_children`: hair_front_* parts exist and can move independently before ParamHairFront is shown / distinguishes from: not a fake slider with no moving front hair art
- `evidence_separation`: technical PASS, human visual PASS, Mini Cubism PASS, and Cubism structure PASS are recorded separately / distinguishes from: not treating validator or Mini Cubism preview as final production rig success

## Failure Patterns

- `late_patch_clean_base` -> `FAIL_VISUAL_QA`
  - signals: rectangular skin boundary, stain around sockets, open-eye or mouth remnants in face_base
  - recovery: regenerate or model-native repaint clean base; do not widen cover patches
- `moving_eye_white` -> `FAIL_RIG_POLICY`
  - signals: eye white follows EyeBallX/Y, whole baked eye slides inside face
  - recovery: keep white fixed; move only anchor-locked iris/pupil/highlight detail
- `split_eye_detail_drift` -> `REVISE_OR_REGENERATE`
  - signals: pupil/highlight detach from iris, cross-eyed gaze, only a small part of original eye moves
  - recovery: use manual anchor correction and regenerate production split as a coherent eye packet
- `oversized_or_centered_mouth` -> `REVISE_OR_REGENERATE`
  - signals: wide open mouth too large, round patch boundary, tiny mouth opens at center only
  - recovery: regenerate smile-open mouth packet with bounded max open and visible teeth/tongue
- `pasted_mouth_internals` -> `FAIL_VISUAL_QA`
  - signals: teeth/tongue/inner look like overlays, internals do not follow mouth shape
  - recovery: generate internals inside coordinated mouth opening, then split cleanly
- `fake_hairfront_slider` -> `UNSUPPORTED_CONTROL_HIDE`
  - signals: ParamHairFront exists but no independent front hair child parts move
  - recovery: hide in diagnostic preview until hair_front_* parts exist
- `validator_only_promotion` -> `BLOCKED_FROM_PRODUCTION`
  - signals: PNG validator passes but contact sheet or human review says REVISE/FAIL
  - recovery: keep technical PASS separate and return to visual/overlay QA
- `mini_cubism_as_real_cubism` -> `BLOCKED_FROM_PRODUCTION_CLAIM`
  - signals: Mini Cubism pose sweep PASS used as final rig proof
  - recovery: author real Cubism deformers/keyforms, then run CMO3 structure inspection

## Required Outputs

- `raw_outputs/`
- `normalized_layers/`
- `generation_manifest.json`
- `layer_manifest.json`
- `technical_validation_report.json`
- `64part_completeness_report.json`
- `contact_sheet.png`
- `overlay_qa_report.md`
- `human_visual_review.md`
- `manual_anchor_overrides.json when used`
- `mini_cubism_diagnostic_project/ after visual QA only`
- `import_ready_candidate.psd after material QA`
- `cubism_import_smoke.json after actual Cubism Editor import`
- `cmo3_structure_report.json after real Cubism authoring`

## Source References

- `project_status`: `docs/status/PROJECT-STATUS.md`
- `material_pack_first_plan`: `docs/ref/CUBISM-V2-MATERIAL-PACK-FIRST-GENERATION.md`
- `confirmed_64part_spec`: `experiments/reference-model-structure-001/reports/cubism_v2_new_model_v2_standard_part_spec.json`
- `v21_success_replay`: `experiments/cubism-v2-new-character-002/reports/model_edit_v21_supported_rig_smoke_preview/success_pattern_replay_v1/success_pattern_replay_report.md`
- `v21_clean_contact_sheet`: `experiments/cubism-v2-new-character-002/reports/model_edit_v21_supported_rig_smoke_preview/supported_pose_sweep_clean_replay_v2/v21_supported_pose_sweep_clean_contact_sheet.png`
- `manual_eye_anchor_overrides`: `experiments/cubism-v2-new-character-002/reports/model_edit_v19_generated_eye_preview/manual_eye_detail_anchor_v1/manual_eye_detail_anchor_overrides.json`

## Self Review

- `part_count`: `64`
- `group_counts`: `{'body': 10, 'face_base': 8, 'eye_L': 8, 'eye_R': 8, 'brow': 2, 'mouth': 8, 'hair': 16, 'clothing': 4}`
- `no_duplicate_part_ids`: `True`
- `has_real_hairfront_scope`: `True`
- `has_eye_detail_split_scope`: `True`
- `has_mouth_internal_scope`: `True`
- `status`: `PASS`
