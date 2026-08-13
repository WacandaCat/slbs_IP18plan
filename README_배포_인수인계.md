# SLBS 아이폰18 상황실 — 정적 사이트 배포 인수인계

## 목표
이 폴더의 정적 HTML들을 **한 URL**로 호스팅한다(팀 공유용 내부 대시보드 허브).

## 폴더 구성 (전부 정적 HTML, 빌드 불필요)
- `index.html` — 허브(랜딩). 아래 페이지들을 **상대경로**로 링크.
- `schedule.html` — 런치 스케줄(제품 출시 일정 계산기). 원본: `WacandaCat/slbs_schedule`의 `index.html`.
  - 원래 Vercel(`slbs-launch-schedule-danny37park.vercel.app`)에 따로 떠 있었으나 Deployment Protection 때문에
    외부에서 로그인 벽에 막혀서 이 사이트 안으로 흡수했다. 계산기 전용 단일 파일이라 API 호출 없음
    (외부 의존: cdn.jsdelivr.net Pretendard, fonts.googleapis.com JetBrains Mono — 폰트뿐).
  - 원본 레포가 갱신되면 `slbs_schedule/index.html`을 다시 복사해 `schedule.html`로 덮어쓰면 된다.
- `prsm-board.html` — PRSM 성과 콘텐츠 보드(반응×성과 산점도·사분면·KV 근거표)
- `mono-board.html` — 모노클리어 IP 성과 보드
- `soza-master.html` — 소재 통합본(브리프+PRSM/모노 보드, iframe 탭)
- `concept.html` — Prism Moment 컨셉 디렉션 v3
- `references.html` — 실사 레퍼런스 보드(v2, 검정배경 pre-filtered)
- `basetone.html` — 베이스톤 SVG 도식
- `brief.html` — 소재 브리프
- `concept-ref.html` — 컨셉+레퍼런스+베이스톤 통합본(iframe 탭)
- `kv-guide.html` — KV 디자인 요청 패키지(brief 확장). 디렉션/스토리보드 2탭, 각 탭은 `<iframe srcdoc>`로 인라인.

## 이미지: 이미 호스팅됨 — 손댈 것 없음
모든 보드/컨셉 이미지는 **Supabase Storage 공개 버킷에 이미 올라가 있고, HTML에 절대 URL로 박혀 있다.**
- 버킷 공개 URL 형식: `https://yhbduxezupwfmcemuokt.supabase.co/storage/v1/object/public/board-img/bN.jpg|png`
- 따라서 **어디에 호스팅하든 이미지가 그대로 로드된다.** 이미지 파일을 같이 올릴 필요 없음.
- (참고) brief.html의 예시 이미지 몇 개는 facebook.com/ads/image 영구 permalink를 쓴다. 만료되면 교체 필요할 수 있으나 나머지는 Storage라 안전.

## 현재 배포 상태 (완료)
- **라이브 URL: https://wacandacat.github.io/slbs_IP18plan/**
- 레포: `https://github.com/WacandaCat/slbs_IP18plan` (public), 파일은 **레포 루트**에 평면 배치.
- Pages 소스: **`gh-pages` 브랜치 / (root)**.
  - 워크플로 `GITHUB_TOKEN`으로는 Pages 사이트 *생성*이 막혀 있어(`Resource not accessible by integration`)
    `actions/configure-pages@v5`의 `enablement: true`가 실패했다. 대신 `gh-pages` 브랜치를 푸시하면
    GitHub이 Pages를 자동 활성화하는 경로를 사용했고, `pages build and deployment`가 성공했다.
- 갱신 방법: **`main`에 push**하면 `.github/workflows/pages.yml`이 `main` 트리를 `gh-pages`로 미러링 →
  GitHub 기본 Pages 빌드가 자동 배포. (수동으로 `gh-pages`에 직접 push해도 동일)
- Settings → Pages에서 소스를 `main` / `(root)`로 바꿔도 된다. 그 경우 미러링 워크플로는 지워도 무방.
- Jekyll 처리 방지를 위해 `.nojekyll`을 루트에 두었다(밑줄로 시작하는 파일/폴더 대비).

## 배포 방법 (택1)

### A. GitHub Pages (사용자가 원한 방식)
사용자 레포: `https://github.com/WacandaCat/slbs_IP18plan` (public)
```
cd <이 폴더>
git init && git add -A && git commit -m "SLBS iPhone18 상황실 허브"
git branch -M main
git remote add origin https://github.com/WacandaCat/slbs_IP18plan.git
git push -u origin main
```
그다음 GitHub → repo → Settings → Pages → Source: **Deploy from a branch** → Branch: `main` / `/ (root)` → Save.
1~2분 뒤 URL: `https://wacandacat.github.io/slbs_IP18plan/`
(gh CLI가 있으면: `gh api -X POST repos/WacandaCat/slbs_IP18plan/pages -f source[branch]=main -f source[path]=/` 로 Pages 활성화)

### B. Vercel (정적, 더 빠름)
```
cd <이 폴더>
vercel --prod    # 프레임워크 없음(Other), 빌드 커맨드 없음, 루트 그대로
```

## 이전 세션에서 못 끝냈던 이유 (해소됨, 기록용)
- 예전 클라우드 세션은 git 프록시가 `slbs_IP18plan` push를 차단했음 → 이번 세션은 이 레포가 인가되어 push 성공.
- MCP Vercel 배포 도구의 호출당 인라인 용량 한계는 그대로라, 243KB짜리 `soza-master.html` 때문에 Vercel MCP 경로는 여전히 비효율 → GitHub Pages로 배포함.
- 남은 제약: 이 샌드박스는 `*.github.io` 아웃바운드가 막혀 있어 배포된 페이지를 세션 안에서 직접 열어볼 수는 없다(빌드/배포 성공 여부는 Actions로 확인).

## KV 제작 가이드 편입 (v2)
- `kv-guide.html` 추가, 허브 `index.html`에 "KV 제작" 섹션 카드 추가.
- **이미지 주의**: `kv-guide.html`의 `<img>` 소스는 Supabase Storage 4개 + `facebook.com/ads/image/?d=...` 퍼머링크 **5개**가 섞여 있다.
  "GO — 이렇게 (검증된 KV)" 섹션의 예시 5컷이 아직 메타 퍼머링크다. 이건 만료될 수 있고 뷰어 환경에 따라 안 뜰 수 있으니,
  깨지면 해당 5컷을 Storage(`board-img` 버킷)에 올리고 URL을 갈아끼우면 된다. 나머지 페이지는 전부 Storage라 안전.

## 데이터 출처 / 맥락
- Supabase 프로젝트: `yhbduxezupwfmcemuokt` (slbs-d2c-dashboard). 이미지 버킷 `board-img`(public).
- 지표: 메타 소재 자기보고 + 자사몰 실판매 canonical(realtime_orders+sales_raw). 금액 판단은 자사몰 MER 기준.
- 내부 공유용.
