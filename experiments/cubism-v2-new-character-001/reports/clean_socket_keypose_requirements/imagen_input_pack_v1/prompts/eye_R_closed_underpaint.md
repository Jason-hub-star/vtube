Asset: eye_R_closed_underpaint
Korean name: 오른눈 닫힘용 피부 밑색
Target group: eye_R
Target parameter: ParamEyeROpen

Common constraints:
- Use the selected character reference exactly: same identity, same face proportions, same anime rendering style, same front-facing camera, same lighting.
- Generate Live2D/Cubism material, not a new character design and not a sprite sheet.
- No labels, no guides, no text, no colored boxes, no extra face marks, no new accessories.
- Prefer transparent background/full-canvas layer output when possible.
- If the image model cannot output a true layer, generate a clean high-resolution reference and route it through the normalization/alpha validation step before use.

Task:
Create clean eye-socket skin material for the specified left/right eye area. Remove iris, pupil, white of eye, highlight, and open-eye lash artifacts. Preserve surrounding skin gradient, blush, eyelid fold, and hair occlusion style. Output only the clean material needed under closed eyelids. Make it a soft underpaint layer for closed-eye states.

Output requirements:
- Preferred: 2048x2048 RGBA full-canvas transparent PNG aligned to the provided reference canvas.
- If only a crop can be generated, keep the crop aspect ratio and include the ROI name in the filename; the normalization pipeline will place it into 2048x2048.
- Do not create a sprite sheet. Do not include labels or guide marks.
