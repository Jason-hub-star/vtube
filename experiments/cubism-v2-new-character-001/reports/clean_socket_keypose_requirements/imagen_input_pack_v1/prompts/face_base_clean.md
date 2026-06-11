Asset: face_base_clean
Korean name: 눈/입 잔상이 없는 얼굴 기본
Target group: face
Target parameter: ParamEyeLOpen, ParamEyeROpen, ParamMouthOpenY, ParamMouthForm

Common constraints:
- Use the selected character reference exactly: same identity, same face proportions, same anime rendering style, same front-facing camera, same lighting.
- Generate Live2D/Cubism material, not a new character design and not a sprite sheet.
- No labels, no guides, no text, no colored boxes, no extra face marks, no new accessories.
- Prefer transparent background/full-canvas layer output when possible.
- If the image model cannot output a true layer, generate a clean high-resolution reference and route it through the normalization/alpha validation step before use.

Task:
Create a clean full face base material. Remove baked open-eye pixels and mouth remnants while preserving skin tone, blush, nose, cheek shading, face contour, and hair occlusion. This must be usable under all eye and mouth keyposes.

Output requirements:
- Preferred: 2048x2048 RGBA full-canvas transparent PNG aligned to the provided reference canvas.
- If only a crop can be generated, keep the crop aspect ratio and include the ROI name in the filename; the normalization pipeline will place it into 2048x2048.
- Do not create a sprite sheet. Do not include labels or guide marks.
