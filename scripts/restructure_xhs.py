#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 xhs-dl 下载的 小红书源/小天才./{note,video}/ 重组成原仓库的作品结构：

  小红书源/<作品名>/
      ├── 1.webp 2.webp ...      # 图文：编号媒体（保持下载时的命名）
      ├── video.mp4              # 视频
      └── info.json              # 元数据（兼容抖音 info.json  schema，另加 渠道/note_id）

info.json 字段与抖音版对齐（标题/发布时间/作者/统计/类型/作品链接/媒体），
build_library.py 读的是同一套键；新增：
  "渠道": "小红书"      —— 数据来源
  "note_id": "..."     —— 小红书笔记 ID（24 位 hex）

用法：python3 scripts/restructure_xhs.py
重组完成后可安全删除 小红书源/小天才. 目录（脚本会提示）。
"""

import json
import os
import re
import shutil
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "小红书源", "小天才")
DST = os.path.join(ROOT, "小红书源")

# 主页核实过的作者信息（xhs-dl 的 md 只带昵称，这里补齐）
AUTHOR = {
    "nickname": "小天才.",
    "unique_id": "Xiaotiancaiylt",
    "signature": "166 45 / 自由模特",
}

MD_RE = re.compile(
    r"<!--\s*xhs-note:\s*(?P<note_id>\S+)\s*-->\s*\n#\s*(?P<title>.*?)\n\n"
    r"-\s*\*\*作者\*\*:\s*(?P<author>.*?)\n"
    r"-\s*\*\*发布时间\*\*:\s*(?P<time>.*?)\n"
    r"-\s*\*\*类型\*\*:\s*(?P<type>.*?)\n"
    r"-\s*\*\*点赞\*\*:\s*(?P<digg>\d+|-)\s*\|\s*\*\*收藏\*\*:\s*(?P<collect>\d+|-)\s*\|\s*\*\*评论\*\*:\s*(?P<comment>\d+|-)\n"
    r"-\s*\*\*原文链接\*\*:\s*<(?P<link>\S+)>",
    re.S,
)


def parse_md(path):
    """解析 xhs-dl 生成的 Markdown，提取元数据。"""
    txt = open(path, encoding="utf-8").read()
    m = MD_RE.search(txt)
    if not m:
        return None
    d = m.groupdict()
    title = (d["title"] or "").strip()
    t = (d["time"] or "").strip()
    date = t.split(" ")[0] if t else ""

    # 正文：## 正文 到下一个 ## 之间；话题以 #xxx[话题]# 形式嵌在正文里
    body_raw = ""
    bm = re.search(r"##\s*正文\s*\n(.*?)(?=\n##\s|\Z)", txt, re.S)
    if bm:
        body_raw = bm.group(1).strip()
    clean = body_raw.replace("[话题]#", " ").replace("[话题]", "")
    tags = re.findall(r"#([^\s#]+)", clean)
    seen, tag_out = set(), []
    for t2 in tags:
        t2 = t2.strip(" ，。、")
        if t2 and t2 not in seen:
            seen.add(t2)
            tag_out.append(t2)
    desc = re.sub(r"#[^\s#]+", "", clean)
    desc = re.sub(r"\s+", " ", desc).strip()

    return {
        "note_id": d["note_id"].strip(),
        "标题": title or "未命名",
        "发布时间": date,
        "类型": (d["type"] or "").strip(),
        "统计": {
            "digg_count": int(d["digg"]) if d["digg"].isdigit() else 0,
            "collect_count": int(d["collect"]) if d["collect"].isdigit() else 0,
            "comment_count": int(d["comment"]) if d["comment"].isdigit() else 0,
            "recommend_count": 0,
            "share_count": 0,
        },
        "作品链接": (d["link"] or "").strip(),
        "标签": tag_out[:6],
        "正文": desc,
    }


def image_size(path):
    """读图片宽高；读不了就退 0（build_library 里会再兜底）。"""
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return (0, 0)


def media_files(folder):
    """编号媒体文件，按数字序号排序（1.webp, 2.webp, ..., 10.webp）。"""
    out = []
    for f in os.listdir(folder):
        m = re.match(r"^(\d+)\.(webp|jpg|jpeg|png|gif)$", f, re.I)
        if m:
            out.append((int(m.group(1)), f))
    out.sort()
    return [f for _, f in out]


def restructure_note(name):
    """note/<标题>/ → 小红书源/<标题>/（图文）。

    幂等：源目录媒体已搬走的（重跑场景），改为从目标目录收集媒体，
    用仍然留在 note/<标题>/ 里的 md 重新生成 info.json。
    """
    src = os.path.join(SRC, "note", name)
    md = os.path.join(src, name + ".md")
    meta = parse_md(md) if os.path.exists(md) else None
    if not meta:
        print(f"  ! md 解析失败，跳过：{name}", file=sys.stderr)
        return None

    dst = os.path.join(DST, name)
    os.makedirs(dst, exist_ok=True)
    for f in media_files(src):
        shutil.move(os.path.join(src, f), os.path.join(dst, f))

    imgs = []
    for f in media_files(dst):
        w, h = image_size(os.path.join(dst, f))
        imgs.append({"file": f, "width": w, "height": h})
    if not imgs:
        print(f"  ! 没有媒体文件，跳过：{name}", file=sys.stderr)
        return None

    info = {
        "渠道": "小红书",
        "note_id": meta["note_id"],
        "标题": meta["标题"],
        "发布时间": meta["发布时间"],
        "作者": dict(AUTHOR),
        "统计": meta["统计"],
        "类型": meta["类型"] or "图文",
        "作品链接": meta["作品链接"],
        "标签": meta["标签"],
        "正文": meta["正文"],
        "媒体": {"kind": "image", "images": imgs},
    }
    with open(os.path.join(dst, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    return ("image", name, len(imgs))


def restructure_video(name):
    """video/<标题>.mp4 → 小红书源/<标题>/video.mp4（视频）。

    幂等：mp4 已搬走的（重跑场景），用仍在 video/ 里的 md 重新生成 info.json。
    """
    base = os.path.join(SRC, "video", name)
    src_mp4 = base + ".mp4"
    src_md = base + ".md"
    dst = os.path.join(DST, name)
    dst_mp4 = os.path.join(dst, "video.mp4")
    if not os.path.exists(src_mp4) and not os.path.exists(dst_mp4):
        print(f"  ! 视频缺失，跳过：{name}", file=sys.stderr)
        return None
    meta = parse_md(src_md) if os.path.exists(src_md) else None
    if not meta:
        print(f"  ! md 解析失败，跳过：{name}", file=sys.stderr)
        return None

    os.makedirs(dst, exist_ok=True)
    if os.path.exists(src_mp4):
        shutil.move(src_mp4, dst_mp4)

    info = {
        "渠道": "小红书",
        "note_id": meta["note_id"],
        "标题": meta["标题"],
        "发布时间": meta["发布时间"],
        "作者": dict(AUTHOR),
        "统计": meta["统计"],
        "类型": "视频",
        "作品链接": meta["作品链接"],
        "标签": meta["标签"],
        "正文": meta["正文"],
        "媒体": {"kind": "video", "video": "video.mp4"},
    }
    with open(os.path.join(dst, "info.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    return ("video", name, 1)


def main():
    if not os.path.isdir(SRC):
        print(f"源目录不存在：{SRC}", file=sys.stderr)
        sys.exit(1)

    done = {"image": 0, "video": 0}
    skipped = 0

    note_dir = os.path.join(SRC, "note")
    if os.path.isdir(note_dir):
        for name in sorted(os.listdir(note_dir)):
            if not os.path.isdir(os.path.join(note_dir, name)):
                continue
            r = restructure_note(name)
            if r:
                done["image"] += 1
                print(f"  ✓ 图文 {r[1]}（{r[2]} 张）")
            else:
                skipped += 1

    video_dir = os.path.join(SRC, "video")
    if os.path.isdir(video_dir):
        for f in sorted(os.listdir(video_dir)):
            if f.endswith(".mp4"):
                r = restructure_video(f[:-4])
                if r:
                    done["video"] += 1
                    print(f"  ✓ 视频 {r[1]}")
                else:
                    skipped += 1

    print(f"\n完成：图文 {done['image']} 部 / 视频 {done['video']} 部，跳过 {skipped}")
    print(f"新结构：{DST}/<作品名>/{{1.webp…, video.mp4, info.json}}")
    print(f"确认无误后可删除中间目录：{SRC}")


if __name__ == "__main__":
    main()
