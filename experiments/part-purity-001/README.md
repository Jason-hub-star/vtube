# Part Purity Review 001

이 실험은 Live2D/Cubism production 파츠 순도 검수의 현재 작업 공간이다.
검수 UI는 `review_app/`, 서버는 `scripts/review_app_server.py`에 있다.

운영 계획은 `docs/ref/LIVE2D-PART-PURITY-PIPELINE.md`를 따른다.

## Files

- `part_generation_manifest.json`: AI 이미지 생성/정리 대상 목록.
- `reports/part_visual_review.json`: 사람이 저장한 원본 검수 결과.
- `reports/ai_fix_queue.json`: AI가 바로 읽는 재생성/cleanup 큐.

## Local Run

```bash
python3 scripts/build_review_manifest.py
python3 scripts/review_app_server.py --port 8040
```

Open `http://127.0.0.1:8040/`.

## Review Flow

1. `PSD 파츠 27개` 탭에서 production 파츠를 하나씩 확인한다.
2. `확대 비교`와 `파츠만 확대`로 실제 파츠와 오염 여부를 본다.
3. `O 통과`, `X 실패`, `수정 필요`, `참고용` 중 하나를 저장한다.
4. 실패/수정 파츠는 문제 태그와 메모를 남긴다.
5. `ai_fix_queue.json`만 다음 AI 생성/cleanup 작업의 입력으로 사용한다.

## Current Priority

- `R_upper_lash`: 머리카락 섞임으로 재생성 우선.
- `mouth_inner`: bbox 여유 부족과 선 잘림으로 cleanup 우선.
