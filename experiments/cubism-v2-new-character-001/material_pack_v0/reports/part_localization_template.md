# Cubism v2 Part Localization Template

- status: `PASS_PART_LOCALIZATION_TEMPLATE_READY`
- overrides: `37`
- anchor outside ROI: `10`
- json: `experiments/cubism-v2-new-character-001/material_pack_v0/reports/part_localization_template.json`

## Reference BBoxes

| Basis | BBox |
|---|---|
| `canvas` | `[0, 0, 2048, 2048]` |
| `eye_L` | `[808, 657, 217, 242]` |
| `eye_R` | `[1060, 660, 204, 239]` |
| `mouth` | `[953, 825, 148, 246]` |
| `brow` | `[827, 606, 410, 88]` |
| `face` | `[796, 685, 470, 389]` |
| `body` | `[626, 1036, 799, 680]` |
| `head` | `[766, 576, 530, 528]` |

## Policy

- ROI absolute coordinates are used for current-candidate remasking.
- ROI relative coordinates are the reusable template for future similarly framed characters.
- Saved anchors are preserved, but ROI center is safer for extraction because many saved anchors are outside the ROI.
