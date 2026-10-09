#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pactivekorea.com -> GitHub Pages(정적 사이트) 미러링 v2
원본 사이트의 상대/절대 링크를 정확히 해석한 뒤,
GitHub Pages 프로젝트 저장소에서도 동작하는 상대경로로 다시 쓴다.
"""
import os, re, html, time, urllib.parse, threading, shutil
from concurrent.futures import ThreadPoolExecutor
import requests, urllib3
urllib3.disable_warnings()

BASE = "http://www.pactivekorea.com"
OUT = os.environ.get("OUT_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.isdir(OUT):
    # 저장소 메타 파일(.git, tools, README 등)은 남기고 사이트 결과물만 지운다
    KEEP = {".git", "tools", "README.md", ".gitignore", ".gitattributes"}
    for entry in os.listdir(OUT):
        if entry in KEEP:
            continue
        p = os.path.join(OUT, entry)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
os.makedirs(OUT, exist_ok=True)

sess = requests.Session()
sess.verify = False
sess.headers.update({"User-Agent": "Mozilla/5.0 (compatible; site-mirror/2.0)"})
_lock = threading.Lock()
_log = []

def get(url, binary=False, tries=3):
    for i in range(tries):
        try:
            r = sess.get(url, timeout=45)
            if r.status_code == 200:
                if binary:
                    return r.content
                # 원본 서버가 일부 페이지에 charset 을 보내지 않는다.
                # requests 의 자동 추정에 맡기면 한글이 깨지므로 직접 UTF-8 우선으로 디코딩한다.
                raw = r.content
                for enc in ("utf-8", "cp949", "euc-kr"):
                    try:
                        return raw.decode(enc)
                    except UnicodeDecodeError:
                        continue
                return raw.decode("utf-8", errors="replace")
            return None
        except Exception:
            time.sleep(1.2 * (i + 1))
    return None

BOARDS = {"sub401": "news", "sub402": "knowledge"}

def ko_out(u):
    """원본 사이트 경로 -> 정적 사이트 경로"""
    p = urllib.parse.urlparse(u).path
    if p in ("/", "/index.php"):
        return "index.html"
    p = p.lstrip("/")
    if p.endswith("/"):
        p += "index.html"
    if p.endswith(".php"):
        p = p[:-4] + ".html"
    return p

def board_out(u):
    qs = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
    t = qs.get("bo_table", [""])[0]
    d = BOARDS.get(t)
    if not d:
        return None
    wid = qs.get("wr_id", [""])[0]
    return "%s/%s.html" % (d, wid) if wid else "%s/index.html" % d

# ---------- 1. 수집 대상 ----------
targets = []  # (원본 URL, 출력경로, 원본 디렉터리)
for u in ["/"] + ["/sub%d.php" % i for i in range(101, 103)] + \
         ["/sub%d.php" % i for i in range(201, 203)] + \
         ["/sub%d.php" % i for i in range(301, 324)]:
    targets.append((u, ko_out(u), "/"))
for u in ["/en/"] + ["/en/sub%d.php" % i for i in range(300, 325)]:
    targets.append((u, ko_out(u), "/en/"))
for t in BOARDS:
    u = "/gnuboard5/bbs/board.php?bo_table=" + t
    targets.append((u, board_out(u), "/gnuboard5/bbs/"))

pages = {}     # outpath -> (html, src_url)
page_src = {}  # outpath -> 원본 디렉터리

def fetch_page(url, outpath, srcdir):
    h = get(BASE + urllib.parse.quote(url, safe="/?=&%"))
    if h and len(h) > 500:
        with _lock:
            pages[outpath] = h
            page_src[outpath] = srcdir
            _log.append("PAGE %-30s -> %s (%d)" % (url, outpath, len(h)))

with ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(lambda a: fetch_page(*a), targets))

# 게시글
posts = []
for t, d in BOARDS.items():
    lp = d + "/index.html"
    if lp not in pages:
        continue
    for i in sorted({int(x) for x in re.findall(r"wr_id=(\d+)", pages[lp])}):
        posts.append(("/gnuboard5/bbs/board.php?bo_table=%s&wr_id=%d" % (t, i),
                      "%s/%d.html" % (d, i), "/gnuboard5/bbs/"))
z = [(u, o, s) for (u, o, s) in targets if o in pages]
with ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(lambda a: fetch_page(*a), posts))

# ---------- 2. 리소스 수집 ----------
def resolve(ref, srcdir):
    """원본 페이지 기준으로 사이트 내부 절대경로 계산 (루트 밖으로 나가지 않게 클램프)"""
    ref = html.unescape(ref).strip()
    if ref.startswith(("#", "javascript:", "mailto:", "data:")):
        return None
    if ref.startswith(("http://", "https://")):
        if "pactivekorea.com" not in ref:
            return None
        ref = urllib.parse.urlparse(ref).path + (
            ("?" + urllib.parse.urlparse(ref).query) if urllib.parse.urlparse(ref).query else "")
    if ref.startswith(("/", "#", "javascript:", "mailto:", "data:")):
        path = ref
    else:
        path = os.path.join(srcdir, ref)
    path = path.split("#")[0]
    path, _, query = path.partition("?")
    parts = []
    for seg in path.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if parts:
                parts.pop()
            continue
        parts.append(seg)
    out = "/" + "/".join(parts)
    return out + (("?" + query) if query else "")

assets = set()
for outpath, h in pages.items():
    srcdir = page_src[outpath]
    for m in re.findall(r'(?:href|src)=["\']([^"\']+)["\']', h):
        if m.endswith("/"):
            continue
        p = resolve(m, srcdir)
        if p:
            p = p.split("?")[0]
        if p and not p.endswith(".php") and p not in ("/", "/en"):
            assets.add(p)
for css in ["/style.css", "/en/style.css"]:
    c = get(BASE + css)
    if c:
        cdir = os.path.dirname(css) + "/"
        for m in re.findall(r'url\((["\']?)([^)"\']+)\1\)', c):
            p = resolve(m[1], cdir)
            if p:
                assets.add(p.split("?")[0])

print("assets:", len(assets))

def fetch_asset(p):
    dest = os.path.join(OUT, p.lstrip("/"))
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    data = get(BASE + urllib.parse.quote(p), binary=True)
    if not data:
        with _lock: _log.append("MISS asset %s" % p)
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(data)

with ThreadPoolExecutor(max_workers=8) as ex:
    list(ex.map(fetch_asset, sorted(assets)))

# 원본에서 EUC-KR 로 내려오는 JS/CSS 는 UTF-8 로 변환해 둔다(주석 한글 깨짐 방지)
for root, _dirs, files in os.walk(OUT):
    if ".git" in root:
        continue
    for fn in files:
        if not fn.endswith((".js", ".css")):
            continue
        p = os.path.join(root, fn)
        raw = open(p, "rb").read()
        try:
            raw.decode("utf-8")
            continue
        except UnicodeDecodeError:
            pass
        for enc in ("cp949", "euc-kr"):
            try:
                open(p, "w", encoding="utf-8").write(raw.decode(enc))
                _log.append("ENCODING %s (%s -> utf-8)" % (fn, enc))
                break
            except UnicodeDecodeError:
                continue

# ---------- 3. 링크 재작성 ----------
def map_url(u, srcdir, depth):
    u = html.unescape(u).strip()
    if u.startswith(("#", "javascript:", "mailto:", "data:")):
        return u
    if u.startswith(("http://", "https://")) and "pactivekorea.com" not in u:
        return u
    p = resolve(u, srcdir)
    if not p:
        return u
    path, _, q = p.partition("?")
    if path.startswith("/gnuboard5/bbs/board.php"):
        tgt = board_out(p)
        if not tgt:
            return "#"
    elif path.startswith("/gnuboard5/bbs/download.php"):
        qs = urllib.parse.parse_qs(q)
        if "wr_id" not in qs or "bo_table" not in qs:
            return BASE + path + (("?" + q) if q else "")
        tgt = "downloads/%s_%s.bin" % (qs["bo_table"][0], qs["wr_id"][0])
    elif path.startswith("/gnuboard5/bbs/view_image.php"):
        qs = urllib.parse.parse_qs(q)
        fn = qs.get("fn", [""])[0]
        if not fn:
            return BASE + path + (("?" + q) if q else "")
        tgt = "media/%s/%s" % (qs.get("bo_table", ["etc"])[0], fn)
    elif path.startswith(("/gnuboard5/bbs/link.php", "/gnuboard5/bbs/popup.php")):
        # 외부 링크/팝업은 원본 서버 페이지로 연결 (정적 사본 미생성)
        return BASE + path + (("?" + q) if q else "")
    elif path.endswith(".php"):
        tgt = ko_out(path)
    elif path in ("/", ""):
        tgt = "index.html"
    else:
        tgt = path.lstrip("/")
    return ("../" * depth) + tgt

def rewrite(h, outpath):
    depth = outpath.count("/")
    srcdir = page_src[outpath]
    en = outpath.startswith("en/")

    def js_menu(m):
        code = m.group(1)
        if code in BOARDS.values() or code in ("401", "402"):
            return 'href="%s"' % map_url("/gnuboard5/bbs/board.php?bo_table=sub%s" % code, "/", depth)
        u = "/%ssub%s.php" % ("en/" if en else "", code)
        if en and ko_out(u) not in pages:
            u = "/sub%s.php" % code
        return 'href="%s"' % map_url(u, "/", depth)

    def fix(m):
        attr, q, val = m.group(1), m.group(2), m.group(3)
        if val.startswith(("javascript:", "data:", "mailto:", "#")):
            return m.group(0)
        return '%s=%s%s%s' % (attr, q, map_url(val, srcdir, depth), q)
    # 1) 일반 href/src 먼저 변환 (javascript: 링크는 건드리지 않는다)
    h = re.sub(r'(href|src)=(["\'])([^"\']+)\2', fix, h)
    # 2) 그 다음 javascript 메뉴 링크를 실제 정적 링크로 치환 (이중 변환 방지)
    h = re.sub(r'href="javascript:mainmenu\(\'(\d+)\'\)"', js_menu, h)
    return h.replace('href="javascript:main()"',
                     'href="%s"' % ("../" * depth + "index.html"))

for outpath, h in pages.items():
    dest = os.path.join(OUT, outpath)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "w", encoding="utf-8").write(rewrite(h, outpath))

# ---------- 4. CSS 재작성 ----------
for css, depth in [("style.css", 0), ("en/style.css", 1),
                   ("gnuboard5/skin/board/notice/style.css", 3),
                   ("gnuboard5/css/default.css", 2)]:
    p = os.path.join(OUT, css)
    if not os.path.exists(p):
        continue
    c = open(p, encoding="utf-8", errors="replace").read()
    cdir = "/" + os.path.dirname(css) + "/"
    def css_fix(m):
        q, u = m.group(1), m.group(2)
        if u.startswith(("http", "data:")):
            return m.group(0)
        return "url(%s%s%s)" % (q, map_url(u, cdir, depth), q)
    open(p, "w", encoding="utf-8").write(re.sub(r'url\((["\']?)([^)"\']+)\1\)', css_fix, c))

# ---------- 5. 첨부파일 ----------
att_urls = {}
for outpath in list(pages):
    for m in re.findall(r'(?:href|src)=["\']([^"\']*download\.php[^"\']*)["\']', pages[outpath]):
        u = html.unescape(m)
        q = urllib.parse.urlparse(u).query
        qs = urllib.parse.parse_qs(q)
        if "wr_id" not in qs or "bo_table" not in qs:
            continue
        att_urls["/gnuboard5/bbs/download.php?" + q] = qs

renames = {}
for url, qs in att_urls.items():
    r = sess.get(BASE + url, timeout=90)
    if r.status_code != 200 or not r.content:
        continue
    name = "downloads/%s_%s.bin" % (qs["bo_table"][0], qs["wr_id"][0])
    dest = os.path.join(OUT, name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(r.content)
    cd = r.headers.get("Content-Disposition", "")
    newname = name
    m2 = re.search(r'filename\*?=(?:UTF-8\'\')?"?([^";]+)"?', cd)
    if m2:
        raw = m2.group(1)
        try:
            orig = raw.encode("latin1").decode("cp949")
        except Exception:
            orig = raw
        ext = os.path.splitext(orig.strip())[1].lower()
        if ext and 1 < len(ext) <= 6:
            newname = name[:-4] + ext
    if newname != name:
        os.rename(dest, os.path.join(OUT, newname))
        renames[name.split("/")[-1]] = newname.split("/")[-1]
    _log.append("ATTACH %s -> %s (%d bytes) cd=%s" % (name, newname, len(r.content), cd))

# 확장자 변경분을 HTML/CSS 안의 링크에 반영
if renames:
    for root, _, files in os.walk(OUT):
        for fn in files:
            if not fn.endswith((".html", ".css", ".js")):
                continue
            p = os.path.join(root, fn)
            c = open(p, encoding="utf-8", errors="replace").read()
            o = c
            for a, b in renames.items():
                c = c.replace(a, b)
            if c != o:
                open(p, "w", encoding="utf-8").write(c)

# ---------- 6. 게시글 이미지 미러링 ----------
vjobs = {}
for outpath, h in pages.items():
    for m in re.findall(r'(?:href|src)=["\']([^"\']*view_image\.php[^"\']*)["\']', h):
        u = html.unescape(m)
        if "/gnuboard5/data/file/" in u:
            continue
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(u).query)
        fn = qs.get("fn", [""])[0]
        t = qs.get("bo_table", ["etc"])[0]
        if fn:
            vjobs["media/%s/%s" % (t, fn)] = "/gnuboard5/data/file/%s/%s" % (t, fn)

def fetch_media(item):
    dest_rel, src = item
    dest = os.path.join(OUT, dest_rel)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    data = get(BASE + urllib.parse.quote(src), binary=True)
    if not data:
        with _lock: _log.append("MISS media %s" % src)
        return
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(data)
    with _lock: _log.append("MEDIA %s (%d)" % (dest_rel, len(data)))

with ThreadPoolExecutor(max_workers=4) as ex:
    list(ex.map(fetch_media, sorted(vjobs.items())))

# 원본에서 404 인 off.png 자리표시자(투명 1x1) 생성
PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000a49444154789c6360000002000100ffff03000006"
    "0005574bd1f00000000049454e44ae426082")
for p in ("img/off.png", "en/img/off.png"):
    d = os.path.join(OUT, p)
    if not os.path.exists(d):
        os.makedirs(os.path.dirname(d), exist_ok=True)
        open(d, "wb").write(PNG_1PX)
        _log.append("PLACEHOLDER %s" % p)

# ---------- 7. 마무리 정리 ----------
# (1) gnuboard JS 전역변수의 http 절대주소 -> https (HTTPS 전환 시 혼합콘텐츠 방지)
# (2) link.php(외부 관련링크) 를 최종 목적지 URL 로 치환
link_map = {}
for outpath, h in pages.items():
    for m in re.findall(r'(?:href|src)=["\']([^"\']*link\.php[^"\']*)["\']', h):
        u = html.unescape(m)
        if "pactivekorea.com" not in u:
            continue
        path = urllib.parse.urlparse(u).path
        query = urllib.parse.urlparse(u).query
        try:
            rr = sess.get(BASE + path + "?" + query, allow_redirects=False, timeout=30)
            loc = rr.headers.get("Location")
            if loc:
                link_map[path + "?" + query] = loc
                _log.append("LINK %s -> %s" % (path + "?" + query, loc))
        except Exception:
            pass

for root, _dirs, files in os.walk(OUT):
    if ".git" in root:
        continue
    for fn in files:
        if not fn.endswith((".html", ".js", ".css")):
            continue
        p = os.path.join(root, fn)
        c = open(p, encoding="utf-8", errors="replace").read()
        o = c
        c = c.replace("http://www.pactivekorea.com/gnuboard5",
                      "https://www.pactivekorea.com/gnuboard5")
        for a, b in link_map.items():
            c = re.sub(r'https?://www\.pactivekorea\.com' + re.escape(a), b, c)
        if c != o:
            open(p, "w", encoding="utf-8").write(c)

open(os.path.join(OUT, ".nojekyll"), "w").write("")
print("\n".join(_log))
print("=== DONE:", OUT)
