#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 data/library.js 重建 INDEX.md —— 本地总索引，给人和脚本看，站点不读它。

双渠道：抖音源/ 与 小红书源/ 分开列，双平台作品在抖音表里标注。
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, "data", "library.js")

src = open(LIB, encoding="utf-8").read()
i = src.index("[")
data = json.loads(src[i:src.rindex("]") + 1])


def num(n):
    if not n:
        return "-"
    if n >= 10000:
        s = ("%.1f" % (n / 10000))
        if n >= 100000:
            s = "%.0f" % (n / 10000)
        return s.rstrip("0").rstrip(".") + "万"
    return str(n)


def kind_label(w):
    return "视频" if w.get("kind") == "video" else "图文"


def rows(works):
    out = []
    for n, w in enumerate(works, 1):
        link = "./" + w["path"].replace("%20", " ").replace("%23", "#")
        # path 是逐段 percent-encoded 的，这里只解最外层即可点
        from urllib.parse import unquote
        link = "./" + unquote(w["path"])
        ch = w.get("channel") or "抖音"
        mark = "　·双平台" if ch == "双平台" else ""
        out.append("| %d | %s | [%s](%s) | %s | %s%s |" % (
            n, w.get("date") or "-", w["title"], link, kind_label(w),
            num((w.get("stats") or {}).get("digg")), mark))
    return out


dy = [w for w in data if (w.get("channel") or "抖音") in ("抖音", "双平台")]
xhs = [w for w in data if w.get("channel") == "小红书"]

lines = []
lines.append("# 小天才. 作品归档（抖音号 Xiaotiancaiylt）")
lines.append("")
lines.append("共 %d 部作品（抖音源 %d 部 / 小红书源 %d 部，其中 %d 部双平台重复已合并）· 整理时间 %s"
             % (len(data), len(dy), len(xhs),
                sum(1 for w in dy if w.get("channel") == "双平台"),
                data and json.loads(src[src.index("{"):src.rindex("}") + 1]).get("generated", "")))
lines.append("")
lines.append("## 抖音源（根目录 `抖音源/`）")
lines.append("")
lines.append("| # | 发布日期 | 作品 | 类型 | 点赞 |")
lines.append("|---|---|---|---|---|")
lines += rows(dy)
lines.append("")
lines.append("## 小红书源（`小红书源/`）")
lines.append("")
lines.append("| # | 发布日期 | 作品 | 类型 | 点赞 |")
lines.append("|---|---|---|---|---|")
lines += rows(xhs)
lines.append("")
lines.append("## 文件说明")
lines.append("")
lines.append("- 视频作品：`video.mp4` 为最高清晰度版，`video_web.mp4` 为压过的 1080p 版（4K 母版超 GitHub 单文件上限，只留本地）；全部无水印")
lines.append("- 图文作品：`01.webp`、`02.webp` … 为作品原图（小红书原为 PNG，已转同分辨率 WebP，PNG 留在各作品 `原图/` 子目录）")
lines.append("- Live 图（照片+视频）：")
lines.append("  - `NN.webp` + `NN.mp4` —— 原始照片与视频（最保真）")
lines.append("  - `NN_live.heic` + `NN_live.mov` —— iOS Live Photo 配对（导入苹果相册可用）")
lines.append("  - `NN_livephoto.jpg` —— Google Motion Photo（安卓/Google 相册可识别）")
lines.append("- `info.json` —— 作品元数据")
lines.append("- 双平台作品：媒体以抖音源为准，小红书目录只留 `info.json` 记元数据和原文链接（见 `scripts/dupe_map.json`）")
lines.append("")
lines.append("## 渠道")
lines.append("")
lines.append("- 抖音 %.0f 部 · 小红书 %.0f 部 · 双平台 %.0f 部"
             % (sum(1 for w in data if w.get("channel") == "抖音"),
                sum(1 for w in data if w.get("channel") == "小红书"),
                sum(1 for w in data if w.get("channel") == "双平台")))
lines.append("- 数据由 `scripts/build_library.py` 生成，本文件只是给人看的总索引")

open(os.path.join(ROOT, "INDEX.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
print("INDEX.md 已重建：抖音源 %d 部 + 小红书源 %d 部 = %d 部" % (len(dy), len(xhs), len(data)))
