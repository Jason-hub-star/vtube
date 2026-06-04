# CREATURE-SCHEMA-001 Anchor Schema Plan

작성일: 2026-06-02

## Verdict

```text
status: VERIFIED
decision: keep
```

사람형 anime 공식은 다른 생명체/마스코트형 캐릭터에 자동 적용하지 않는다. 캐릭터 타입별 required anchor가 없으면 해당 타입의 coordinate alignment는 실패 처리한다.

## 공통 규칙

```text
1. schema_type을 먼저 결정한다.
2. schema_type별 required anchors를 모두 검출해야 한다.
3. required anchor가 없으면 fallback 추정으로 production PASS를 주지 않는다.
4. screenshot은 마지막 QA evidence로만 사용한다.
5. full-canvas layer가 가능하면 crop/scale/place보다 우선한다.
```

## human_anime

```json
{
  "schema_type": "human_anime",
  "required_anchors": [
    "left_iris_center",
    "right_iris_center",
    "face_center_x"
  ],
  "optional_anchors": [
    "mouth_line_center",
    "chin_center",
    "brow_l_center",
    "brow_r_center"
  ],
  "derived_metrics": [
    "eye_distance_px",
    "mouth_target_center",
    "mouth_target_width_px",
    "eye_target_width_px"
  ],
  "failure_rule": "If two iris centers are not detected, do not infer mouth/eye placement."
}
```

## dog_mascot

```json
{
  "schema_type": "dog_mascot",
  "required_anchors": [
    "left_eye_center",
    "right_eye_center",
    "nose_tip",
    "muzzle_center"
  ],
  "optional_anchors": [
    "mouth_curve_center",
    "left_ear_base",
    "right_ear_base",
    "chin_or_muzzle_bottom"
  ],
  "derived_metrics": [
    "eye_distance_px",
    "muzzle_width_px",
    "mouth_target_center",
    "mouth_target_width_px"
  ],
  "failure_rule": "If nose_tip or muzzle_center is missing, do not reuse human mouth formula."
}
```

## cat_mascot

```json
{
  "schema_type": "cat_mascot",
  "required_anchors": [
    "left_eye_center",
    "right_eye_center",
    "nose_tip",
    "muzzle_center"
  ],
  "optional_anchors": [
    "left_ear_tip",
    "right_ear_tip",
    "left_whisker_root",
    "right_whisker_root",
    "mouth_curve_center"
  ],
  "derived_metrics": [
    "eye_distance_px",
    "muzzle_width_px",
    "mouth_target_center",
    "mouth_target_width_px"
  ],
  "failure_rule": "If muzzle anchors are missing, only allow iris/eye placement; block mouth placement."
}
```

## Test Acceptance

```text
PASS:
  human_anime, dog_mascot, cat_mascot have separate required anchors.
  mascot schemas include nose/muzzle anchors.
  missing anchor rule blocks unsafe human-formula reuse.

FAIL:
  any non-human schema derives mouth solely from human eye distance.
  missing anchors silently fall back to human_anime geometry.
```

## Next Action

```text
Create one generated dog/cat mascot canonical fixture before testing mascot placement.
Do not test non-human placement using the current human anime canonical.
```
