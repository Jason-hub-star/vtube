Asset: eye_R_closed_lid
Korean name: 오른눈 완전히 감은 눈꺼풀/감은 눈 선
Target group: eye_R
Target parameter: ParamEyeROpen=0

Common constraints:
- Use the selected character reference exactly: same identity, same face proportions, same anime rendering style, same front-facing camera, same lighting.
- Generate Live2D/Cubism material, not a new character design and not a sprite sheet.
- No labels, no guides, no text, no colored boxes, no extra face marks, no new accessories.
- Prefer transparent background/full-canvas layer output when possible.
- If the image model cannot output a true layer, generate a clean high-resolution reference and route it through the normalization/alpha validation step before use.

Task:
Create a style-matched eyelid keypose for the specified eye: half closed, mostly closed, or fully closed. Preserve the original character style, lash thickness, eyelid curve, and left/right symmetry. Do not include the open iris/pupil/eye white.

Output requirements:
- Preferred: 2048x2048 RGBA full-canvas transparent PNG aligned to the provided reference canvas.
- If only a crop can be generated, keep the crop aspect ratio and include the ROI name in the filename; the normalization pipeline will place it into 2048x2048.
- Do not create a sprite sheet. Do not include labels or guide marks.
