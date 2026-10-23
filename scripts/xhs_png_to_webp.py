#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 小红书源/ 里的 PNG 原图转成全分辨率 WebP（q92, method 6），原图移入 原图/ 子目录留档。

为什么转：
  - PNG 原图单张 4-7MB，360 张共 1.5GB。直接进 git 仓库会涨到 ~1.8GB，
    clone 慢，且站点每张图要加载 4MB+。
  - WebP q92 全分辨率（像素数不变）体积只有 PNG 的 ~16%，视觉无损。
  - 1.5GB 若走 Git LFS：GitHub Pro 配额是 2GB 存储 / 2GB 月带宽，
    而 Pages 每次自动部署都要拉一遍 LFS → 一次部署吃 1.5GB 带宽，
    一个月只能部署一次。所以图片不走 LFS（视频走，体积小、配额安全）。

原图不删：移到 小红书源/<作品名>/原图/ 下，.gitignore 挡掉，只留本地。

幂等：已经转过（目录里没有 .png 但 原图/ 里有）的会跳过。
"""

import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XHS = os.path.join(ROOT, "小红书源")
ORIG_SUB = "原图"
QUALITY = 92

try:
    from PIL import Image
except ImportError:
    sys.exit("需要 Pillow：pip install pillow")


def convert_work(work_dir):
    """转换一个作品文件夹。返回 (转换数, 跳过数, 省下字节)。"""
    pngs = sorted(f for f in os.listdir(work_dir)
                  if f.lower().endswith(".png") and not f.startswith("."))
    if not pngs:
        return 0, 0, 0

    orig_dir = os.path.join(work_dir, ORIG_SUB)
    os.makedirs(orig_dir, exist_ok=True)

    info_path = os.path.join(work_dir, "info.json")
    info = {}
    if os.path.exists(info_path):
        try:
            info = json.load(open(info_path, encoding="utf-8"))
        except Exception:
            info = {}

    n = 0
    saved = 0
    for f in pngs:
        src = os.path.join(work_dir, f)
        dst = os.path.join(work_dir, os.path.splitext(f)[0] + ".webp")
        try:
            with Image.open(src) as im:
                im.load()
                im.convert("RGB").save(dst, "WEBP", quality=QUALITY, method=6)
        except Exception as e:
            print(f"  ! 转换失败 {f}: {e}", file=sys.stderr)
            continue
        saved += os.path.getsize(src) - os.path.getsize(dst)
        shutil.move(src, os.path.join(orig_dir, f))
        n += 1

    # info.json 里的文件名同步改成 .webp
    media = info.get("媒体") or {}
    for im in media.get("images", []):
        f = im.get("file") or ""
        if f.lower().endswith(".png"):
            im["file"] = os.path.splitext(f)[0] + ".webp"
    if media.get("video"):
        pass
    if info:
        with open(info_path, "w", encoding="utf-8") as fh:
            json.dump(info, fh, ensure_ascii=False, indent=1)

    return n, 0, saved


def main():
    if not os.path.isdir(XHS):
        sys.exit(f"找不到 {XHS}")
    total_n = 0
    total_saved = 0
    for name in sorted(os.listdir(XHS)):
        d = os.path.join(XHS, name)
        if not os.path.isdir(d) or name == ORIG_SUB:
            continue
        n, _, saved = convert_work(d)
        if n:
            total_n += n
            total_saved += saved
            print(f"  {name}: {n} 张 → webp")
    print(f"\n✓ 共转换 {total_n} 张，省下 {total_saved / 1024 / 1024 / 1024:.2f} GB")
    print(f"  原图已移入各作品的 {ORIG_SUB}/ 子目录（.gitignore，仅本地）")


if __name__ == "__main__":
    main()
