# HANDOFF — 대만 클라이언트 NFC 안내 페이지 (tw-nfc-guide)

갱신일: 2026-09-11 · 담당: Claude Code (이전: Cowork 세션 → 원본 소스 유실, 본 세션에서 스펙대로 재구축)

## 1. 한 줄 요약
대만 클라이언트 4곳에 배포할 NFC 카드용 모바일 웹페이지. 카드를 태그하면 짧은 https 주소가 열리고,
그 페이지에서 구글맵 길찾기(호텔은 주변 맛집·명소, 문화관·대학은 오시는 길)로 연결된다.
언어는 번체중문 / 영어 / 한국어 3개, 상단 버튼으로 전환.

## 2. 설계 원칙 (이전 세션 결정 유지)
- NTAG213(144B)에는 긴 URL이 안 들어가고, 아이폰은 `https://`만 백그라운드 인식 → **태그에는 짧은 https 주소 하나만**, 내용은 웹페이지가 담당.
- 지도는 구글맵(대만). 링크는 좌표가 아니라 **장소명+주소(중문) 텍스트 쿼리**:
  - 정보: `https://www.google.com/maps/search/?api=1&query=<장소명 주소>`
  - 길찾기: `https://www.google.com/maps/dir/?api=1&destination=<장소명 주소>&origin=<출발지>&travelmode=walking|driving|transit`
  - 언어 버튼을 바꿔도 쿼리는 항상 중문(zh)으로 만든다 → 대만 구글맵 매칭이 가장 정확.
- 데이터(data.json)와 렌더러(app.js) 분리 → 내용 수정 시 태그 재기록 불필요.
- 좌표(lat/lng)는 **거리·시간 추정에만** 사용(직선거리×1.35, 도보 75 m/min, 시내 28 km/h). 페이지에 "추정치" 문구 표시.

## 3. 클라이언트 4곳
| slug | 클라이언트 | 카드 내용 | 비고 |
|---|---|---|---|
| lin | The Lin Hotel 林酒店 (台中市西屯區朝富路99號) | 맛집 6 · 명소 6 | Taichung Hotel Association |
| comin | 康茵行旅 Comin' Place (台中市烏日區大同九街73號) | 맛집 6 · 명소 5 | 高鐵台中역 약 1 km |
| miso | 台灣味噌釀造文化館 / 味榮食品 (台中市**豐原區**西勢路701號) | 오시는 길 4(豐原역·高鐵·台中역·국도1호) + 개관·예약·연락처 표 | ⚠ 烏日 아님. 페이지에 경고 박스 있음 |
| ncnu | 國立暨南國際大學 觀光休閒與餐旅管理學系 (南投縣埔里鎮大學路1號, 管理學院 338室) | 오시는 길 4(高鐵→6670, 시내→6670, 국도6호 愛蘭IC, 埔里轉運站) + 학과 연락처 + 명소 6 | 자동차 목적지는 管理學院(大學路470號) |

## 4. 저장소 구조
```
tw-nfc/
├─ data3.py        ← ★ 모든 콘텐츠(3개 언어) 정의. 실행하면 dist/data.json 생성
├─ dist/           ← 배포 디렉터리 (정적, 빌드 불필요)
│  ├─ index.html   (4개 페이지 링크 목록, 테스트용)
│  ├─ lin.html / comin.html / miso.html / ncnu.html  (껍데기: <body data-slug="..."><script src="app.js">)
│  ├─ app.js       (data.json fetch → 언어 선택 → DOM 렌더. ?lang=ko|en|zh > localStorage 'lang' > navigator.language > zh)
│  ├─ style.css    (모바일 1열, 라이트/다크 자동)
│  ├─ data.json    (data3.py 산출물, 커밋함)
│  └─ vercel.json  {"cleanUrls":true,"trailingSlash":false}
└─ HANDOFF.md
```
- 경로는 전부 **상대경로**(`app.js`, `data.json`)라 Vercel 루트에 올려도, GitHub Pages 하위 폴더에 두어도 동작.

## 5. data3.py 데이터 규약
- 텍스트 필드는 전부 `T(zh, en, ko)` → `{"zh","en","ko"}` dict. app.js `t()`가 현재 언어로 꺼내고 없으면 zh로 폴백.
- 아이템 종류
  - `poi(name, address, desc, lat, lng, tag, hours, origin=클라이언트, walk=True, drive_min=…)` — 장소 카드. 버튼: 상세 정보 / 도보(3 km 이내) / 자동차.
  - `route(name, frm=출발지, desc, steps=[T…], modes=["transit","driving"], dest=목적지, km, drive_min)` — 교통 카드. 버튼: 대중교통 / 택시·자동차. 목적지는 `dest` > 페이지 `dest` > `origin`.
  - `tip(title, text)` — 노란 안내 박스. `info([(k, v, href), …])` — key/value 표(전화는 `tel:`, 링크는 https).
- 페이지: `PAGES[slug] = {client, origin, dest?, kicker?, title, subtitle?, sections:[section(title, items)], footer?}`
- 클라이언트 배너: `place(..., logo=URL, hero=URL, hero_credit=…, theme="#hex")`. 헤더 아래에 대표사진(hero) + 로고 카드가 뜬다.
  hero가 없으면 theme 색 그라데이션 배너. 이미지 로드 실패 시 자동으로 텍스트 이름으로 대체(onerror).
  현재 로고 4개는 클라이언트 사이트 **핫링크**(§8 URL) → 사이트가 바뀌면 깨질 수 있으니 확정 후 `dist/img/`에 로컬 복사 권장.
- 사진: `poi(..., photo=URL 또는 "img/xxx.jpg", credit="…", emoji="🧋")`. 없으면 태그 기반 이모지 플레이스홀더.
  명소 16곳은 위키미디어 공용 `commons("파일명")` 썸네일(작가/라이선스는 파일 페이지에서 확인 필요, 웹 표시 시 credit 표기됨).
  식당 6+6곳은 해당 매장 자유이용 사진이 없어 이모지 → 클라이언트에 사진 요청해서 `dist/img/`에 넣고 photo= 연결.
- 지도: Leaflet 1.9.4(`dist/vendor/`) + CARTO Voyager 타일(OSM 기반, 키 불필요). 클라이언트=검정 핀, POI=번호 핀(카드 번호와 일치), 출발역=회색 핀.
  핀 팝업의 정보/길찾기 버튼은 구글맵 링크. 구글 지도 타일을 쓰려면 Maps JavaScript API 키가 필요해 채택 안 함.

## 6. 빌드·미리보기·배포
```bash
cd tw-nfc && python3 data3.py               # dist/data.json 재생성
cd dist && python3 -m http.server 8765      # http://localhost:8765/lin.html?lang=ko
```
- file:// 로는 안 됨(fetch). 반드시 http 서버.
- **GitHub Pages(이 레포)**: main에 머지되면 `https://wacandacat.github.io/slbs_IP18plan/tw-nfc/dist/lin.html` 로 바로 공개됨(보호 없음). 상황실 허브 index.html에도 카드 추가함.
- **Vercel(권장, 짧은 주소)**: `cd tw-nfc/dist && vercel --prod` (프레임워크 Other, 빌드 없음). 새 프로젝트는 Deployment Protection이 기본 ON → Settings → Deployment Protection → Vercel Authentication OFF 필수.
  Cowork/MCP의 Vercel 토큰으로는 이전 프로젝트(tw-nfc-guide, nfc-guide-tw)가 조회되지 않음(프로젝트 목록 빈 배열). CLI로 한 프로젝트에 고정 권장.
- NFC Tools 앱: 기록 추가 → URL → `https://` + `<도메인>/lin` (Vercel cleanUrls) 또는 `…/tw-nfc/dist/lin.html` (Pages).

## 7. 콘텐츠 검증 상태 (인쇄 전 확인 필요)
샌드박스에서 구글맵·대만 공식 사이트 직접 접속이 차단되어 **검색 스니펫 기반**으로 작성함. 주소·전화·영업시간은 복수 출처 교차확인했으나 아래는 꼭 재확인:
- 味噌文化館: 휴관일(공식 "매일" vs 일부 사이트 "월요일 휴관"), 최종입장 16:00, DIY 회차. 921번 버스 정류장명 "台灣味噌文化館"은 확실.
- 暨大: 학과 사무실 338室은 클라이언트 제공값 그대로(검색상 341室 언급 있음). 6670 고속철→暨大 요금, 캠퍼스 진입 노선(6670B/E/F) 확인. 管理學院 大學路470號는 EMBA 주소 스니펫 기반.
- 康茵行旅: 烏日 식당 3곳(老先覺·這隻雞·拾捌號) 좌표 ±300 m 추정. 烏日啤酒廠은 공장 견학 중단 중(제품센터만 개방). 烏日夜市는 2023년 폐업, 臺中國際展覽館은 2026-06 철거 → 둘 다 미기재.
- 林酒店: 春水堂朝富店 등 7곳 좌표는 주소 기반 추정(±200 m). 屋馬中港店은 2025-02 재개장 확인.
- 도보/차량 시간 전부 추정치. 링크는 텍스트 쿼리라 좌표 오차가 길찾기에 영향 없음.

## 8. 로고 / 캐릭터 자료 (다운로드는 사용자 브라우저에서)
- 暨南大學 공식 CI(AI): https://service.ncnu.edu.tw/ncnuweb/units/share/%E5%85%A8%E6%A0%A1%E5%85%B1%E7%94%A8/web_material/images/logo/ps/NCNU_logo%E5%9C%96%E8%88%87%E5%BA%95%E6%96%87%E5%AD%97.ai
- 觀餐系 엠블럼 PNG: https://www.tourism.ncnu.edu.tw/wp-content/uploads/2021/03/footer_logo-1.png · 가로형: …/web_logo_v2.png
- The Lin Hotel PNG: https://static.wixstatic.com/media/0b7d63_163fc4ed42a548ef97e7262b6d6c356a~mv2.png
- 味榮食品 로고: https://www.sauceco.com.tw/theme-b67/images/logo.png , logo2.png (흰색: footer-logo.png, logo2-footer.png)
- 康茵行旅 (저해상): https://comingplace.com/wp-content/uploads/2019/12/中英文LOGO（灰）.png
- 벡터 없는 3곳(린호텔·味榮·康茵)은 클라이언트에 AI 파일 요청. 이주홍님 방향은 "캐릭터 말고 로고".

## 9. 남은 일
0. 사진·로고 URL이 실제로 뜨는지 배포 페이지에서 확인(샌드박스에선 외부 이미지 차단이라 미검증). 깨진 건 이모지/텍스트로 폴백됨.
1. 대니님 국문 검수 → data3.py 수정 → `python3 data3.py` → 커밋(Pages 자동) 또는 `vercel --prod`.
2. §7 항목 구글맵/전화로 재확인.
3. 최종 주소 확정(커스텀 도메인 검토) → NFC 태그 기록.
4. (선택) 로고 이미지 `dist/logo/`에 넣고 `place(..., logo=...)` 연결.

## 10. 함정 메모
- 이 샌드박스는 `*.vercel.app`, `*.github.io`, 구글맵, 대만 공식 사이트 아웃바운드가 막혀 있음 → 배포 결과는 로컬 http 서버 + Playwright로만 검증했음.
- Vercel MCP: 프로젝트 조회/재배포/보호설정 변경 불가 → CLI 사용.
