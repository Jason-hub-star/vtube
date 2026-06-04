# validation-smoke-001

작성일: 2026-06-02

## 목적

아래 세 가지를 직접 검증한다.

```text
1. 현재 imagegen mouth/eye PNG에서 실제 crop/mask가 되는지 확인
2. canonical_front 위에 mouth/eye 후보를 합성해 표정 후보로 쓸 수 있는지 확인
3. See-through/ComfyUI-See-through가 주인님 Mac 환경에서 canonical_front를 처리할 수 있는지 확인
```

## 입력

```text
/Users/family/jason/Vtube/experiments/imagegen-limit-test-001/generated/canonical_front.png
/Users/family/jason/Vtube/experiments/imagegen-limit-test-002/generated/individual_mouth_parts.png
/Users/family/jason/Vtube/experiments/imagegen-limit-test-002/generated/individual_eye_parts.png
```

## 실행 명령

```bash
python3 /Users/family/jason/Vtube/experiments/validation-smoke-001/scripts/crop_mask_composite_smoke.py
```

## 결과

```text
mouth crop/mask: PASS
eye crop/mask: PASS
canonical composite smoke: PASS
See-through local Mac direct processing: BLOCKED
ComfyUI-See-through standalone processing: BLOCKED
```

## Evidence 파일

```text
reports/crop_mask_composite_report.json
reports/qa_report.md
reports/see_through_environment_report.md
crops/mouth/*.png
crops/eye/*.png
composites/*.png
```

## 판정

```text
imagegen mouth 후보:
  계속 테스트할 가치 있음

imagegen eye 후보:
  crop/mask는 가능하지만 semantic 분류와 canonical 위치 보정이 필수

See-through:
  현재 Mac 로컬 confirmed core path로 두면 안 됨
  remote GPU, HuggingFace Space, ModelScope, 별도 ComfyUI 환경 중 하나로 재검증 필요
```

## 다음 액션

```text
1. eye component semantic classifier spike
2. mouth 후보 위치/스케일 자동 보정 spike
3. layer_manifest schema 최소화
4. See-through remote/ComfyUI 검증 경로 선택
```
