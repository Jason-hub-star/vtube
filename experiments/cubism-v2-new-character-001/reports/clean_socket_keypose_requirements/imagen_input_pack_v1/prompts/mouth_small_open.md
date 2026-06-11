Asset: mouth_small_open
Korean name: 작게 열린 입
Target group: mouth
Target parameter: ParamMouthOpenY=0.3

Common constraints:
- Use the selected character reference exactly: same identity, same face proportions, same anime rendering style, same front-facing camera, same lighting.
- Generate Live2D/Cubism material, not a new character design and not a sprite sheet.
- No labels, no guides, no text, no colored boxes, no extra face marks, no new accessories.
- Prefer transparent background/full-canvas layer output when possible.
- If the image model cannot output a true layer, generate a clean high-resolution reference and route it through the normalization/alpha validation step before use.

Task:
Create a style-matched mouth keypose for the specified state: closed smile, small open, wide open, or O vowel. Preserve the original mouth position, line style, lip softness, and anime shading.

Output requirements:
- Preferred: 2048x2048 RGBA full-canvas transparent PNG aligned to the provided reference canvas.
- If only a crop can be generated, keep the crop aspect ratio and include the ROI name in the filename; the normalization pipeline will place it into 2048x2048.
- Do not create a sprite sheet. Do not include labels or guide marks.
