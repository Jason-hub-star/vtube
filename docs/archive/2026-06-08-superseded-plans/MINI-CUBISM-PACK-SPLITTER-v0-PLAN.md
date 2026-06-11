# Mini Cubism Pack Splitter v0 Plan

Updated: 2026-06-05

## Summary

Mini Cubism pack-splitter-v0의 목표는 완성 캐릭터 한 장에서 70개 이상 파츠를 억지로 뽑는 방식을 중단하고, `clean base mannequin + pack` 단위로 분해/QA/rig 연결을 검증하는 것이다.

현재 `See-through 70+ custom split v2`는 structural PASS지만 visual FAIL이다. 이 결과를 실패로 덮지 않고, 새 파이프라인의 negative gate로 유지한다.

기본 실험 폴더:

```text
experiments/mini-cubism-pack-splitter-v0-001/
```

## Current Constraints

- 기존 dedicated 640 See-through는 `*_layers.json`을 만들었지만 clean inference report가 없고 7개 empty normalized layer가 있다.
- `seethrough_70_custom_split_v2`는 73 parts, 18 hair, 16 eye, 8 mouth, 33 physics targets를 만들었지만 critical face/eye/mouth generated/fallback 후보 23개 때문에 `REVISE_VISUAL`이다.
- Face v1은 technical PASS였지만 주인님 visual review FAIL이다. 계속 negative fixture로 유지한다.
- Glue, CMO3/MOC3 writer, Cubism production compatibility는 pack-splitter-v0 범위 밖이다.

## Architecture

Pack-splitter-v0는 아래 네 pack을 별도 입력/출력/QA 단위로 다룬다.

```text
base_mannequin
  - bald head
  - face_base, ears, neck, torso, arms
  - neutral two-piece swimsuit/rig underlayer
  - chest and pelvis are covered; abdomen remains visible skin

hair_pack
  - front bangs, side locks, back hair, tips
  - physics-first targets

outfit_pack
  - collar, chest cloth, sleeves, shoulders, frills, ribbon
  - garment/cloth physics targets

accessory_pack
  - choker, gem, earrings, headwear, small attach points
```

Eyes and mouth are not treated as normal decomposition targets. They are `keypose_asset_pack` candidates because closed/half/open states often do not exist in the source image.

## Model Probe Roles

| Candidate | Role | Use In v0 | Gate |
|---|---|---|---|
| LayerD / `cyberagent/layerd-birefnet` | Iterative layer decomposition and raw RGBA layer extraction | Primary probe for base/hair/outfit/accessory packs | Must produce non-empty layers and improve over See-through contact sheet |
| BiRefNet / BiRefNet_HR / BiRefNet-matting | High-quality alpha/matting cleanup | Edge cleanup for body, hair, clothing masks | Must reduce jagged/contaminated boundaries |
| SAM2.1 | ROI box/point prompt mask refinement | Eye, mouth, bang, ribbon, choker ROI refinement | Must stay inside pack ROI and avoid unrelated regions |
| Fashion SegFormer | Clothing semantic segmentation | Outfit pack category hints | Use as reference mask only unless visually clean |
| AnimeInstanceSegmentation | Anime/cartoon character mask | Character foreground and instance sanity check | Reference only until it beats existing coarse masks |
| BRIA RMBG-2.0 | Strong background removal | Deferred | Gated/license-other; not default production dependency |

References:

- LayerD official repo: https://github.com/CyberAgentAILab/LayerD
- LayerD BiRefNet model: https://huggingface.co/cyberagent/layerd-birefnet
- BiRefNet: https://huggingface.co/ZhengPeng7/BiRefNet
- BiRefNet_HR: https://huggingface.co/ZhengPeng7/BiRefNet_HR
- BiRefNet-matting: https://huggingface.co/ZhengPeng7/BiRefNet-matting
- SAM2.1 large: https://huggingface.co/facebook/sam2.1-hiera-large
- Hugging Face mask generation docs: https://huggingface.co/docs/transformers/en/tasks/mask_generation
- Fashion SegFormer: https://huggingface.co/Itbanque/fashion_segformer
- AnimeInstanceSegmentation: https://huggingface.co/dreMaz/AnimeInstanceSegmentation

## Required Outputs

```text
experiments/mini-cubism-pack-splitter-v0-001/
  README.md
  pack_splitter_manifest.json
  base_mannequin/
    canonical_base.png
    candidate_manifest.json
  hair_pack/
    candidate_manifest.json
  outfit_pack/
    candidate_manifest.json
  accessory_pack/
    candidate_manifest.json
  hf_probe/
    layerd/
    birefnet/
    sam2/
    fashion_segformer/
    anime_instance/
  reports/
    hf_probe_report.json
    pack_splitter_qa_report.json
    model_comparison_contact_sheet.png
    pack_problem_contact_sheet.png
    review_summary.md
  mini_cubism_project_pack_v0/
```

`mini_cubism_project_pack_v0/` is created only after pack QA PASS. Before PASS, project promotion must fail closed.

## Implementation Phases

1. **Experiment bootstrap**
   - Create `pack_splitter_manifest.json` with pack definitions, source canonical paths, candidate model list, and QA thresholds.
   - Preserve all existing dedicated v1 and See-through v2 evidence.
   - Mark status as `PLANNED_PENDING_PROBE`.

2. **Clean base mannequin**
   - Generate or select a neutral two-piece swimsuit/rig underlayer base with no hair and no outfit decoration.
   - The underlayer covers only the chest and pelvis. The abdomen must remain visible skin so crop tops, open jackets, and belly-visible outfits can be tested later.
   - Required visual constraints: front-facing, full torso, no cropped head/arms, no text/watermark, visible ears/neck/arms.
   - This is rig-safe base evidence, not final character art.

3. **HF probe**
   - Run LayerD low-level decomposition first because it can return raw RGBA layers.
   - Run BiRefNet variants for foreground/matting cleanup.
   - Run SAM2.1 with pack ROI boxes rather than full automatic masks.
   - Run Fashion SegFormer only on outfit pack candidates.
   - Run AnimeInstanceSegmentation as a reference foreground sanity check.

4. **Candidate fusion**
   - For each target part, keep multiple candidate masks with provenance.
   - Never overwrite the source candidate; select by score into `selected_candidate_id`.
   - Store rejected candidates as reference evidence.

5. **QA gate**
   - Structural gates: full-canvas 2048 PNG, non-empty alpha, unique part IDs, pack totals.
   - Visual gates: ROI containment, alpha coverage range, symmetry, edge cleanliness, style contamination, generated/procedural flags.
   - Critical gates: face/eye/mouth generated/fallback candidates cannot pass production QA.
   - Contact sheets are required before 주인님 review.

6. **Mini Cubism connection**
   - Build local project only from QA PASS packs.
   - Hair/outfit/accessory parts get physics profiles first.
   - Eye/mouth keypose packs remain separate until style-matched assets exist.

## Acceptance Criteria

- `hf_probe_report.json` compares LayerD, BiRefNet, SAM2, Fashion SegFormer, and AnimeInstance candidates on the same source.
- At least one contact sheet shows model-by-model masks for base/hair/outfit/accessory packs.
- QA distinguishes `STRUCTURAL_PASS_VISUAL_FAIL` from true PASS.
- `pack_splitter_qa_report.json` blocks project promotion if critical visual gates fail.
- 주인님 review is limited to `model_comparison_contact_sheet.png`, `pack_problem_contact_sheet.png`, and `review_summary.md`.
- The plan does not claim Cubism `.cmo3/.moc3` compatibility.

## First Implementation Commands

```bash
cd /Users/family/jason/Vtube
python3 scripts/bootstrap_mini_cubism_pack_splitter_v0.py \
  --experiment experiments/mini-cubism-pack-splitter-v0-001
python3 scripts/run_mini_cubism_hf_pack_probe.py \
  --experiment experiments/mini-cubism-pack-splitter-v0-001
python3 scripts/validate_mini_cubism_pack_splitter_v0.py \
  --experiment experiments/mini-cubism-pack-splitter-v0-001
```

These scripts do not exist yet. They are the next implementation target.

## Decision

Proceed with pack-splitter-v0 as the next Mini Cubism layer strategy. Do not spend the next loop trying to make single-image See-through 70+ pass by adding more generated/fallback parts.
