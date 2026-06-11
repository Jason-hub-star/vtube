Asset: mouth_base_clean
Korean name: 입 잔상이 없는 깨끗한 입 주변 피부/입 베이스
Target group: mouth
Target parameter: ParamMouthOpenY, ParamMouthForm

Common constraints:
- Use the selected character reference exactly: same identity, same face proportions, same anime rendering style, same front-facing camera, same lighting.
- Generate Live2D/Cubism material, not a new character design and not a sprite sheet.
- No labels, no guides, no text, no colored boxes, no extra face marks, no new accessories.
- Prefer transparent background/full-canvas layer output when possible.
- If the image model cannot output a true layer, generate a clean high-resolution reference and route it through the normalization/alpha validation step before use.

Task:
Create clean mouth-base material around the mouth area. Remove baked mouth line/open-mouth remnants while preserving face shading, chin, blush, and surrounding skin style.

Output requirements:
- Preferred: 2048x2048 RGBA full-canvas transparent PNG aligned to the provided reference canvas.
- If only a crop can be generated, keep the crop aspect ratio and include the ROI name in the filename; the normalization pipeline will place it into 2048x2048.
- Do not create a sprite sheet. Do not include labels or guide marks.
