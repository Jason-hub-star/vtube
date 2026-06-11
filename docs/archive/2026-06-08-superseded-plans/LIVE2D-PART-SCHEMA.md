# Live2D Part Schema

This document is the source reference for the local part-purity review app.
The current v1 target is a Cubism-import material pack: production layers go
into `import_ready.psd`, while mouth/blink key poses stay in `reference_pack/`.

## Related Pipeline

Use `docs/ref/LIVE2D-PART-PURITY-PIPELINE.md` for the active operating plan:

```text
part schema -> review_app visual check -> ai_fix_queue.json -> AI cleanup/regeneration -> PSD rebuild -> Cubism import smoke
```

The schema defines what each part is allowed to contain. The review app records
whether the current image actually satisfies that rule.

## Review Rules

- Production layers must contain only the named part and transparent pixels.
- Reference and guide images must never be included in the import PSD.
- Left/right production layers use `L_` and `R_` prefixes.
- Any human review verdict of `X`, `REVISE`, or `DISCARDED` forces the layer
  out of the next accepted import candidate until it is regenerated or cleaned.
- Contamination means visible pixels from another semantic part, even if the
  artifact is visually small.

## Issue Tags

| Tag | Meaning | AI negative prompt hint |
| --- | --- | --- |
| `hair_mixed` | Hair pixels appear in a non-hair part. | no hair strands, no bangs, no side hair |
| `skin_mixed` | Skin/face/neck pixels appear in another part. | no skin area, no face fill, no neck fill |
| `eye_white_mixed` | Eye white pixels appear outside the eye-white layer. | no sclera, no white eyeball region |
| `iris_mixed` | Iris/pupil pixels appear outside iris or pupil layers. | no iris, no pupil, no black eye disk |
| `line_cut` | Important line art is cropped or broken. | complete continuous line art, uncropped outline |
| `alpha_dirty` | Stray semi-transparent pixels remain outside the part. | clean alpha, transparent background, no residue |
| `bbox_too_tight` | Bounding box cuts into expected deformation margin. | include safe transparent margin around part |
| `missing_underpaint` | Deforming part lacks hidden underpaint. | include covered underpaint where required |
| `wrong_shape` | Shape does not match the canonical design. | match canonical silhouette and proportions |

## Production Parts

| Part ID | Korean name | Group | Include in PSD | Allowed features | Forbidden contamination |
| --- | --- | --- | --- | --- | --- |
| `face_underpaint` | 얼굴 언더페인트 | face | true | hidden skin fill behind face parts | hair, eyes, mouth, clothes |
| `back_hair` | 뒷머리 | hair | true | rear hair mass only | face, neck, front hair, side hair |
| `body` | 몸통 | body | true | body skin and torso base | clothes, hair, face |
| `clothes` | 의상 | body | true | clothing pixels only | skin, hair, face |
| `L_arm` | 왼쪽 팔 | body | true | left arm, sleeve, or visible arm-side silhouette only | face, hair, right arm, background |
| `R_arm` | 오른쪽 팔 | body | true | right arm, sleeve, or visible arm-side silhouette only | face, hair, left arm, background |
| `neck` | 목 | face | true | neck skin only | clothes, hair, face outline |
| `face_base` | 얼굴 베이스 | face | true | visible face skin and face outline | hair, eyes, mouth |
| `L_eye_white` | 왼쪽 흰자 | eyes | true | left sclera only | iris, pupil, lash, hair, skin |
| `R_eye_white` | 오른쪽 흰자 | eyes | true | right sclera only | iris, pupil, lash, hair, skin |
| `L_iris` | 왼쪽 홍채 | eyes | true | left iris color only | pupil, highlight, eye white, lash |
| `R_iris` | 오른쪽 홍채 | eyes | true | right iris color only | pupil, highlight, eye white, lash |
| `L_pupil` | 왼쪽 동공 | eyes | true | left pupil only | iris, highlight, eye white |
| `R_pupil` | 오른쪽 동공 | eyes | true | right pupil only | iris, highlight, eye white |
| `L_highlight` | 왼쪽 눈 하이라이트 | eyes | true | left eye catchlight only | iris, pupil, eye white |
| `R_highlight` | 오른쪽 눈 하이라이트 | eyes | true | right eye catchlight only | iris, pupil, eye white |
| `L_upper_lash` | 왼쪽 윗속눈썹 | eyes | true | upper lash line only | hair, skin, eye white, iris |
| `R_upper_lash` | 오른쪽 윗속눈썹 | eyes | true | upper lash line only | hair, skin, eye white, iris |
| `L_lower_lash` | 왼쪽 아랫속눈썹 | eyes | true | lower lash line only | hair, skin, eye white, iris |
| `R_lower_lash` | 오른쪽 아랫속눈썹 | eyes | true | lower lash line only | hair, skin, eye white, iris |
| `L_brow` | 왼쪽 눈썹 | brows | true | left brow only | hair, skin, lash |
| `R_brow` | 오른쪽 눈썹 | brows | true | right brow only | hair, skin, lash |
| `mouth_line` | 입 라인 | mouth | true | mouth outline and lip line only | teeth, tongue, skin |
| `mouth_inner` | 입 안쪽 | mouth | true | dark mouth cavity only | teeth, tongue, skin, cropped line |
| `teeth` | 치아 | mouth | true | teeth only | tongue, mouth line, skin |
| `tongue` | 혀 | mouth | true | tongue only | teeth, mouth line, skin |
| `L_side_hair` | 왼쪽 옆머리 | hair | true | left side hair lock only | face, eye, brow, back hair |
| `R_side_hair` | 오른쪽 옆머리 | hair | true | right side hair lock only | face, eye, brow, back hair |
| `front_hair` | 앞머리 | hair | true | front bangs only | face, eye, brow, side/back hair |

## Future Fine Split Candidates

These are not all required for v1, but they are useful once the pipeline moves
from bootstrap extraction to generation by part:

- face: cheek blush, nose shadow, ear left/right, face line, skin shadow
- hair: back lower hair, back upper hair, front bang clusters, ahoge, side locks,
  hair highlights, hair shadows
- eyes: upper eyelid fold, lower eyelid fold, eyelid skin cover, eye shadow
- mouth: upper lip line, lower lip line, mouth corner left/right, upper teeth,
  lower teeth, inner shadow
- clothes: collar, sleeve left/right, ribbon, accessory, cloth shadow

## Reference Parts

Mouth and blink references are key-pose guides for Cubism parameters. They are
not frame-swap production layers and must stay outside `import_ready.psd`.

- Mouth references map to `ParamMouthOpenY` and `ParamMouthForm`.
- Blink references map to `ParamEyeLOpen` and `ParamEyeROpen`.
- Overlay images are comparison evidence only.
