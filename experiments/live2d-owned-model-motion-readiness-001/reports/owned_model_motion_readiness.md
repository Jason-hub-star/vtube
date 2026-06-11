# 보유 Live2D 모델 움직임 준비도

- total_models: `57`
- strong_motion_reference: `25`
- runtime_motion_checkable: `19`
- structure_good_but_motion_missing: `8`
- not_motion_ready: `5`

## 결론

- 레거시 이미지는 실패 fixture 용도일 뿐, 보유 모델 검수 대상이 아닙니다.
- `STRONG_MOTION_REFERENCE` 모델은 구조와 motion/physics가 모두 있어 움직임 기준선으로 쓰기 좋습니다.
- `RUNTIME_MOTION_CHECKABLE` 모델은 실제 렌더링 프리뷰로 움직임 확인은 가능하지만 편집 구조 학습은 제한됩니다.
- 최종적으로 잘 움직이는지는 model3/moc3/motion3를 브라우저 Live2D player에 올려 눈으로 확인해야 합니다.

## Top Strong Motion References
- `haru_greeter_t05` score `100` / physics `4` / deformer `66+31` / keyform `221`
- `haruto_t01` score `100` / physics `4` / deformer `58+18` / keyform `215`
- `hiyori_pro_t11` score `100` / physics `11` / deformer `50+54` / keyform `346`
- `kei_basic_free_t02` score `100` / physics `6` / deformer `47+2` / keyform `150`
- `kei_vowels_pro_t02` score `100` / physics `6` / deformer `46+2` / keyform `141`
- `koharu_t01` score `100` / physics `5` / deformer `63+18` / keyform `220`
- `mao_pro_t06` score `100` / physics `16` / deformer `116+59` / keyform `497`
- `miara_pro_t04` score `100` / physics `19` / deformer `93+107` / keyform `467`
- `miku_sample_t05` score `100` / physics `13` / deformer `27+38` / keyform `233`
- `natori_pro_t06` score `100` / physics `11` / deformer `128+52` / keyform `407`
- `ren_t01` score `100` / physics `16` / deformer `128+22` / keyform `470`
- `rice_pro_t03` score `100` / physics `9` / deformer `58+80` / keyform `306`
- `tsumiki_t01` score `100` / physics `7` / deformer `67+22` / keyform `240`
- `wanko_touch_t01` score `100` / physics `4` / deformer `28+6` / keyform `85`
- `Epsilon_t02` score `95` / physics `2` / deformer `51+12` / keyform `169`

## Runtime Check Candidates
- `Haru` score `60` / physics `4` / mode `RUNTIME_ONLY`
- `Haru` score `60` / physics `4` / mode `RUNTIME_ONLY`
- `Hiyori` score `60` / physics `11` / mode `RUNTIME_ONLY`
- `Hiyori` score `60` / physics `11` / mode `RUNTIME_ONLY`
- `Kei_basic` score `60` / physics `6` / mode `RUNTIME_ONLY`
- `Kei_vowels` score `60` / physics `6` / mode `RUNTIME_ONLY`
- `Mao` score `60` / physics `16` / mode `RUNTIME_ONLY`
- `Mao` score `60` / physics `16` / mode `RUNTIME_ONLY`
- `Natori` score `60` / physics `11` / mode `RUNTIME_ONLY`
- `Natori` score `60` / physics `11` / mode `RUNTIME_ONLY`
- `Rice` score `60` / physics `9` / mode `RUNTIME_ONLY`
- `Rice` score `60` / physics `9` / mode `RUNTIME_ONLY`
- `Rice` score `60` / physics `9` / mode `RUNTIME_ONLY`
- `Wanko` score `60` / physics `4` / mode `RUNTIME_ONLY`
- `Wanko` score `60` / physics `4` / mode `RUNTIME_ONLY`
