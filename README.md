# 사무자동화산업기사 교재 지원 페이지

공개 주소: https://sumilee-phd.github.io/OA/ · 저장소: https://github.com/sumilee-phd/OA

『2027 사무자동화산업기사』(이수미 지음, 1권 필기·2권 실기)의 교재 지원 페이지입니다. 교재에 인쇄되는 QR 코드가 이 주소를 가리키므로 쪽 주소를 바꾸지 않습니다.

| 쪽 | 주소 | 내용 |
|---|---|---|
| 홈 | `/` | 표지, 바로 가기, 원칙 |
| 실습 파일 | `/files/` | 2권 10~16장 실습 파일 45개와 전체 묶음 ZIP, 확인값(SHA-256 앞 8자리) |
| 정오표 | `/errata/` | 1권·2권·웹앱 정오 사항 |
| 자주 묻는 질문 | `/faq/` | 16문항, 답마다 근거 절 번호 |
| 영상 | `/videos/` | 장·절 단위 영상 목록 |
| 오류 제보 | `/report/` | 제보 양식으로 연결(GitHub 이슈 양식, 구글 폼으로 바꿀 수 있음) |

관련 웹앱: 필기 CBT https://sumilee-phd.github.io/OA-cbt/ · 실기 시뮬레이터 https://sumilee-phd.github.io/OA-sim/

## 고치는 법

- 정오 사항: `data/errata.json`의 `items`에 `{page, where, wrong, right, date}`를 추가합니다.
- 영상: `data/videos.json`의 `items`에 `{section, title, url, length}`를 추가합니다.
- FAQ: `data/faq.json`. 답은 교재 원고의 사실만 쓰고 `ref`에 근거 절을 적습니다.
- 제보 버튼 목적지: `data/config.json`의 `report_url`·`report_label`.

고친 뒤 작업장에서 다음을 실행하고 커밋·푸시합니다.

```
python tools/build_site.py
```

생성기는 작업장 `90_자산/실습파일/`의 파일을 `files/`로 복사하고, 2권 부록 `20_원고/2권/a2_파일목록.md`의 확인값과 대조합니다. 불일치가 있으면 종료 코드 1로 끝나므로, 실습 파일을 바꿨다면 부록을 먼저 다시 만듭니다(`90_자산/그림/appendix/make_appendix.py files`).

## 디자인과 글꼴

- 기준 문서: 작업장 `90_자산/웹앱_디자인기준_20261111.md`. 홈은 교재 표지(노랑·먹·원색 알약), 하위 쪽은 내지(버건디 절 번호·꼬리표 상자) 형식입니다.
- 글꼴: Pretendard(SIL OFL 1.1), jsDelivr 고정 버전 v1.3.9. 불러오지 못하면 맑은 고딕으로 표시합니다.

## 인쇄용 QR

`qr/qr_print_300dpi.png`는 교재 인쇄용 QR(오류 정정 M, 300dpi)입니다.
