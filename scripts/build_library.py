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


def split_title(raw):
    """标题第一行作文本，其余 #话题 拆成 tags。"""
    raw = (raw or "").strip()
    lines = [l.strip() for l in raw.split("\n") if l.strip()]
    if not lines:
        return "未命名", []
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
    return (first or "未命名"), out[:4]


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
                thumb = os.path.join(tdir, "cover.webp")
                if HAS_PIL and not os.path.exists(thumb):
                    try:
                        with Image.open(poster) as im:
                            im = im.convert("RGB")
                            if im.width > THUMB_W:
                                im = im.resize((THUMB_W, round(im.height * THUMB_W / im.width)), Image.LANCZOS)
                            im.save(thumb, "WEBP", quality=THUMB_Q, method=4)
                    except Exception as e:
                        print(f"  ! cover thumb fail {thumb}: {e}", file=sys.stderr)
                if os.path.exists(thumb):
                    item["coverThumb"] = f"thumbs/{hh}/cover.webp"
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
            item["images"].append({
                "src": f"thumbs/{hh}/{thumb_name}" if ok else urlpath(*(rel_parts + [f])),
                "full": urlpath(*(rel_parts + [f])),
                "live": urlpath(*(rel_parts + [im["live_video"]])) if im.get("live_video") else None,
                "w": im.get("width") or 0,
                "h": im.get("height") or 0,
            })
        if item["images"]:
            item["cover"] = item["images"][0]["src"]
            item["coverW"] = item["images"][0]["w"]
            item["coverH"] = item["images"][0]["h"]
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
    print(f"✓ {len(works)} 部作品（{imgs} 张图 / {vids} 条视频）→ data/library.js")
    print(f"  渠道分布: " + " / ".join(f"{k} {v}" for k, v in sorted(ch.items())))
    if merged:
        print(f"  双平台合并 {merged} 部（去重表 scripts/dupe_map.json）")
    if not HAS_PIL:
        print("! 没装 Pillow，缩略图跳过（画廊会直接用原图，慢一些）", file=sys.stderr)


if __name__ == "__main__":
    build()
