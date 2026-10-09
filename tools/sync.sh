#!/usr/bin/env bash
# 원본 www.pactivekorea.com 에서 정적 사본을 다시 내려받고 GitHub에 반영합니다.
# 사용: bash tools/sync.sh
set -euo pipefail
cd "$(dirname "$0")/.."

if ! python3 -c "import requests" 2>/dev/null; then
  echo "[1/4] requests 패키지 설치"
  python3 -m pip install -q requests
fi

echo "[2/4] 원본 사이트 미러링 (약 2~3분 소요)"
python3 tools/mirror.py

echo "[3/4] 변경 사항 커밋"
git add -A
if git diff --cached --quiet; then
  echo "  변경된 내용이 없습니다."
else
  git commit -m "사이트 갱신: $(date +%Y-%m-%d)"
fi

echo "[4/4] push"
git push
echo "완료. GitHub Pages 반영까지 1~2분 걸립니다."