# SLBS 아이폰18 상황실 — 정적 사이트 배포 인수인계

## 목표
이 폴더의 정적 HTML들을 **한 URL**로 호스팅한다(팀 공유용 내부 대시보드 허브).

## 폴더 구성 (전부 정적 HTML, 빌드 불필요)
- `index.html` — 허브(랜딩). 아래 페이지들을 **상대경로**로 링크. 운영 카드는 외부 런치스케줄로 링크.
- `prsm-board.html` — PRSM 성과 콘텐츠 보드(반응×성과 산점도·사분면·KV 근거표)
- `mono-board.html` — 모노클리어 IP 성과 보드
- `soza-master.html` — 소재 통합본(브리프+PRSM/모노 보드, iframe 탭)
- `concept.html` — Prism Moment 컨셉 디렉션 v3
- `references.html` — 실사 레퍼런스 보드(v2, 검정배경 pre-filtered)
- `basetone.html` — 베이스톤 SVG 도식
- `brief.html` — 소재 브리프
- `concept-ref.html` — 컨셉+레퍼런스+베이스톤 통합본(iframe 탭)

## 이미지: 이미 호스팅됨 — 손댈 것 없음
모든 보드/컨셉 이미지는 **Supabase Storage 공개 버킷에 이미 올라가 있고, HTML에 절대 URL로 박혀 있다.**
- 버킷 공개 URL 형식: `https://yhbduxezupwfmcemuokt.supabase.co/storage/v1/object/public/board-img/bN.jpg|png`
- 따라서 **어디에 호스팅하든 이미지가 그대로 로드된다.** 이미지 파일을 같이 올릴 필요 없음.
- (참고) brief.html의 예시 이미지 몇 개는 facebook.com/ads/image 영구 permalink를 쓴다. 만료되면 교체 필요할 수 있으나 나머지는 Storage라 안전.

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

## 왜 클라우드 세션에서 못 끝냈나 (참고)
- 이 클라우드 세션 샌드박스는 **git 프록시**가 있어 세션에 인가되지 않은 GitHub 레포로의 push를 차단함(`slbs_IP18plan` 미인가).
- MCP Vercel 배포 도구는 **호출당 ~26KB 인라인 용량 한계**가 있어, 60KB+ 보드/243KB 통합본을 한 번에 못 올림.
- 로컬 Claude Code는 두 제약이 모두 없음 → 위 A/B 그대로 하면 끝.

## 데이터 출처 / 맥락
- Supabase 프로젝트: `yhbduxezupwfmcemuokt` (slbs-d2c-dashboard). 이미지 버킷 `board-img`(public).
- 지표: 메타 소재 자기보고 + 자사몰 실판매 canonical(realtime_orders+sales_raw). 금액 판단은 자사몰 MER 기준.
- 내부 공유용.
