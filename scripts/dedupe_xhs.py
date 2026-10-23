#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
双平台去重比对：小红书笔记 ↔ 抖音作品。

方法：平均哈希（ahash, 16×16=256 bit）比对首图（视频用 ffmpeg 抽 2s 帧）。
同一张图换平台转码（webp/jpg）后 ahash 汉明距离通常 0~4；不同图一般 >15。
距离 ≤8 且图片数一致的判为同一部作品；结果写 scripts/dupe_map.json，
供 build_library.py 合并双平台条目（channel=双平台）时消费。

用法：python3 scripts/dedupe_xhs.py
"""

import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XHS_DIR = os.path.join(ROOT, "小红书源")
LIB = os.path.join(ROOT, "data", "library.js")
OUT = os.path.join(ROOT, "scripts", "dupe_map.json")

from PIL import Image

N = 16  # 16×16 → 256 bit


def ahash(path):
    """图片文件的平均哈希；视频先用 ffmpeg 抽帧。"""
    p = path
    if path.lower().endswith((".mp4", ".mov")):
        fd, p = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        r = subprocess.run(
            ["ffmpeg", "-y", "-ss", "2", "-i", path, "-frames:v", "1", p],
            capture_output=True,
        )
        if r.returncode != 0 or os.path.getsize(p) == 0:
            os.unlink(p)
            return None
    try:
        with Image.open(p) as im:
            g = im.convert("L").resize((N, N), Image.LANCZOS)
            px = list(g.getdata())
            avg = sum(px) / len(px)
            bits = 0
            for i, v in enumerate(px):
                if v > avg:
                    bits |= 1 << i
            return bits
    except Exception as e:
        print(f"  ! hash fail {path}: {e}", file=sys.stderr)
        return None
    finally:
        if p != path and os.path.exists(p):
            os.unlink(p)


def dist(a, b):
    if a is None or b is None:
        return 999
    return bin(a ^ b).count("1")


def load_douyin():
    txt = open(LIB, encoding="utf-8").read()
    m = re.search(r"window\.LIBRARY = (.*?);\s*$", txt, re.S)
    d = json.loads(m.group(1))
    out = []
    for w in d["works"]:
        full = None
        if w["kind"] == "video":
            # 视频优先用网页版（压过的 1080p），与原目录对齐
            vp = os.path.join(ROOT, w["dir"])
            for cand in ("video_web.mp4", "video.mp4"):
                if os.path.exists(os.path.join(vp, cand)):
                    full = os.path.join(vp, cand)
                    break
        elif w.get("images"):
            full = os.path.join(ROOT, w["dir"], os.path.basename(w["images"][0]["full"]))
        if full and os.path.exists(full):
            files = []
            if w["kind"] == "video":
                files = [full]
            else:
                for im in w.get("images") or []:
                    fp = os.path.join(ROOT, w["dir"], os.path.basename(im["full"]))
                    if os.path.exists(fp):
                        files.append(fp)
            out.append({
                "dir": w["dir"], "title": w["title"], "kind": w["kind"],
                "count": w.get("count") or 0, "cover": full, "files": files,
            })
    return out


def load_xhs():
    out = []
    for name in sorted(os.listdir(XHS_DIR)):
        d = os.path.join(XHS_DIR, name)
        p = os.path.join(d, "info.json")
        if not os.path.exists(p):
            continue
        j = json.load(open(p, encoding="utf-8"))
        m = j.get("媒体") or {}
        if m.get("kind") == "video":
            full = os.path.join(d, m.get("video") or "video.mp4")
            count = 1
        else:
            imgs = m.get("images") or []
            full = os.path.join(d, imgs[0]["file"]) if imgs else None
            count = len(imgs)
        if full and os.path.exists(full):
            files = []
            if m.get("kind") == "video":
                files = [full]
            else:
                for im in (m.get("images") or []):
                    fp = os.path.join(d, im["file"])
                    if os.path.exists(fp):
                        files.append(fp)
            out.append({
                "dir": name, "title": j.get("标题"), "kind": m.get("kind"),
                "count": count, "cover": full, "files": files,
            })
    return out


def main():
    dy = load_douyin()
    xh = load_xhs()
    print(f"抖音 {len(dy)} 部 / 小红书 {len(xh)} 部\n")

    pairs = []
    for x in xh:
        hx = ahash(x["cover"])
        for d in dy:
            hd = ahash(d["cover"])
            dd = dist(hx, hd)
            if dd <= 12:
                pairs.append((dd, x, d))

    pairs.sort(key=lambda t: t[0])
    print("距离  小红书作品                        抖音作品                          图数")
    print("-" * 90)
    for dd, x, d in pairs:
        flag = "★" if dd <= 8 else " "
        print(f"{flag}{dd:3d}   {x['title'][:20]:<22} {d['title'][:20]:<22} "
              f"{x['count']}/{d['count']}")

    # 判定：首图距离 ≤8 只是候选。最终看「小红书这篇的图有多大比例
    # 出现在抖音那部作品里」——重叠率 ≥60% 才判同一作品（同拍摄、两平台发帖，
    # 选图/标题不同很常见；只共用封面但内容不同的是不同帖，不合并）。
    def overlap_ratio(x, d):
        xh = [ahash(f) for f in x["files"]]
        dy = [ahash(f) for f in d["files"]]
        xh = [h for h in xh if h]
        dy = [h for h in dy if h]
        if not xh or not dy:
            return 0.0
        hit = sum(1 for h in xh if any(dist(h, g) <= 6 for g in dy))
        return hit / len(xh)

    dupe = {}
    for dd, x, d in pairs:
        if dd > 8:
            continue
        ratio = overlap_ratio(x, d)
        if ratio < 0.6:
            continue
        key = x["dir"]
        cand = (dd, -ratio, d["dir"], d["title"], x["count"], d["count"])
        if key not in dupe or cand[:2] < dupe[key][0][:2]:
            dupe[key] = (cand, ratio)
    dupe_out = {}
    for k, (cand, ratio) in dupe.items():
        dupe_out[k] = {
            "douyin_dir": cand[2],
            "distance": cand[0],
            "overlap": round(ratio, 2),
            "xhs_count": cand[4],
            "douyin_count": cand[5],
        }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(dupe_out, f, ensure_ascii=False, indent=1)
    print(f"\n判定重复 {len(dupe_out)} 部 → {OUT}")
    for k, v in dupe_out.items():
        print(f"  ★ {k}  ↔  {v['douyin_dir']}（首图距离 {v['distance']}，"
              f"图片重叠 {v['overlap']:.0%}，{v['xhs_count']}/{v['douyin_count']} 张）")


if __name__ == "__main__":
    main()
