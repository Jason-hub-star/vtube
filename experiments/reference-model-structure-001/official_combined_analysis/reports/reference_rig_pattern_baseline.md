# Reference Rig Pattern Baseline

Generated: 2026-06-05T15:27:42.509429+00:00

Source: https://www.live2d.com/ko/learn/sample/

This baseline learns structure and rigging patterns only. It must not be used to copy official sample art, textures, PSD layers, or character designs.

## eye

| Model | Decision | Learning Target | Measured Max Counts |
|---|---|---|---|
| Epsilon | REFERENCE_ONLY | standard easy-to-use model, expression effects | models=1, art=73, param=37, warp=51, rot=12, key=169, phys=2, motion=15, psd=0 |
| Momose Hiyori | KEEP | standard Cubism 3.0 model, deformer structure, parameter structure, hair skinning | models=4, art=149, param=78, warp=62, rot=56, key=382, phys=11, motion=30, psd=0 |
| Niziiro Mao | KEEP | blend shapes, multiply and screen color, mouth, eyebrow, and hair additive shape differences, wide face motion range | models=3, art=262, param=132, warp=116, rot=59, key=497, phys=16, motion=23, psd=0 |
| Mark-kun | KEEP | simple deformer structure, simple parameter structure, physics, eye blink, PSD availability | models=3, art=33, param=27, warp=26, rot=13, key=90, phys=1, motion=12, psd=0 |
| Tsumiki | KEEP | eyelid clipping mask, standard avatar motion | models=1, art=89, param=46, warp=67, rot=22, key=240, phys=7, motion=23, psd=0 |
| Unity-chan | KEEP | eyelid clipping mask, PSD layer reference, deformed character model | models=1, art=70, param=39, warp=40, rot=15, key=140, phys=3, motion=16, psd=2 |

## mouth

| Model | Decision | Learning Target | Measured Max Counts |
|---|---|---|---|
| Epsilon | REFERENCE_ONLY | standard easy-to-use model, expression effects | models=1, art=73, param=37, warp=51, rot=12, key=169, phys=2, motion=15, psd=0 |
| Momose Hiyori | KEEP | standard Cubism 3.0 model, deformer structure, parameter structure, hair skinning | models=4, art=149, param=78, warp=62, rot=56, key=382, phys=11, motion=30, psd=0 |
| Kei | KEEP | motion sync, lip-sync presets, mouth parameter composition | models=2, art=61, param=31, warp=47, rot=2, key=150, phys=6, motion=8, psd=0 |
| Niziiro Mao | KEEP | blend shapes, multiply and screen color, mouth, eyebrow, and hair additive shape differences, wide face motion range | models=3, art=262, param=132, warp=116, rot=59, key=497, phys=16, motion=23, psd=0 |
| Mark-kun | REFERENCE_ONLY | simple deformer structure, simple parameter structure, physics, eye blink, PSD availability | models=3, art=33, param=27, warp=26, rot=13, key=90, phys=1, motion=12, psd=0 |
| Nito | KEEP | two-head character, multiple variants in one model, large mouth expression, limbless comical motion | models=5, art=299, param=66, warp=137, rot=145, key=559, phys=0, motion=105, psd=0 |

## hair

| Model | Decision | Learning Target | Measured Max Counts |
|---|---|---|---|
| Momose Hiyori | KEEP | standard Cubism 3.0 model, deformer structure, parameter structure, hair skinning | models=4, art=149, param=78, warp=62, rot=56, key=382, phys=11, motion=30, psd=0 |
| Niziiro Mao | KEEP | blend shapes, multiply and screen color, mouth, eyebrow, and hair additive shape differences, wide face motion range | models=3, art=262, param=132, warp=116, rot=59, key=497, phys=16, motion=23, psd=0 |
| Hatsune Miku | KEEP | twin-tail hair skinning, smooth long hair motion | models=1, art=116, param=59, warp=27, rot=38, key=233, phys=13, motion=8, psd=0 |
| Rice Glassfield | REFERENCE_ONLY | extended interpolation, inverted mask, forelock and fire effects | models=5, art=183, param=96, warp=58, rot=85, key=306, phys=9, motion=16, psd=0 |

## body_angle

| Model | Decision | Learning Target | Measured Max Counts |
|---|---|---|---|
| Chitose | REFERENCE_ONLY | male avatar model, right-arm switching, handwave motion | models=1, art=79, param=33, warp=54, rot=13, key=175, phys=2, motion=4, psd=0 |
| Haru | REFERENCE_ONLY | arm switching, clothing changes, voice and expression testing, overall Live2D feature test | models=3, art=114, param=42, warp=53, rot=34, key=267, phys=4, motion=35, psd=0 |
| Momose Hiyori | KEEP | standard Cubism 3.0 model, deformer structure, parameter structure, hair skinning | models=4, art=149, param=78, warp=62, rot=56, key=382, phys=11, motion=30, psd=0 |
| Izumi | KEEP | multiple art styles, oblique source pose, opposite-facing motion | models=4, art=77, param=30, warp=39, rot=6, key=171, phys=3, motion=40, psd=0 |
| Niziiro Mao | KEEP | blend shapes, multiply and screen color, mouth, eyebrow, and hair additive shape differences, wide face motion range | models=3, art=262, param=132, warp=116, rot=59, key=497, phys=16, motion=23, psd=0 |
| Miara | REFERENCE_ONLY | full-body avatar, voice motion, physics baseline | models=1, art=245, param=138, warp=93, rot=107, key=467, phys=19, motion=3, psd=0 |
| Parameter Controller Sample | REFERENCE_ONLY | parameter controller, target following, animation efficiency | models=2, art=3, param=27, warp=0, rot=1, key=2, phys=0, motion=0, psd=0 |
| Ren Foster | REFERENCE_ONLY | Cubism 5.3 rich drawing, alpha blend masks, offscreen rendering, high-spec avatar expression | models=3, art=201, param=73, warp=128, rot=22, key=470, phys=16, motion=9, psd=0 |

## physics

| Model | Decision | Learning Target | Measured Max Counts |
|---|---|---|---|
| Haru | REFERENCE_ONLY | arm switching, clothing changes, voice and expression testing, overall Live2D feature test | models=3, art=114, param=42, warp=53, rot=34, key=267, phys=4, motion=35, psd=0 |
| Momose Hiyori | KEEP | standard Cubism 3.0 model, deformer structure, parameter structure, hair skinning | models=4, art=149, param=78, warp=62, rot=56, key=382, phys=11, motion=30, psd=0 |
| Kei | REFERENCE_ONLY | motion sync, lip-sync presets, mouth parameter composition | models=2, art=61, param=31, warp=47, rot=2, key=150, phys=6, motion=8, psd=0 |
| Mark-kun | KEEP | simple deformer structure, simple parameter structure, physics, eye blink, PSD availability | models=3, art=33, param=27, warp=26, rot=13, key=90, phys=1, motion=12, psd=0 |
| Miara | REFERENCE_ONLY | full-body avatar, voice motion, physics baseline | models=1, art=245, param=138, warp=93, rot=107, key=467, phys=19, motion=3, psd=0 |
| Hatsune Miku | KEEP | twin-tail hair skinning, smooth long hair motion | models=1, art=116, param=59, warp=27, rot=38, key=233, phys=13, motion=8, psd=0 |
| Natori | REFERENCE_ONLY | expressions, pose, motion baseline, physics baseline | models=3, art=176, param=96, warp=128, rot=52, key=407, phys=11, motion=24, psd=0 |
| Ren Foster | REFERENCE_ONLY | Cubism 5.3 rich drawing, alpha blend masks, offscreen rendering, high-spec avatar expression | models=3, art=201, param=73, warp=128, rot=22, key=470, phys=16, motion=9, psd=0 |
| Shizuku | REFERENCE_ONLY | legacy sample structure, pose and physics baseline | models=1, art=187, param=45, warp=156, rot=27, key=358, phys=3, motion=4, psd=0 |
| Wanko | REFERENCE_ONLY | touch motions, non-human avatar runtime, physics baseline | models=3, art=78, param=25, warp=28, rot=6, key=85, phys=4, motion=22, psd=0 |

## mask

| Model | Decision | Learning Target | Measured Max Counts |
|---|---|---|---|
| Gantzert & Felixander | KEEP | additive drawing effects, many clipping expressions, right hand, dragon wings, thunder and fire reflection | models=1, art=249, param=74, warp=52, rot=38, key=537, phys=0, motion=6, psd=0 |
| Ren Foster | KEEP | Cubism 5.3 rich drawing, alpha blend masks, offscreen rendering, high-spec avatar expression | models=3, art=201, param=73, warp=128, rot=22, key=470, phys=16, motion=9, psd=0 |
| Rice Glassfield | KEEP | extended interpolation, inverted mask, forelock and fire effects | models=5, art=183, param=96, warp=58, rot=85, key=306, phys=9, motion=16, psd=0 |
| Tsumiki | KEEP | eyelid clipping mask, standard avatar motion | models=1, art=89, param=46, warp=67, rot=22, key=240, phys=7, motion=23, psd=0 |
| Unity-chan | KEEP | eyelid clipping mask, PSD layer reference, deformed character model | models=1, art=70, param=39, warp=40, rot=15, key=140, phys=3, motion=16, psd=2 |

## psd_layering

| Model | Decision | Learning Target | Measured Max Counts |
|---|---|---|---|
| Haru Greeter | KEEP | PSD material division, PSD import material structure, avatar greeting motions | models=1, art=86, param=42, warp=66, rot=31, key=221, phys=4, motion=27, psd=2 |
| Haruto | KEEP | PSD material division, paired sample character, runtime motion baseline | models=2, art=87, param=51, warp=58, rot=20, key=215, phys=4, motion=11, psd=4 |
| Koharu | KEEP | PSD material division, paired sample character, runtime motion baseline | models=2, art=91, param=52, warp=63, rot=20, key=220, phys=5, motion=11, psd=4 |
| Mark-kun | KEEP | simple deformer structure, simple parameter structure, physics, eye blink, PSD availability | models=3, art=33, param=27, warp=26, rot=13, key=90, phys=1, motion=12, psd=0 |
| Unity-chan | REFERENCE_ONLY | eyelid clipping mask, PSD layer reference, deformed character model | models=1, art=70, param=39, warp=40, rot=15, key=140, phys=3, motion=16, psd=2 |

## motion_pose

| Model | Decision | Learning Target | Measured Max Counts |
|---|---|---|---|
| Chitose | KEEP | male avatar model, right-arm switching, handwave motion | models=1, art=79, param=33, warp=54, rot=13, key=175, phys=2, motion=4, psd=0 |
| Epsilon | REFERENCE_ONLY | standard easy-to-use model, expression effects | models=1, art=73, param=37, warp=51, rot=12, key=169, phys=2, motion=15, psd=0 |
| Gantzert & Felixander | REFERENCE_ONLY | additive drawing effects, many clipping expressions, right hand, dragon wings, thunder and fire reflection | models=1, art=249, param=74, warp=52, rot=38, key=537, phys=0, motion=6, psd=0 |
| Haru | KEEP | arm switching, clothing changes, voice and expression testing, overall Live2D feature test | models=3, art=114, param=42, warp=53, rot=34, key=267, phys=4, motion=35, psd=0 |
| Haru Greeter | REFERENCE_ONLY | PSD material division, PSD import material structure, avatar greeting motions | models=1, art=86, param=42, warp=66, rot=31, key=221, phys=4, motion=27, psd=2 |
| Haruto | REFERENCE_ONLY | PSD material division, paired sample character, runtime motion baseline | models=2, art=87, param=51, warp=58, rot=20, key=215, phys=4, motion=11, psd=4 |
| Izumi | REFERENCE_ONLY | multiple art styles, oblique source pose, opposite-facing motion | models=4, art=77, param=30, warp=39, rot=6, key=171, phys=3, motion=40, psd=0 |
| Koharu | REFERENCE_ONLY | PSD material division, paired sample character, runtime motion baseline | models=2, art=91, param=52, warp=63, rot=20, key=220, phys=5, motion=11, psd=4 |
| Niziiro Mao | REFERENCE_ONLY | blend shapes, multiply and screen color, mouth, eyebrow, and hair additive shape differences, wide face motion range | models=3, art=262, param=132, warp=116, rot=59, key=497, phys=16, motion=23, psd=0 |
| Natori | KEEP | expressions, pose, motion baseline, physics baseline | models=3, art=176, param=96, warp=128, rot=52, key=407, phys=11, motion=24, psd=0 |
| Nito | KEEP | two-head character, multiple variants in one model, large mouth expression, limbless comical motion | models=5, art=299, param=66, warp=137, rot=145, key=559, phys=0, motion=105, psd=0 |
| Parameter Controller Sample | REFERENCE_ONLY | parameter controller, target following, animation efficiency | models=2, art=3, param=27, warp=0, rot=1, key=2, phys=0, motion=0, psd=0 |
| Rice Glassfield | REFERENCE_ONLY | extended interpolation, inverted mask, forelock and fire effects | models=5, art=183, param=96, warp=58, rot=85, key=306, phys=9, motion=16, psd=0 |
| Shizuku | REFERENCE_ONLY | legacy sample structure, pose and physics baseline | models=1, art=187, param=45, warp=156, rot=27, key=358, phys=3, motion=4, psd=0 |
| Wanko | REFERENCE_ONLY | touch motions, non-human avatar runtime, physics baseline | models=3, art=78, param=25, warp=28, rot=6, key=85, phys=4, motion=22, psd=0 |

## New Image Generation Requirements

- 완전 신규 2048 정면 단일 원본 캐릭터
- 눈 흰자/홍채/속눈썹이 분리되기 쉬운 크고 명확한 눈
- 입 라인이 작게 묻히지 않고 ParamMouthOpenY/Form 기준 keyform을 만들 수 있는 얼굴
- 앞머리/옆머리/뒷머리 흐름이 구분되는 헤어 실루엣
- ParamAngleX/Y와 BodyAngleX/Y에서 overhang이 적도록 목/어깨/상체가 가려지지 않는 구조
- 초기 모델에서는 무거운 clipping/mask/rich effect를 최소화
- 텍스트, 라벨, 잘린 팔, 과도한 장식, 복잡한 손가락 겹침 금지

## Minimal Cubism Rig Gate

- Scope: eye, mouth, hair, body_angle
- Delta: warp_deformers > 0
- Delta: keyform_bindings > 0
- Evidence: before/after cmo3_structure_report.json
- Evidence: deformer hierarchy screenshot
- Evidence: eye/mouth/hair/body angle parameter extreme screenshots
- Evidence: draw order and overhang review note

## Missing Profile Model IDs

- `github_live2d_cubism_web_motionsync_samples_resources_kei_basic_kei_basic.model3`
- `github_live2d_cubism_web_motionsync_samples_resources_kei_vowels_kei_vowels.model3`
