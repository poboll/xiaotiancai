# 拾遗馆

小天才（余乐彤）的作品归档，外加一封没寄出的信。

线上地址：**https://xtc.caiths.com**

[![《女主》禁止上船，后果自负 · 结尾](media/nvzhu-loop.gif)](https://raw.githubusercontent.com/poboll/xiaotiancai/main/media/nvzhu.mp4)

> 《女主》禁止上船，后果自负 · 全片 82 秒，`media/nvzhu.mp4`（21MB）。GIF 只是结尾四秒的循环，点它看完整视频。

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
| `index.html` | 首页。两行开场、置顶两条、128 部作品的瀑布流，可按图文/视频/渠道/年份筛 |
| `story.html` | 「我为什么收这些」，上面那段话的完整版 |
| `work.html?w=<id>` | 单部作品的详情页，图片竖排、可点开大图、上下篇切换；视频作品下方直接展示全片文稿 |
| `works/longlong-xiaotiancai/` | 《致王卓凡》那封信的阅读页，附故事梗概、观后感、精选评论、插图 |
| `works/longlong-xiaotiancai/assets/` | 信的 PDF 打印版和 DOCX 可编辑版 |

**双平台归档**：她的作品在抖音和小红书两边都发。同一部作品两边都有的，在数据里合并成一条（渠道标「双平台」，出处给两个原文链接）；只有一边有的，标「抖音」或「小红书」。首页可以按渠道筛。

作品数据不是手写的。`scripts/build_library.py` 会扫描 `抖音源/` 和 `小红书源/` 里每个带 `info.json` 的文件夹，读标题、日期、点赞、图片列表，生成 `data/library.js` 和缩略图。所以**丢一个新文件夹进去，跑一下脚本，首页就自动多一张卡片**。

两部纪录片（冈仁波齐、喀什）的全片文稿放在 `data/scripts.js` 里，由内嵌字幕逐帧识别 + 人工听校交叉校验整理，会按句断段、带章节标题和时间码显示在视频下方。

---

## 目录

```
.
├── index.html               首页
├── story.html               我的那段话
├── work.html                作品详情（?w=<id>）
├── 404.html                 链接失效时的兜底页
├── favicon.svg / .png       站点图标
├── assets/
│   ├── site.css             全站样式
│   ├── app.js               首页：置顶 + 筛选 + 瀑布流
│   └── work.js              详情页：图片、灯箱、上下篇、视频文稿
├── data/
│   ├── works.js             站名、开场白、置顶两条（手改这里）
│   ├── library.js           作品数据（脚本生成，别手改）
│   └── scripts.js           两部纪录片的全片文稿（手改这里）
├── 抖音源/
│   └── <标题>/              抖音作品：01.webp… + video.mp4 + info.json
├── 小红书源/
│   └── <标题>/              小红书作品：01.webp… + video.mp4 + info.json
│       └── 原图/            PNG 原片（.gitignore，只留本地）
├── media/
│   ├── nvzhu.mp4            《女主》禁止上船全片（README 和信件页用）
│   ├── nvzhu-loop.gif       结尾四秒循环（README 自动播放用）
│   ├── nvzhu-poster.jpg     视频封面帧
│   └── ill/                 信件页插图（webp）
├── scripts/
│   ├── build_library.py     扫描两个源目录 → 生成 library.js + 缩略图
│   ├── xhs_png_to_webp.py   PNG 原图转同分辨率 WebP（幂等）
│   ├── dedupe_xhs.py        ahash + 全图重叠率判双平台重复 → dupe_map.json
│   ├── restructure_xhs.py   把下载工具的两层目录拍平
│   └── dupe_map.json        双平台去重表（build_library.py 消费它）
├── thumbs/                  缩略图（640px webp）和视频封面
├── works/
│   ├── _template/           新作品的空白模板
│   └── longlong-xiaotiancai/ 那封信
└── .github/workflows/pages.yml
```

作品文件夹的名字就是原视频的标题，带话题、带空格。**URL 里不会出现它们**——每部作品在数据里有一个短 id（抖音的 `aweme_id`、小红书的 `note_id`），所以链接是 `work.html?w=7694638636729750649`，不是一长串百分号。

---

## 原图是怎么发现、怎么拿到的

这一节是这个仓库里最值得留下的东西。小红书的水印和清晰度坑，我踩遍了。

### 1. 下载工具

用的是 Gitee 上的 [`hnxyy/xhs-downloader`](https://gitee.com/hnxyy/xhs-downloader)，Go 写的，用 go-rod 驱动 Chrome，读页面的 `window.__INITIAL_STATE__` 拿数据——绕开了 x-s / x-t 签名那套。源码放在 `tools/xhs-dl-src/`（本地，`.gitignore` 挡掉）。

### 2. 游客只能看 31 篇，登录才有 80 篇

第一次跑完只下来 31 篇。我以为是工具漏了，其实不是——**未登录状态下小红书主页只吐 31 篇笔记**，滚动到底就没了。扫码登录一次（登录态持久化在 `~/.xhs-dl/browser-data`），重跑，80 篇全量到手。

### 3. 网页端给的是缩图，不是原图

工具默认拿的是网页端签名 URL：

```
https://sns-webpic-qc.xhscdn.com/1040g2sg31.../{fileId}!nd_dft_wgth_webp_3
```

这地址带签名、带「配方」，服务端按配方决定回多大的图——**1080 到 1439 宽之间的 webp**。改后缀、改参数，一律 403。而第三方解析能拿到 1703×2271，差了一截。

### 4. 突破口：抓包看去水印小程序

用户给了个去水印小程序的 HAR 抓包（`Stream-2026-10-23 11:25:06.har`，36MB，248 个请求）。翻下来发现小程序后端是 `www.async-dev.fun`，图片请求长这样：

```
https://ci.xiaohongshu.com/{fileId}?imageView2/2/w/0/format/png
```

三个关键点：

- **`ci.xiaohongshu.com` 是另一个 CDN**，不走网页端那套签名
- **`w/0` 是不缩放**，服务端按原尺寸给
- **`format/png` 是无损转出**——裸链默认返回 HEIC 原片，指定 png 才转成 PNG

而且小程序下的文件和用户自己从第三方解析下的文件，**字节数完全一致**（4839923）。同一个源。

### 5. fileId 从哪来

`fileId` 就在笔记页的 `__INITIAL_STATE__` 里：

```js
entry.note.noteDetailMap[noteId].note.imageList[].fileId
```

`imageList` 每一项的 `width` / `height` **就是原图尺寸**（比如 2560×1922），网页端 URL 里的尺寸是服务端另外算的，两者不是一回事。

我写了个探针 `tools/xhs-dl-src/cmd/probe/main.go`，把笔记页 `imageList` 的原始 JSON 整个 dump 出来对比，才确认这条路走得通。

### 6. 给工具打补丁

改了三处：

| 文件 | 改动 |
|---|---|
| `internal/xhs/types.go` | `Image` 结构加 `FileId` 字段 |
| `internal/xhs/note.go` | 解析时把 `fileId` 带出来 |
| `internal/cli/common.go` | 图片任务优先拼 `ci.xiaohongshu.com` 原图地址，网页 URL 降级成 fallback |

### 7. 扩展名 bug：Content-Type 会骗人

补丁跑通后，文件扩展名全是 `.jfif` 或 `.jpg`，内容其实是 PNG。两个坑叠在一起：

- Go 的 `mime.ExtensionsByType("image/png")` 在部分系统上返回 `.jfif`
- **直连（不走代理）时，`ci.xiaohongshu.com` 把 PNG 内容标成 `Content-Type: image/jpeg`**

所以不能信响应头。改成读**文件头魔术字节**判格式（`sniffExt`），PNG/JPEG/WEBP/GIF/HEIC 各自认各自的。这一下根治了。

### 8. 结果

360 张原图全量重下，1.5GB，尺寸 1440×1920 / 1920×2560 / 1706×2560 / 2560×1922 等，`info.json` 里记的尺寸和实际文件零误差。

---

## 体积与清晰度：为什么图片是 WebP，视频才走 LFS

### 图片：全分辨率 WebP，PNG 原片留本地

PNG 原图单张 4-7MB，360 张 1.5GB。直接进 git，仓库会涨到 1.8GB——clone 慢，站点每点开一张图都要加载 4MB+。

`scripts/xhs_png_to_webp.py` 把它们转成**同分辨率 WebP**（q92, method 6）：

- **像素数一点没变**，还是 1706×2560 / 2560×1922
- 体积降到 PNG 的 **16%** 左右（1.5GB → 210MB）
- q92 对照片是视觉无损，损失只在发丝、远处树叶这类极高频细节里，基本看不出来

PNG 原片没删，移到各作品的 `原图/` 子目录，`.gitignore` 挡掉，只留本地。想比对随时可以。

抖音那边的图本来下载下来就是 webp，不用转。

### 视频：Git LFS

`.gitattributes` 里只让 mp4 走 LFS：

```
抖音源/**/*.mp4 filter=lfs diff=lfs merge=lfs -text
小红书源/**/*.mp4 filter=lfs diff=lfs merge=lfs -text
```

原因是 mp4 是二进制，git 压不动，而且原片可能超 GitHub 单文件 100MB 上限。进 LFS 的视频一共 110MB 左右，配额和带宽都宽裕。

### 为什么图片不走 LFS

GitHub Pro 的 LFS 配额是 **2GB 存储 + 2GB 月带宽**。1.5GB 原图走 LFS 的话：

- 存储一口吃掉 75%，基本没余量
- 更致命的是**带宽**——Pages 每次自动部署都要 `actions/checkout` 拉一遍 LFS，**一次部署就是 1.5GB，一个月只能部署一次**

所以图片走普通 git + WebP，只有视频走 LFS。这是算过账的，不是随便定的。

### 4K 原片留在本地

两部纪录片的 4K 母版（174MB / 163MB）超过 GitHub 单文件 100MB 上限，`.gitignore` 排掉了，进仓库的是压过的 `video_web.mp4`（1080p，35-52MB）。

---

## 抖音那边是不是也没拿到最清晰的？

查了，而且这次是拿接口原始数据逐条实测的，不是看尺寸猜。

### 图片：尺寸是原图，质量档是 q75

抖音作品图在接口里有两套地址：

| 字段 | 模板 | 特征 |
|---|---|---|
| `images[].url_list[0]` | `tplv-dy-aweme-images:q75.webp` | **无水印、不带缩放参数** ← 下载用的是这个 |
| `images[].download_url_list[0]` | `tplv-dy-water-v2:<水印>:W:H.webp` | 带水印，且缩到 API 声明的尺寸 |

两个关键实测：

1. **`q75` 模板没有缩放参数，服务端返回的就是原图分辨率。** 比如 `aweme_id=7509483903486446905`，API 声明 1440×1920，实际从链接取到 **2160×2880**；`7517627389665398073` 声明 1920×1280，实取 **3240×2160**。本地文件和链接返回**字节级一致**。所以 `info.json` 里记的 `width`/`height` 是低一档的声明值，不是原图尺寸——这也是之前 546 张里有 31 张「实际大于声明」的原因。
2. **想换更高档不行。** 把模板改成 `q90` / `q100` / 去掉模板，全部 **403**——URL 的 `x-signature` 和模板是绑定的，改一个字符签名就失效。而接口里压根没提供别的无水印档位。

所以：**尺寸上早就拿到原图了，唯一残留的是 q75 这个有损压缩档，而抖音不提供更高的无水印档位。**

### 视频：最高档

`video.bit_rate` 是个按码率降序的档位表。下载逻辑优先 `download_addr.url_list`，否则展平所有 `bit_rate[].play_addr.url_list` 取第一条（即最高档）。实测两部纪录片：

| 作品 | 分辨率 | 编码 | 码率 |
|---|---|---|---|
| 真正的西域 · 喀什 | 3840×2160 | HEVC | 4.45 Mbps |
| 总有一天 · 冈仁波齐 | 3840×2160 | HEVC | 3.20 Mbps |

和 `bit_rate` 列表顶部条目（4454068 / 4516259）对得上。**视频也是服务端给的最好水平。**

### 结论

抖音侧不用重下。抓包里的两个小程序都是小红书解析器，对抖音不适用。

---

## 双平台去重

同一部作品两边都发，但选图和标题不一定一样，不能按标题判重。`scripts/dedupe_xhs.py` 的做法：

1. 对小红书首图和抖音封面算 **ahash**（16×16 平均哈希，256 bit）
2. 距离 ≤ 8 的进候选
3. 候选再按**全图重叠率 ≥ 60%** 最终判定
4. 标题相似度做 tiebreak

结果写在 `scripts/dupe_map.json`，12 部双平台作品。`build_library.py` 消费它：命中的小红书作品不单列，合并进抖音条目，渠道改「双平台」，附上 `xhsLink`。

重复的那 12 份小红书媒体（355MB）由脚本自动写 `.gitignore` 挡掉，只保留 `info.json` 记元数据和原文链接。

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

往仓库里加新的小红书 PNG 原图后：

```bash
python3 scripts/xhs_png_to_webp.py   # 转 WebP，原图移进 原图/
python3 scripts/build_library.py
```

---

## 加一部新作品

1. 把下载好的文件夹丢进 `抖音源/` 或 `小红书源/`（里面要有 `info.json`）。
2. 跑 `python3 scripts/build_library.py`。
3. `git add . && git commit -m "feat: 新作品" && git push`。

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

置顶哪几部作品在 `scripts/build_library.py` 的 `PINNED_ORDER` 里，按 `aweme_id` 写。

---

## 发布

推到 `main` 就自动部署，workflow 会先跑一遍 `build_library.py` 再上传。checkout 步骤带 `lfs: true`，视频实体才会被拉下来。

首次需要开一次开关：

> 仓库 → **Settings** → **Pages** → **Build and deployment** → **Source** 选 **GitHub Actions**

自定义域名 `xtc.caiths.com` 走 Cloudflare：

- Cloudflare DNS 加一条 `CNAME  xtc → poboll.github.io`，**代理状态关掉**（灰色云，DNS only）。开着橙云 GitHub 签不出证书。
- GitHub 仓库 Pages 设置里填 `xtc.caiths.com`，等证书签发（几分钟到半小时）。
- 想强制 https，等证书好了再勾 `Enforce HTTPS`。

---

## 版权

站内所有影像、文字版权归原作者 **小天才.（余乐彤）** 所有。这里只做个人收藏和阅读记录，不用于任何商业用途，也不接广告。如果作者本人希望撤下，删掉对应文件夹即可。
