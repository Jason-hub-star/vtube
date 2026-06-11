# Cubism v2 Review Gate Spec

Updated: 2026-06-06

## Decision

Do not throw away the unified review app. Reuse it with a Cubism v2-specific
manifest and verdict schema.

Discard or archive only old standalone per-experiment `preview/index.html`
surfaces when they compete with `review_app`.

## Review Surface

Keep:

```text
/Users/family/jason/Vtube/review_app/index.html
/Users/family/jason/Vtube/review_app/src/app.js
/Users/family/jason/Vtube/scripts/review_app_server.py
```

Extend or generate new manifests:

```text
/Users/family/jason/Vtube/review_app/review_manifest.json
```

Recommended future manifest mode:

```text
mode: cubism_v2
tier: v2_min | v2_standard | v2_rich
review_gate: concept | part_taxonomy | structure | motion_visual
```

## Gates

### G0 Concept

Purpose:

```text
Choose a single-source matched character before part generation.
```

Review checks:

```text
style consistency
front or near-front pose
clear eye/mouth/hair silhouette
neck and shoulders visible
arms not blocking face or hair
no text or heavy transparent effects
```

Verdicts:

```text
concept_accept
concept_revise
concept_reject
```

### G1 Part Taxonomy

Purpose:

```text
Confirm the layer set matches the Cubism tier before PSD/Cubism import.
```

v2_min required part floor:

```text
20-25 parts
eye L/R internal parts
mouth internal parts
front/side/back hair
face/neck/body/shoulder-arm basics
```

Review checks:

```text
part exists
full-canvas alignment
alpha cleanliness
no accidental crop
no style mismatch
underpaint sufficient for expected motion
```

Verdicts:

```text
part_keep
part_revise
part_reject
```

### G2 Cubism Structure

Purpose:

```text
Prove real Cubism structure exists.
```

Source:

```text
CMO3 structure reports
compare_cmo3_structure_reports.py
```

This is not a visual-only gate.

Minimum pass:

```text
ArtMesh >= 20
Parameter >= 15
Warp Deformer >= 8
Rotation Deformer >= 1
KeyformBinding >= 20
```

Verdicts:

```text
structure_pass
structure_fail
```

### G3 Motion Visual

Purpose:

```text
Check whether Cubism parameter extremes look acceptable.
```

Required evidence:

```text
eye open/half/closed
mouth closed/half/open/form extremes
hair swing left/neutral/right
head/body angle extremes
draw order and overhang note
```

Verdicts:

```text
motion_keep
motion_revise
motion_reject
```

## Tier Review Load

```text
v2_min:
  concept candidates: 3-6
  parts: 20-25
  motion: eye/mouth/hair/body extremes only

v2_standard:
  parts: 50-70
  motion: key extremes plus physics settle frames
  requires visual pass before v2_rich

v2_rich:
  parts: 90+
  review masks, expressions, arm/clothing toggles, and richer effects
  allowed only after v2_standard passes
```

## Non-Negotiables

```text
human visual FAIL is never production success
numeric/structure PASS is not visual PASS
Mini Cubism local preview is not Cubism CMO3/MOC3 proof
official sample art/texture/PSD is never reused
```
