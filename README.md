# pactivekorea.com 정적 사본 (GitHub Pages용)

`http://www.pactivekorea.com` 의 **전체 페이지·이미지·게시글 자료**를 내려받아
GitHub Pages에서 그대로 열리는 **정적 사이트(static site)** 로 변환한 저장소입니다.

- 원본: http://www.pactivekorea.com (PHP 기반, 그누보드5 게시판 포함)
- 변환: `.php` → `.html`, 메뉴의 `javascript:` 링크 → 실제 정적 링크, 루트 절대경로(`/img/..`) → 상대경로
- 용량: 약 103MB / 약 350개 파일

## 폴더 구조

```
/                     국문 사이트 (index.html, sub101.html ~ sub323.html)
/en/                  영문 사이트 (약 20개 페이지)
/img/, /en/img/       이미지
/news/                뉴스 게시판 (원본 gnuboard5 sub401) - index.html + 글번호.html
/knowledge/           지식커뮤니티 게시판 (원본 gnuboard5 sub402)
/media/               게시글 본문 이미지 (원본 크기)
/downloads/           게시글 첨부파일
/gnuboard5/           게시판 스킨 CSS/JS (원본 그대로, 상대경로로 수정)
/tools/               사이트를 다시 내려받는 스크립트 (mirror.py, sync.sh)
```

## 사용 방법

### 1) GitHub에 올리기

```bash
cd pactivekorea-github
git init
git add .
git commit -m "pactivekorea.com 정적 사본"
git branch -M main
git remote add origin https://github.com/<사용자명>/<저장소명>.git
git push -u origin main
```

### 2) GitHub Pages 켜기

저장소 → **Settings → Pages → Source: Deploy from a branch → Branch: main / (root)** → Save

- 주소: `https://<사용자명>.github.io/<저장소명>/`
- 반영까지 1~2분 정도 걸립니다.

### 3) (선택) 기존 도메인 연결

`Settings → Pages → Custom domain` 에 `www.pactivekorea.com` 입력 후 DNS에 아래 레코드 추가:

| 타입 | 이름 | 값 |
|---|---|---|
| CNAME | www | `<사용자명>.github.io` |
| A | @ | 185.199.108.153 / .109.153 / .110.153 / .111.153 |

## 다시 내려받기(갱신)

```bash
python3 tools/mirror.py
```

원본 사이트에 새 글이나 페이지가 추가되면 위 명령으로 전체를 다시 받아 덮어씁니다.

## 주의사항

- **게시판 동적 기능**(글쓰기, 검색, 로그인)은 정적 사본에서 동작하지 않습니다. 글 목록·본문 열람과 첨부파일 다운로드는 정상 동작합니다.
- GitHub는 **파일 1개당 100MB** 를 넘으면 push를 거부하고, 50MB 넘으면 경고합니다. 현재 가장 큰 파일은 `downloads/sub401_9.mp4` (약 29MB), `media/sub401/3695292269_*.jpg` (약 21MB) 로 제한 이내입니다.
- 이 사이트의 저작권은 **팩티브코리아**에 있습니다. 공개 저장소로 올릴 경우 검색엔진에 노출되므로, 비공개 저장소 + Pages 공개 여부를 먼저 결정하세요.
- 자세한 설명은 별도 안내 문서 `pactivekorea-github-가이드.md` 를 참고하세요.