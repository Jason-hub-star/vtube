# Live2D Part Success Patterns

- kind: `strong20`
- model_count: `20`
- cmo3_pass_or_warn: `20`

## eye

- decision: Use separate eye open/smile/eyeball/brow parameters; verify neutral and extreme eye screenshots.
- parameter_or_group_count: `{'min': 2, 'median': 15.0, 'max': 20, 'mean': 13.95}`
- motion_parameter_count: `{'min': 2, 'median': 15.0, 'max': 20, 'mean': 13.6}`
- part_count: `{'min': 1, 'median': 1.0, 'max': 14, 'mean': 2.6}`

| Model | Example |
|---|---|
| `haru_greeter_t05` | `{"model": "haru_greeter_t05", "params": ["ParamBrowLAngle", "ParamBrowLForm", "ParamBrowLX", "ParamBrowLY", "ParamBrowRAngle", "ParamBrowRForm", "ParamBrowRX", "ParamBrowRY", "Para` |
| `haruto_t01` | `{"model": "haruto_t01", "params": ["PARAM_BROW_L_ANGLE", "PARAM_BROW_L_FORM", "PARAM_BROW_L_X", "PARAM_BROW_L_Y", "PARAM_BROW_R_ANGLE", "PARAM_BROW_R_FORM", "PARAM_BROW_R_X", "PARA` |
| `hiyori_pro_t11` | `{"model": "hiyori_pro_t11", "params": ["ParamBrowLAngle", "ParamBrowLForm", "ParamBrowLX", "ParamBrowLY", "ParamBrowRAngle", "ParamBrowRForm", "ParamBrowRX", "ParamBrowRY", "ParamC` |
| `kei_basic_free_t02` | `{"model": "kei_basic_free_t02", "params": ["ParamBrowLForm", "ParamBrowLY", "ParamBrowRForm", "ParamBrowRY", "ParamCheek", "ParamEyeBallX", "ParamEyeBallY", "ParamEyeLOpen", "Param` |
| `kei_vowels_pro_t02` | `{"model": "kei_vowels_pro_t02", "params": ["ParamBrowLForm", "ParamBrowLY", "ParamBrowRForm", "ParamBrowRY", "ParamCheek", "ParamEyeBallX", "ParamEyeBallY", "ParamEyeLOpen", "Param` |

## mouth

- decision: Use MouthOpen/Form plus vowel/lip-sync references when available; Kei is the mouth baseline.
- parameter_or_group_count: `{'min': 0, 'median': 2.0, 'max': 9, 'mean': 2.6}`
- motion_parameter_count: `{'min': 0, 'median': 2.0, 'max': 9, 'mean': 2.15}`
- part_count: `{'min': 0, 'median': 1.0, 'max': 1, 'mean': 0.95}`

| Model | Example |
|---|---|
| `haru_greeter_t05` | `{"model": "haru_greeter_t05", "params": ["ParamMouthForm", "ParamMouthOpenY"], "motion_params": ["ParamMouthForm", "ParamMouthOpenY"], "parts": ["口"]}` |
| `haruto_t01` | `{"model": "haruto_t01", "params": ["PARAM_MOUTH_FORM", "PARAM_MOUTH_FORM_02", "PARAM_MOUTH_OPEN_Y"], "motion_params": ["PARAM_MOUTH_FORM", "PARAM_MOUTH_FORM_02", "PARAM_MOUTH_OPEN_` |
| `hiyori_pro_t11` | `{"model": "hiyori_pro_t11", "params": ["ParamMouthForm", "ParamMouthOpenY"], "motion_params": ["ParamMouthForm", "ParamMouthOpenY"], "parts": ["입"]}` |
| `kei_basic_free_t02` | `{"model": "kei_basic_free_t02", "params": ["ParamMouthForm", "ParamMouthOpenY"], "motion_params": [], "parts": ["입 기본"]}` |
| `kei_vowels_pro_t02` | `{"model": "kei_vowels_pro_t02", "params": ["ParamA", "ParamE", "ParamI", "ParamMouthOpenY", "ParamO", "ParamU"], "motion_params": [], "parts": ["입 모음만"]}` |

## hair

- decision: Use front/side/back hair parameters and physics outputs; Miku/Hiyori are primary hair baselines.
- parameter_or_group_count: `{'min': 0, 'median': 5.0, 'max': 23, 'mean': 5.6}`
- motion_parameter_count: `{'min': 0, 'median': 2.5, 'max': 10, 'mean': 2.9}`
- part_count: `{'min': 0, 'median': 3.0, 'max': 13, 'mean': 4.35}`

| Model | Example |
|---|---|
| `haru_greeter_t05` | `{"model": "haru_greeter_t05", "params": ["ParamHairBack", "ParamHairFront", "ParamHairSide"], "motion_params": ["ParamHairBack", "ParamHairFront", "ParamHairSide"], "parts": ["前髪",` |
| `haruto_t01` | `{"model": "haruto_t01", "params": ["PARAM_HAIR_BACK", "PARAM_HAIR_FLUFFY", "PARAM_HAIR_FLUFFY_02", "PARAM_HAIR_FRONT", "PARAM_HAIR_SIDE"], "motion_params": ["PARAM_HAIR_BACK", "PAR` |
| `hiyori_pro_t11` | `{"model": "hiyori_pro_t11", "params": ["ParamHairAhoge", "ParamHairBack", "ParamHairFront"], "motion_params": ["ParamHairAhoge"], "parts": ["뒷머리", "앞머리", "앞머리 오른쪽(스키닝)", "앞머리 오른쪽(회` |
| `kei_basic_free_t02` | `{"model": "kei_basic_free_t02", "params": ["ParamHairBack", "ParamHairBackFuwa", "ParamHairFront", "ParamHairFrontFuwa", "ParamHairSide", "ParamHairSide2", "ParamHairSideFuwa"], "m` |
| `kei_vowels_pro_t02` | `{"model": "kei_vowels_pro_t02", "params": ["ParamHairBack", "ParamHairBackFuwa", "ParamHairFront", "ParamHairFrontFuwa", "ParamHairSide", "ParamHairSide2", "ParamHairSideFuwa"], "m` |

## body_angle

- decision: Use AngleX/Y/Z and BodyAngleX/Y/Z as standard motion axes; avoid treating extreme sweep as natural pose.
- parameter_or_group_count: `{'min': 0, 'median': 2.5, 'max': 10, 'mean': 3.65}`
- motion_parameter_count: `{'min': 0, 'median': 0.0, 'max': 10, 'mean': 2.95}`
- part_count: `{'min': 0, 'median': 0.0, 'max': 4, 'mean': 0.85}`

| Model | Example |
|---|---|
| `haru_greeter_t05` | `{"model": "haru_greeter_t05", "params": ["ParamAngleX", "ParamAngleY", "ParamAngleZ", "ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ"], "motion_params": ["ParamAngleX", "Pa` |
| `haruto_t01` | `{"model": "haruto_t01", "params": [], "motion_params": [], "parts": []}` |
| `hiyori_pro_t11` | `{"model": "hiyori_pro_t11", "params": ["ParamAngleX", "ParamAngleY", "ParamAngleZ", "ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ"], "motion_params": ["ParamAngleX", "Para` |
| `kei_basic_free_t02` | `{"model": "kei_basic_free_t02", "params": ["ParamAngleX", "ParamAngleY", "ParamAngleZ", "ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ"], "motion_params": [], "parts": ["목"` |
| `kei_vowels_pro_t02` | `{"model": "kei_vowels_pro_t02", "params": ["ParamAngleX", "ParamAngleY", "ParamAngleZ", "ParamBodyAngleX", "ParamBodyAngleY", "ParamBodyAngleZ"], "motion_params": [], "parts": ["목"` |

## arm

- decision: Keep optional for v2_min, but include arm/hand/shoulder variants in v2_standard when the design needs gestures.
- parameter_or_group_count: `{'min': 0, 'median': 5.0, 'max': 37, 'mean': 7.95}`
- motion_parameter_count: `{'min': 0, 'median': 5.0, 'max': 37, 'mean': 7.85}`
- part_count: `{'min': 0, 'median': 0.0, 'max': 8, 'mean': 1.3}`

| Model | Example |
|---|---|
| `haru_greeter_t05` | `{"model": "haru_greeter_t05", "params": ["ParamArmLA", "ParamArmLB", "ParamArmRA", "ParamArmRB", "ParamHandAngleL", "ParamHandAngleR", "ParamHandChangeR", "ParamHandDhangeL"], "mot` |
| `haruto_t01` | `{"model": "haruto_t01", "params": ["PARAM_ARM_L", "PARAM_ARM_L_01", "PARAM_ARM_L_02", "PARAM_ARM_L_03", "PARAM_ARM_R", "PARAM_ARM_R_01", "PARAM_ARM_R_02", "PARAM_ARM_R_03", "PARAM_` |
| `hiyori_pro_t11` | `{"model": "hiyori_pro_t11", "params": ["ParamArmLA", "ParamArmLB", "ParamArmRA", "ParamArmRB", "ParamHandL", "ParamHandLB", "ParamHandR", "ParamHandRB", "ParamShoulder"], "motion_p` |
| `kei_basic_free_t02` | `{"model": "kei_basic_free_t02", "params": [], "motion_params": [], "parts": []}` |
| `kei_vowels_pro_t02` | `{"model": "kei_vowels_pro_t02", "params": [], "motion_params": [], "parts": []}` |

## physics

- decision: Require physics groups for hair/body secondary motion; use output category coverage as the main quality signal.
- parameter_or_group_count: `{'min': 1, 'median': 5.5, 'max': 19, 'mean': 7.2}`
- motion_parameter_count: `{'min': None, 'median': None, 'max': None, 'mean': None}`
- part_count: `{'min': None, 'median': None, 'max': None, 'mean': None}`

| Model | Example |
|---|---|
| `haru_greeter_t05` | `{"model": "haru_greeter_t05", "physics_groups": 4, "outputs": ["ParamHairBack", "ParamHairFront", "ParamHairSide", "ParamScarf"]}` |
| `haruto_t01` | `{"model": "haruto_t01", "physics_groups": 4, "outputs": ["PARAM_HAIR_BACK", "PARAM_HAIR_FRONT", "PARAM_HAIR_SIDE", "PARAM_NECKTIE"]}` |
| `hiyori_pro_t11` | `{"model": "hiyori_pro_t11", "physics_groups": 11, "outputs": ["ParamBustY", "ParamHairBack", "ParamHairFront", "ParamRibbon", "ParamSideupRibbon", "ParamSkirt", "ParamSkirt2", "Par` |
| `kei_basic_free_t02` | `{"model": "kei_basic_free_t02", "physics_groups": 6, "outputs": ["ParamHairBack", "ParamHairBackFuwa", "ParamHairFront", "ParamHairFrontFuwa", "ParamHairSide", "ParamHairSide2", "P` |
| `kei_vowels_pro_t02` | `{"model": "kei_vowels_pro_t02", "physics_groups": 6, "outputs": ["ParamHairBack", "ParamHairBackFuwa", "ParamHairFront", "ParamHairFrontFuwa", "ParamHairSide", "ParamHairSide2", "P` |

## mask_pose_expression

- decision: Use mask/pose/expression only when design needs it; do not force rich-sample complexity into v2_min.
- parameter_or_group_count: `{'min': None, 'median': None, 'max': None, 'mean': None}`
- motion_parameter_count: `{'min': None, 'median': None, 'max': None, 'mean': None}`
- part_count: `{'min': None, 'median': None, 'max': None, 'mean': None}`

| Model | Example |
|---|---|
| `haru_greeter_t05` | `{"model": "haru_greeter_t05", "has_pose": true, "expression_count": 0, "glue_count": 0}` |
| `haruto_t01` | `{"model": "haruto_t01", "has_pose": false, "expression_count": 0, "glue_count": 0}` |
| `hiyori_pro_t11` | `{"model": "hiyori_pro_t11", "has_pose": true, "expression_count": 0, "glue_count": 26}` |
| `kei_basic_free_t02` | `{"model": "kei_basic_free_t02", "has_pose": false, "expression_count": 0, "glue_count": 1}` |
| `kei_vowels_pro_t02` | `{"model": "kei_vowels_pro_t02", "has_pose": false, "expression_count": 0, "glue_count": 1}` |

## psd_layering

- decision: Use PSD/material split examples as taxonomy guidance only; do not reuse official art assets.
- parameter_or_group_count: `{'min': None, 'median': None, 'max': None, 'mean': None}`
- motion_parameter_count: `{'min': None, 'median': None, 'max': None, 'mean': None}`
- part_count: `{'min': None, 'median': None, 'max': None, 'mean': None}`

| Model | Example |
|---|---|
| `haru_greeter_t05` | `{"model": "haru_greeter_t05", "psd_count": 2, "has_psd": true}` |
| `haruto_t01` | `{"model": "haruto_t01", "psd_count": 4, "has_psd": true}` |
| `hiyori_pro_t11` | `{"model": "hiyori_pro_t11", "psd_count": 0, "has_psd": false}` |
| `kei_basic_free_t02` | `{"model": "kei_basic_free_t02", "psd_count": 0, "has_psd": false}` |
| `kei_vowels_pro_t02` | `{"model": "kei_vowels_pro_t02", "psd_count": 0, "has_psd": false}` |
