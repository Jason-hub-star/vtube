# Live2D 보유 모델 실제 테스트

- tested_models: `8`
- runtime_motion_pass: `8`
- view_pass: `5`
- view_warn: `3`
- view_fail: `0`

## 해석

- 이 테스트는 `model3/moc3/motion3/physics3/texture` 파일 기준 검사입니다.
- `view_warn`은 텍스처 alpha가 atlas 가장자리에 닿아 실제 player에서 잘림 여부를 눈으로 확인해야 한다는 뜻입니다.
- 진짜 최종 판정은 Cubism Web player 렌더링 스크린샷/GIF가 필요합니다.

## Models
- `Haru` runtime `PASS` / view `PASS` / motions `6` / animated params `42` / physics `4`
- `Hiyori` runtime `PASS` / view `PASS` / motions `10` / animated params `35` / physics `11`
- `Mao` runtime `PASS` / view `WARN` / motions `8` / animated params `132` / physics `16`
- `Mark` runtime `PASS` / view `PASS` / motions `6` / animated params `19` / physics `1`
- `Natori` runtime `PASS` / view `PASS` / motions `8` / animated params `95` / physics `11`
- `Ren` runtime `PASS` / view `WARN` / motions `3` / animated params `68` / physics `16`
- `Rice` runtime `PASS` / view `PASS` / motions `4` / animated params `54` / physics `9`
- `Wanko` runtime `PASS` / view `WARN` / motions `5` / animated params `22` / physics `4`
