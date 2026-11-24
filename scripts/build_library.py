#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
扫描仓库里的作品文件夹（含 info.json），生成：
  data/library.js      —— 全站作品数据（首页画廊 + 详情页都读它）
  thumbs/<hash>/*.webp —— 缩略图（640px 宽，画廊用）
  thumbs/<hash>/poster.jpg —— 视频作品的封面帧

双渠道（2026-10-23 起，目录对称）：
  - 抖音源/ 各文件夹        → channel=抖音
  - 小红书源/ 各文件夹      → channel=小红书
  - scripts/dupe_map.json   → 双平台去重表：命中的小红书作品不单列，
    合并进抖音条目（channel=双平台，附 xhsLink 小红书原文链接）。
    表由 scripts/dedupe_xhs.py 生成（ahash 比对 + 全图重叠率判定）。

只依赖 Pillow（可选：有 ffmpeg 才能给视频抽封面）。
在 GitHub Actions 里也会跑一遍，所以新丢一个文件夹进去、push，就自动上线。
"""

import json
import os
import re
import sys
import hashlib
import datetime
import subprocess
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"assets", "data", "works", "scripts", "thumbs", "_dedupe_backup",
             "tools", "纪录片学习", "media", ".github"}
DY_DIR_NAME = "抖音源"
XHS_DIR_NAME = "小红书源"
DY_ROOT = os.path.join(ROOT, DY_DIR_NAME)
XHS_ROOT = os.path.join(ROOT, XHS_DIR_NAME)
DUPE_MAP = os.path.join(ROOT, "scripts", "dupe_map.json")
THUMB_W = 640
THUMB_Q = 74

# 置顶作品：画廊里排最前面，封面上带「置顶」标记（像抖音那样）。
# 数组顺序即置顶排序。换置顶就改这里。
PINNED_ORDER = [
    "7561409947121077514",   # 总有一天 · 冈仁波齐（视频）
    "7585371200881282358",   # 真正的西域 · 喀什（视频）
    "7458612718006799625",   # 小爬海（图文）
]

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

HAS_FFMPEG = subprocess.run(
    ["which", "ffmpeg"], capture_output=True
).returncode == 0


def h8(s):
    return hashlib.md5(s.encode("utf-8")).hexdigest()[:8]


def urlpath(*parts):
    """把（可能含中文、#、空格的）路径段逐段编码成 URL 安全路径。"""
    return "/".join(quote(p, safe="") for p in parts)


def clean_title(t):
    """把「未命名作品（2024-01-18）」这类兜底名当成空标题。
    这些作品确实没写文案，站点上就不显示标题，只留日期和张数。"""
    t = (t or "").strip()
    if not t:
        return ""
    if t in ("未命名", "无题"):
        return ""
    if re.fullmatch(r"未命名作品[（(][\d\-\s]+[）)]", t):
        return ""
    # 纯数字 / 纯 ID 串（≥6 位，没有中文和字母词）
    if re.fullmatch(r"[\d_\-\.]{6,}", t):
        return ""
    # 老作品的标题字段直接就是 aweme_id（十六进制那种，如 6291ca15000000021035b84）。
    # 特征是：一整串、没有空格和中文、长度 ≥12。真文案不会长这样。
    if " " not in t and not re.search(r"[\u4e00-\u9fff]", t) and re.fullmatch(r"[0-9a-zA-Z_\-]{12,}", t):
        return ""
    return t


def split_title(raw):
    """标题第一行作文本，其余 #话题 拆成 tags。"""
    raw = (raw or "").strip()
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    if not lines:
        return "", []
    first = lines[0]
    rest = " ".join(lines[1:])
    tags = re.findall(r"#([^\s#]+)", rest or "")
    # 第一行里也可能带话题
    inline = re.findall(r"#([^\s#]+)", first)
    if inline:
        first = re.sub(r"#[^\s#]+", "", first).strip(" ，。、")
        tags = inline + tags
    # 去重保序
    seen, out = set(), []
    for t in tags:
        t = t.strip(" ，。、")
        if t and t not in seen:
            seen.add(t)
            out.append(t)
    return clean_title(first), out[:4]


def trim_uniform_border(im, tol=6, max_frac=0.22, min_area=0.5):
    """找出图片四周「整条都是同一个纯色」的边，返回 (l, t, r, b) 像素。

    为什么要它：
    - 小红书导出的图会把 2:3 的照片左右垫白边凑成 3:4（32px / 640 宽），
      放到瀑布流里就是一条条白框，很难看；
    - 抖音竖版视频的封面自带上下黑边（有的是 227px），瓦片整个变成黑块。
    这两种边都是「填充物」，不是画面内容，裁掉才对。

    只认纯白（min≥236）和纯黑（max≤26），并且每边最多吃掉 max_frac，
    防止把正常留白的照片（比如白墙人像）裁坏。视频封面的黑边能到 28%，
    所以生成封面时单独把这个上限放宽。"""
    W, H = im.size
    px = im.load()
    stepx = max(1, W // 60)
    stepy = max(1, H // 60)
    xs = list(range(0, W, stepx))
    ys = list(range(0, H, stepy))

    def uniform_row(y):
        c0 = px[0, y]
        for x in xs:
            p = px[x, y]
            if max(abs(p[0] - c0[0]), abs(p[1] - c0[1]), abs(p[2] - c0[2])) > tol:
                return None
        return c0

    def uniform_col(x):
        c0 = px[x, 0]
        for y in ys:
            p = px[x, y]
            if max(abs(p[0] - c0[0]), abs(p[1] - c0[1]), abs(p[2] - c0[2])) > tol:
                return None
        return c0

    def filler(c):
        return c is not None and (min(c) >= 236 or max(c) <= 26)

    lim_y, lim_x = int(H * max_frac), int(W * max_frac)
    t = 0
    while t < lim_y and filler(uniform_row(t)):
        t += 1
    b = 0
    while b < lim_y and filler(uniform_row(H - 1 - b)):
        b += 1
    l = 0
    while l < lim_x and filler(uniform_col(l)):
        l += 1
    r = 0
    while r < lim_x and filler(uniform_col(W - 1 - r)):
        r += 1

    # 裁完至少得留这么多面积，否则宁可不动
    if (W - l - r) * (H - t - b) < W * H * min_area:
        return 0, 0, 0, 0
    return l, t, r, b


def make_cover(src, dst, max_w=THUMB_W):
    """生成瓦片用的封面缩略图：先裁掉四周的填充边，再缩到 640 宽。

    返回 (w, h) 裁完后的尺寸；失败返回 None。
    缩略图是派生文件，覆盖写没有风险，原图一概不动。
    视频封面的黑边可以很厚（见过上下各 28%），所以上限放到 0.34。"""
    if not HAS_PIL:
        return None
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            l, t, r, b = trim_uniform_border(im, max_frac=0.34, min_area=0.25)
            if max(l, t, r, b) >= 4:
                im = im.crop((l, t, im.width - r, im.height - b))
            if im.width > max_w:
                im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            im.save(dst, "WEBP", quality=THUMB_Q, method=4)
            return im.size
    except Exception as e:
        print(f"  ! cover fail {src}: {e}", file=sys.stderr)
        return None


def make_thumb(src, dst, max_w=THUMB_W):
    if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src):
        return True
    if not HAS_PIL:
        return False
    try:
        with Image.open(src) as im:
            im = im.convert("RGB")
            w, h = im.size
            if w > max_w:
                im = im.resize((max_w, round(h * max_w / w)), Image.LANCZOS)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            im.save(dst, "WEBP", quality=THUMB_Q, method=4)
        return True
    except Exception as e:
        print(f"  ! thumb fail {src}: {e}", file=sys.stderr)
        return False


def make_poster(video, dst):
    if os.path.exists(dst):
        return True
    if not HAS_FFMPEG:
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    for ss in ("1.2", "0.3"):
        r = subprocess.run(
            ["ffmpeg", "-y", "-ss", ss, "-i", video, "-frames:v", "1",
             "-vf", f"scale={THUMB_W}:-2", "-q:v", "3", dst],
            capture_output=True,
        )
        if r.returncode == 0 and os.path.exists(dst) and os.path.getsize(dst) > 0:
            return True
    return False


def load_dupe_map():
    """双平台去重表：{小红书文件夹: {douyin_dir, distance, ...}}"""
    try:
        return json.load(open(DUPE_MAP, encoding="utf-8"))
    except Exception:
        return {}


def write_dupe_gitignores(dupe):
    """给去重表里的小红书作品目录写一个 .gitignore：
    媒体与抖音源重复，只留本地，不进仓库（信息保留 info.json + 原文链接）。
    幂等，内容不变就不重写。"""
    written = 0
    for name in dupe:
        d = os.path.join(XHS_ROOT, name)
        if not os.path.isdir(d):
            continue
        gi = os.path.join(d, ".gitignore")
        body = (
            "# 与 抖音源/ 里的同一部作品重复（见 scripts/dupe_map.json）。\n"
            "# 媒体只在本地留档，不进仓库；保留 info.json 记录元数据和小红书原文链接。\n"
            "*\n"
            "!.gitignore\n"
            "!info.json\n"
        )
        try:
            if os.path.exists(gi) and open(gi, encoding="utf-8").read() == body:
                continue
            with open(gi, "w", encoding="utf-8") as f:
                f.write(body)
            written += 1
        except Exception as e:
            print(f"  ! 写 {gi} 失败: {e}", file=sys.stderr)
    if written:
        print(f"  已为 {written} 个双平台作品目录写入 .gitignore（媒体不进仓库）")


def scan_work(base, rel_parts, name, channel_default):
    """扫描一个作品文件夹，返回 library 条目；失败返回 None。

    base      绝对目录（含 info.json 和媒体）
    rel_parts 站点 URL 用的相对路径段（抖音为 ["抖音源", name]，
              小红书为 ["小红书源", name]）
    """
    info_p = os.path.join(base, "info.json")
    if not os.path.isdir(base) or not os.path.exists(info_p):
        return None
    try:
        j = json.load(open(info_p, encoding="utf-8"))
    except Exception as e:
        print(f"  ! bad json {name}: {e}", file=sys.stderr)
        return None

    channel = j.get("渠道") or channel_default
    title, tags = split_title(j.get("标题"))
    # 小红书的标签/正文在独立字段里（抖音是标题带 #话题）
    if not tags:
        tags = [str(t) for t in (j.get("标签") or [])][:4]
    date = (j.get("发布时间") or "").strip()
    kind = (j.get("媒体") or {}).get("kind") or ("video" if j.get("类型") == "视频" else "image")
    st = j.get("统计") or {}
    # 缩略图目录：按完整相对路径散列，两个渠道天然不撞
    hh = h8("/".join(rel_parts))
    tdir = os.path.join(ROOT, "thumbs", hh)

    item = {
        # 短 id：抖音用 aweme_id（纯数字、稳定），小红书用 note_id，否则短哈希
        "id": str(j.get("aweme_id") or j.get("note_id") or hh),
        "dir": name,
        "path": urlpath(*rel_parts),
        "title": title,
        "tags": tags,
        "date": date,
        "year": date[:4],
        "type": j.get("类型") or ("视频" if kind == "video" else "图文"),
        "kind": kind,
        "link": j.get("作品链接") or "",
        "channel": channel,
        "stats": {
            "digg": int(st.get("digg_count") or 0),
            "comment": int(st.get("comment_count") or 0),
            "collect": int(st.get("collect_count") or 0),
            "recommend": int(st.get("recommend_count") or 0),
            "share": int(st.get("share_count") or 0),
        },
        "images": [],
        "cover": None,
        "coverW": 0,
        "coverH": 0,
        # 裁掉填充边后的瓦片封面尺寸；没有裁剪时留空，前端回落到 coverW/H
        "thumbW": 0,
        "thumbH": 0,
        "video": None,
        "pin": None,
    }

    if kind == "video":
        vname = (j.get("媒体") or {}).get("video") or "video.mp4"
        # 有网页版（压过的 1080p）就用它，原画太大、GitHub 单文件上限 100MB
        if os.path.exists(os.path.join(base, "video_web.mp4")):
            vname = "video_web.mp4"
        if os.path.exists(os.path.join(base, vname)):
            item["video"] = urlpath(*(rel_parts + [vname]))
            poster = os.path.join(tdir, "poster.jpg")
            if make_poster(os.path.join(base, vname), poster):
                item["cover"] = f"thumbs/{hh}/poster.jpg"
                # 封面尺寸按图片实际宽高算——视频有横有竖，不能硬编码
                cw, ch = THUMB_W, round(THUMB_W * 9 / 16)
                if HAS_PIL:
                    try:
                        with Image.open(poster) as im:
                            cw, ch = im.size
                    except Exception:
                        pass
                item["coverW"], item["coverH"] = cw, ch
                # 瓦片缩略图：设计封面可能是全尺寸大图（1MB+），
                # 首页直接加载太狠。另存一张 640 宽 webp，瓦片用小的、详情页用大的。
                # 视频封面常自带上下黑边（竖版视频塞进 9:16 之外的比例），
                # 顺手在生成时裁掉，不然瓦片就是一整块黑。
                thumb = os.path.join(tdir, "cover.webp")
                size = make_cover(poster, thumb)
                if size:
                    item["coverThumb"] = f"thumbs/{hh}/cover.webp"
                    item["thumbW"], item["thumbH"] = size
                    # 详情页的封面也用裁过边这张——poster.jpg 上下带黑边，
                    # 直接铺进画框会是一大块黑。视频本身没动，播的时候按视频比例重算。
                    item["cover"] = item["coverThumb"]
            # 时长
            if HAS_FFMPEG:
                r = subprocess.run(
                    ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
                     "-of", "default=nw=1:nk=1", os.path.join(base, vname)],
                    capture_output=True, text=True,
                )
                try:
                    item["duration"] = int(float(r.stdout.strip()))
                except Exception:
                    pass
    else:
        imgs = (j.get("媒体") or {}).get("images") or []
        for k, im in enumerate(imgs, 1):
            f = im.get("file")
            if not f:
                continue
            src = os.path.join(base, f)
            if not os.path.exists(src):
                continue
            thumb_name = os.path.splitext(f)[0] + ".webp"
            thumb = os.path.join(tdir, thumb_name)
            ok = make_thumb(src, thumb)
            entry = {
                "src": f"thumbs/{hh}/{thumb_name}" if ok else urlpath(*(rel_parts + [f])),
                "full": urlpath(*(rel_parts + [f])),
                "live": urlpath(*(rel_parts + [im["live_video"]])) if im.get("live_video") else None,
                "w": im.get("width") or 0,
                "h": im.get("height") or 0,
            }
            # 记下图片自带的填充边（小红书导出的白边最常见），
            # 详情页据此把容器比例改成裁后的比例，白边就不会显示出来。
            if ok and HAS_PIL:
                try:
                    with Image.open(thumb) as _im:
                        _l, _t, _r, _b = trim_uniform_border(_im.convert("RGB"))
                    if max(_l, _t, _r, _b) >= 4:
                        _W, _H = _im.size
                        cl, ct = _l / _W, _t / _H
                        cr, cb = _r / _W, _b / _H
                        # 只在「左右对称 / 上下对称」时才裁：
                        # 前端用 object-fit:cover 是靠两边等量裁切来吃掉填充边的，
                        # 不对称的话会把有内容的一侧也切掉，宁可不动。
                        if abs(cl - cr) <= 0.02 and abs(ct - cb) <= 0.02:
                            entry["crop"] = [round(cl, 4), round(ct, 4), round(cr, 4), round(cb, 4)]
                except Exception:
                    pass
            item["images"].append(entry)
        if item["images"]:
            first = item["images"][0]
            item["cover"] = first["src"]
            item["coverW"] = first["w"]
            item["coverH"] = first["h"]
            # 首图如果自带白边（小红书 2:3 垫成 3:4 的常见情况），
            # 单独生成一张裁干净的瓦片封面。原图与详情页缩略图都不动，
            # 只在列表里用这张，避免瀑布流出现一排白框。
            src0 = os.path.join(base, (imgs[0].get("file") or "")) if imgs else ""
            if src0 and os.path.exists(src0):
                cover_thumb = os.path.join(tdir, "cover.webp")
                if HAS_PIL:
                    try:
                        with Image.open(src0) as _im:
                            _insets = trim_uniform_border(_im.convert("RGB"), max_frac=0.34, min_area=0.25)
                    except Exception:
                        _insets = (0, 0, 0, 0)
                    if max(_insets) >= 4:
                        size = make_cover(src0, cover_thumb)
                        if size:
                            item["coverThumb"] = f"thumbs/{hh}/cover.webp"
                            item["thumbW"], item["thumbH"] = size
        item["count"] = len(item["images"])

    # 置顶排序位（0,1,2…），非置顶保持 None
    if item["id"] in PINNED_ORDER:
        item["pin"] = PINNED_ORDER.index(item["id"])

    return item


def build():
    works = []
    author = {}
    dupe = load_dupe_map()
    write_dupe_gitignores(dupe)

    # ── 抖音源：抖音源/ 目录 ──
    if os.path.isdir(DY_ROOT):
        for name in sorted(os.listdir(DY_ROOT)):
            d = os.path.join(DY_ROOT, name)
            if not os.path.isdir(d):
                continue
            item = scan_work(d, [DY_DIR_NAME, name], name, "抖音")
            if not item:
                continue
            try:
                j = json.load(open(os.path.join(d, "info.json"), encoding="utf-8"))
                author = j.get("作者", {}) or author
            except Exception:
                pass
            works.append(item)

    # ── 小红书源：小红书源/ 目录 ──
    xhs_by_dir = {}
    if os.path.isdir(XHS_ROOT):
        for name in sorted(os.listdir(XHS_ROOT)):
            d = os.path.join(XHS_ROOT, name)
            if not os.path.isdir(d):
                continue
            item = scan_work(d, [XHS_DIR_NAME, name], name, "小红书")
            if not item:
                continue
            if name in dupe:
                # 双平台重复：暂存，合并进抖音条目，不单列
                xhs_by_dir[name] = item
            else:
                works.append(item)

    # ── 合并双平台作品 ──
    merged = 0
    for xname, xitem in xhs_by_dir.items():
        target = dupe.get(xname, {}).get("douyin_dir")
        for w in works:
            if w["dir"] == target:
                w["channel"] = "双平台"
                w["xhsLink"] = xitem["link"]
                merged += 1
                break
        else:
            # 去重表里的抖音目录没找到（可能改名了）——保险起见单列
            works.append(xitem)

    # 按发布时间倒序；同一天按标题稳定排序
    works.sort(key=lambda w: (w["date"] or "", w["title"]), reverse=True)

    payload = {
        "author": {
            "nickname": author.get("nickname", ""),
            "uid": author.get("unique_id", ""),
            "signature": (author.get("signature") or "").replace("\n", " / "),
            "count": author.get("aweme_count", 0),
        },
        "generated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "total": len(works),
        "works": works,
    }

    out = os.path.join(ROOT, "data", "library.js")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("/* 自动生成，请勿手改 —— 改完文件夹跑 `python3 scripts/build_library.py` */\n")
        f.write("window.LIBRARY = ")
        json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")

    imgs = sum(w.get("count", 0) for w in works)
    vids = sum(1 for w in works if w["kind"] == "video")
    ch = {}
    for w in works:
        ch[w.get("channel", "?")] = ch.get(w.get("channel", "?"), 0) + 1
    stamp_versions()
    print(f"✓ {len(works)} 部作品（{imgs} 张图 / {vids} 条视频）→ data/library.js")
    print(f"  渠道分布: " + " / ".join(f"{k} {v}" for k, v in sorted(ch.items())))
    if merged:
        print(f"  双平台合并 {merged} 部（去重表 scripts/dupe_map.json）")
    if not HAS_PIL:
        print("! 没装 Pillow，缩略图跳过（画廊会直接用原图，慢一些）", file=sys.stderr)


def stamp_versions():
    """给 HTML 里对脚本/样式的引用打上内容 hash。

    为什么要这个：GitHub Pages 对所有资源只给 max-age=600，而 sw.js 对
    /assets/ 和 /data/ 都是 cache-first（永不过期）。所以只要 URL 不变，
    改过的 app.js / work.js / site.css 就永远到不了老访客手上——表现为
    "改了跟没改一样"、"点进去说没有这部作品"。用内容 hash 当版本号：
    内容没变 URL 就不变（纯吃缓存，零请求），一改 hash 就变，自然失效。

    覆盖范围：data/*.js（作品数据）+ assets/*.js + assets/*.css。
    同时支持 src="..." 和 href="..." 两种引用。
    """
    import glob
    import hashlib
    import re

    # (所在目录, 文件名, 引用属性)
    targets = [
        ("data", "library.js", "src"),
        ("data", "works.js", "src"),
        ("assets", "app.js", "src"),
        ("assets", "work.js", "src"),
        ("assets", "guard.js", "src"),
        ("assets", "sw-register.js", "src"),
        ("assets", "site.css", "href"),
        ("assets", "letter.css", "href"),
    ]
    htmls = glob.glob(os.path.join(ROOT, "*.html"))
    htmls += glob.glob(os.path.join(ROOT, "works", "*", "index.html"))

    for sub, name, attr in targets:
        path = os.path.join(ROOT, sub, name)
        if not os.path.exists(path):
            continue
        with open(path, "rb") as f:
            raw = f.read()
        # generated 时间戳每次生成都变，但它不代表内容变化——算 hash 前剔掉，
        # 否则版本号每次都会变，缓存永远命中不了。
        raw = re.sub(rb'"generated":"[^"]*",?', b"", raw)
        h = hashlib.md5(raw).hexdigest()[:8]
        pat = re.compile(r'(' + attr + r'="[^"]*' + re.escape(name) + r')(\?v=[0-9a-zA-Z]+)?(")')
        for html in htmls:
            with open(html, encoding="utf-8") as f:
                t = f.read()
            new = pat.sub(lambda m: m.group(1) + "?v=" + h + m.group(3), t)
            if new != t:
                with open(html, "w", encoding="utf-8") as f:
                    f.write(new)



if __name__ == "__main__":
    build()
