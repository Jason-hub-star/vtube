# Asset Generation 2048

Date: 2026-06-02

## Goal

Generate the minimum new assets needed for the next Vtube validation tests without mass-producing unvalidated parts.

## Generated Assets

| Asset | Path | Native size | Intended test |
|---|---|---:|---|
| mouth set A, style match | `raw/mouth_set_a_stylematch_source.png` | 1983x793 | `MOUTH-APPLY-DELTA-001` |
| mouth set B, simplified | `raw/mouth_set_b_simple_source.png` | 1983x793 | `MOUTH-APPLY-DELTA-001` |
| blink staged eyelid sheet | `raw/blink_stage_sheet_source.png` | 2103x748 | `BLINK-STAGE-001` |
| clean canonical cyan source | `raw/clean_canonical_cyan_source.png` | 1254x1254 | `ALPHA-CLEANUP-001` |

Preview:

- `reports/generated_assets_contact_sheet.png`
- `reports/asset_manifest.json`

## Current Verdict

OBSERVED. These are raw generated candidates, not production assets.

Use them only after:

- chroma-key removal
- crop/mask extraction
- 2048x2048 full-canvas normalization
- overlay preview
- manual visual review

## Notes

- Mouth set A keeps the current character style closer.
- Mouth set B is simpler and may be easier to normalize for Live2D-style use.
- Blink sheet is closer to eyelid patches than the previous line-only blink, but stage quality is unverified.
- Clean canonical uses cyan chroma-key to compare against the previous green fringe issue.
