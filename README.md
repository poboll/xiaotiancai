# 拾遗馆

小天才（余乐彤）的作品归档，外加一封没寄出的信。

线上地址：**https://xtc.caiths.com**

<video src="https://raw.githubusercontent.com/poboll/xiaotiancai/main/media/ending.mp4" width="100%" autoplay loop muted playsinline controls></video>

> 《女主》禁止上船，后果自负 · 结尾。她说完「你就做自己的齐天大圣」，然后把眼睛闭上了。

---

## 我为什么弄这个

我是从《龙龙历险记》那条南瓜饼的视频入坑的。

她把南瓜饼递过去，他愣了一下。就那半秒，我信了——人在被真心对待的时候脸上是空的，来不及想镜头。这个演不出来。

后来我把她主页从头翻到尾，翻到半夜。翻出来的不只是她的东西，还有我自己那堆旧账：高中的暗恋没说过，大学那几年暧昧了很久谁也没开口，再后来和初恋「呆呆」在一起，一年半，到现在还算稳。只是大学那几年我几乎没带她出去玩过。

看完他们的故事我才反应过来：两个人能顺顺当当地在一起，是千百年修来的缘份。多数人不是不爱，是差一口气。

所以这个站一半是给她存档，一半是给自己留个证据。完整的话写在 [`story.html`](story.html) 里。

那封信我单独整理成了能打印的一版，想挂起来。

---

## 站里有什么

| 页面 | 作用 |
|---|---|
| `index.html` | 首页。两行开场、置顶两条、60 部作品的瀑布流，可按图文/视频/年份筛 |
| `story.html` | 「我为什么收这些」，上面那段话的完整版 |
| `work.html?w=<id>` | 单部作品的详情页，图片竖排、可点开大图、上下篇切换；视频作品下方直接展示全片文稿 |
| `works/longlong-xiaotiancai/` | 《致王卓凡》那封信的阅读页，附故事梗概、观后感、精选评论、插图 |
| `works/longlong-xiaotiancai/assets/` | 信的 PDF 打印版和 DOCX 可编辑版 |

作品数据不是手写的。`scripts/build_library.py` 会扫描仓库里每个带 `info.json` 的文件夹，读标题、日期、点赞、图片列表，生成 `data/library.js` 和缩略图。所以**丢一个新文件夹进来，跑一下脚本，首页就自动多一张卡片**。

两部纪录片（冈仁波齐、喀什）的全片文稿放在 `data/scripts.js` 里，由内嵌字幕逐帧识别 + 人工听校交叉校验整理，会显示在视频下方。`纪录片学习/` 里还有文稿的 Markdown 版和一篇创作方法分析。

---

## 目录

```
.
├── index.html               首页
├── story.html               我的那段话
├── work.html                作品详情（?w=<id>）
├── favicon.svg / .png       站点图标
├── assets/
│   ├── site.css             全站样式
│   ├── app.js               首页：置顶 + 筛选 + 瀑布流
│   └── work.js              详情页：图片、灯箱、上下篇、视频文稿
├── data/
│   ├── works.js             站名、开场白、置顶两条（手改这里）
│   ├── library.js           作品数据（脚本生成，别手改）
│   └── scripts.js           两部纪录片的全片文稿（手改这里）
├── media/
│   ├── ending.mp4           《女主》结尾片段（README 和信件页用）
│   └── ill/                 信件页插图（webp）
├── scripts/
│   └── build_library.py     扫描文件夹 → 生成 library.js + 缩略图
├── thumbs/                  缩略图（640px webp）和视频封面
├── works/
│   ├── _template/           新作品的空白模板
│   └── longlong-xiaotiancai/ 那封信
├── 纪录片学习/               两部纪录片的文稿 + 创作方法分析
├── 各作品文件夹/            每个文件夹 = 一条抖音作品（info.json + 图/视频）
└── .github/workflows/pages.yml
```

作品文件夹的名字就是抖音原视频的标题，带话题、带空格。**URL 里不会出现它们**——每部作品在数据里有一个短 id（抖音的 `aweme_id`），所以链接是 `work.html?w=7694638636729750649`，不是一长串百分号。

---

## 本地预览

```bash
cd ~/Downloads/小天才
python3 -m http.server 8899
# 打开 http://127.0.0.1:8899
```

改完东西要重新生成数据时：

```bash
python3 scripts/build_library.py     # 需要 Pillow：pip install pillow
```

---

## 加一部新作品

1. 把下载好的文件夹整个丢进仓库根目录（里面要有 `info.json`）。
2. 跑 `python3 scripts/build_library.py`。
3. `git add . && git commit -m "add: 新作品" && git push`。

不用碰 HTML，也不用碰 `library.js`。线上会自动多一张卡片。

> 如果是视频作品，原片超过 100MB 的话 GitHub 会拒收。压一个网页版再放进去：
> ```bash
> ffmpeg -i video.mp4 -vf scale=1920:-2 -c:v libx264 -preset medium \
>        -b:v 900k -c:a aac -b:a 96k -movflags +faststart video_web.mp4
> ```
> 脚本会优先用 `video_web.mp4`。

## 改置顶 / 改开场白

全在 `data/works.js` 顶上：

```js
tagline: "她拍下的都是真的，我难受也是。",
intro:   "没什么大道理，就是舍不得删。",

pinned: [
  { kicker, title, sub, text, href, cta },   // 第一条
  { ... }                                     // 第二条
]
```

`href` 可以指站内页面（`works/xxx/index.html`），也可以指站外（加 `external: true` 就会新窗口打开）。

---

## 发布

推到 `main` 就自动部署，workflow 会先跑一遍 `build_library.py` 再上传。

首次需要开一次开关：

> 仓库 → **Settings** → **Pages** → **Build and deployment** → **Source** 选 **GitHub Actions**

自定义域名 `xtc.caiths.com` 走 Cloudflare：

- Cloudflare DNS 加一条 `CNAME  xtc → poboll.github.io`，**代理状态关掉**（灰色云，DNS only）。开着橙云 GitHub 签不出证书。
- GitHub 仓库 Pages 设置里填 `xtc.caiths.com`，等证书签发（几分钟到半小时）。
- 想强制 https，等证书好了再勾 `Enforce HTTPS`。

---

## 关于体积

GitHub 单文件上限 100MB、仓库建议不超过 1GB，所以：

- **4K 原片留在本地**，不进仓库（`.gitignore` 里排掉了那两条）。
- 进仓库的是压过的 `video_web.mp4`（1080p，约 50MB）。
- `_dedupe_backup/`（270MB 旧备份）也排掉了。
- `thumbs/` 是缩略图，24MB，必须留着，不然首页会直接加载原图，很慢。

---

## 版权

站内所有影像、文字版权归原作者 **小天才.（余乐彤）** 所有。这里只做个人收藏和阅读记录，不用于任何商业用途，也不接广告。如果作者本人希望撤下，删掉对应文件夹即可。
