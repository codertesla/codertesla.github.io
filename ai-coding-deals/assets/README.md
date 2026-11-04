# 前端资源：同步上游前必读

`style.css` 与 `search.js` 复制自 [telegram-bots](https://github.com/codertesla/telegram-bots) 的 `docs/assets/`。
**但它们不是纯副本。** `style.css` 尾部有约 80 行本地规则，整文件覆盖会静默删掉这些规则——
构建不会报错、CI 不会失败、页面照常打开，只是视觉上退化，而且很难一眼看出是"被覆盖"导致的。

这份文档就是为了拦住那个操作。

---

## TL;DR

覆盖之前先备份：

```bash
cp ai-coding-deals/assets/style.css /tmp/style.css.bak
```

覆盖之后**必须**确认三条本地规则还在：

```bash
grep -nE "acd-ext|#free-paths|\.hero-panel \.pulse-item" ai-coding-deals/assets/style.css
```

输出里必须同时出现 `acd-ext`、`#free-paths`（至少 2 处）、`.hero-panel .pulse-item`。
少任何一条，就从 `/tmp/style.css.bak` 把对应段落贴回去。

---

## 文件与上游的对应关系

| 本地文件 | 上游文件 | 本地改动 | 覆盖安全吗 |
| --- | --- | --- | --- |
| `style.css` | `docs/assets/style.css` | 前 252 行逐字节同源；253–335 行为本地追加 | ⚠️ **只能覆盖前 252 行** |
| `search.js` | `docs/assets/search.js` | 仅 1 处文案（`[acd-local]` 标记处） | ✅ 可整文件覆盖，再重贴那 3 行 |
| `../../scripts/templates/acd.html.j2` | `templates/index.html.j2` | 骨架同源，内容块完全不同 | ❌ 不要覆盖，按需手动搬结构 |

`style.css` 目前共 335 行，上游为 252 行。分界在 `acd-ext` 注释横幅，它本身就是给覆盖操作看的：

```css
/* ============================================================
   acd-ext: AI 编程省钱指南专属内容块
   以上为 telegram-bots 主样式（可整段覆盖同步）
   以下为本地追加区，同步上游时只需保留本段落
   ============================================================ */
```

| 行区间 | 内容 | 覆盖时怎么处理 |
| --- | --- | --- |
| 1–252 | 上游 `style.css` 原文 | 整段替换为新版上游 |
| 253–319 | `acd-ext`：决策矩阵、通用卡片、失效归档、学生权益、法则列表 | 保留，不要动 |
| 320–335 | 三条布局覆盖规则 | **必须手动贴回**，覆盖后大概率会丢 |

---

## 三条布局覆盖规则，以及为什么不能丢

这三条不是审美偏好，是工具数据与 bot 数据形状不同导致的硬冲突。丢掉任意一条，
页面都会出现固定的视觉缺陷，且不会报错。

### 1. 零成本路径固定 6 条 → 等分三列

```css
#free-paths .featured-card,
#free-paths .featured-card:nth-child(1),
#free-paths .featured-card:nth-child(2) { grid-column: span 2; min-height: 0; }
```

上游为 bot 精选区设计：前两张各跨 3 列做大小混排。本项目恰好 6 条，照搬会变成
「3+3 / 2+2+2」，最后一行右侧空出 2 列孤行。改成每张 `span 2` 得整齐的 3×2。

### 2. 学生权益 5 条 → 栅格下限降到 200px

```css
.acd-student-grid { grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); }
```

上游下限 `240px` 在 1440 宽下只能排 4 列，5 条会变成 4+1 孤行。降到 `200px` 正好一行 5 张。

### 3. 主推面板条目等高 → 统一 min-height

```css
.hero-panel .pulse-item { min-height: 88px; }
```

实测：工具名占 1 行时条目 80px，占 2 行时 87px（`Google Antigravity`、`CodeBuddy` 这类长名）。
7px 的差在侧栏里肉眼可见，四条看起来参差不齐。

**不要改用 `line-clamp` 截断文字**——它会把工具名下方的小字厂商名一起裁掉，丢信息。
抬高最小高度是更保守的解法。

---

## 正确的同步流程

```bash
# 0. 先把上游拉到本地（示例路径，按实际情况替换）
cd /path/to/telegram-bots && git pull

# 1. 只取上游的前 252 行（或新的总行数），拼上本地追加区
cd /path/to/codertesla.github.io
LOCAL_TAIL_START=$(grep -n "acd-ext" ai-coding-deals/assets/style.css | head -1 | cut -d: -f1)
# ↑ 得到的是横幅注释行号（当前为 255），往上退 2 行到空行，从这里切出追加区
tail -n +$((LOCAL_TAIL_START - 2)) ai-coding-deals/assets/style.css > /tmp/style.tail.css
cat /path/to/telegram-bots/docs/assets/style.css /tmp/style.tail.css \
  > ai-coding-deals/assets/style.css

# 2. search.js 可以整文件覆盖，但要重贴本地文案
cp /path/to/telegram-bots/docs/assets/search.js ai-coding-deals/assets/search.js
# 然后把第 42 行附近的「个匹配的机器人 / 个机器人 · 个分类」改成「款匹配的工具 / 款工具 · 个分类」

# 3. 自检（见下节）
python3 scripts/build_acd.py --check
```

如果不想算行号，退回到最朴素的办法：覆盖前 `cp` 备份，覆盖后用 `git diff` 看丢了什么，从备份贴回。

---

## 同步后自检

三道，缺一不可：

```bash
# ① 三条规则还在
grep -nE "acd-ext|#free-paths|\.hero-panel \.pulse-item" ai-coding-deals/assets/style.css

# ② 产物与数据一致
python3 scripts/build_acd.py --check

# ③ 视觉：截图看这三处
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
"$CHROME" --headless=new --no-sandbox --disable-gpu --hide-scrollbars \
  --window-size=1440,11000 --virtual-time-budget=4000 \
  --screenshot=/tmp/acd-sync.png "file://$PWD/ai-coding-deals/index.html"
```

截图里要确认：

| 位置 | 正常表现 |
| --- | --- |
| `#free-paths` | 6 张卡排成 3 列 × 2 行，无右侧空白 |
| 学生权益区 | 5 张卡一行，无落单 |
| 首屏右侧主推面板 | 4 条等高，工具名与厂商小字都完整可见 |

---

## 什么时候某条规则可以删

规则和数据条数是绑死的。以下情况需要重新计算，而不是直接保留：

| 触发条件 | 要做什么 |
| --- | --- |
| 零成本路径不再是 6 条（比如 4 条或 9 条） | 重算 `grid-column: span`，让总列数能被条数整除 |
| 学生权益不再是 5 条 | 调整 `minmax()` 下限，使条数能排满一行 |
| 上游改了 `.pulse-item` 的 `min-height` 或字号 | 重新实测单行/双行高度，更新 88px |
| 上游把 `.featured-card` 的跨列逻辑整个换掉 | 覆盖规则可能要改成 `grid-column: auto`，先看新规则再决定 |

改完任何一条，都要重跑上节的三道自检。

---

## 品牌图标（`logos/`）

`logos/{id}.png` 是 37 款工具的官方品牌图标，88×88 PNG，由 `scripts/fetch_logos.py` 生成并提交进仓库。
页面构建时按 `id` 约定引用，**文件不存在就退回首字母标记**，不产生 404。

```bash
python3 scripts/fetch_logos.py             # 全部重抓（需要 Pillow）
python3 scripts/fetch_logos.py --only roo  # 只重抓某几个，调试用
python3 scripts/fetch_logos.py --check     # 只校验文件齐全，不联网
```

### 为什么是显式来源表，而不是自动抓 favicon

37 个工具里有 **12 个的 product URL 会跳到别的品牌域名**：

| 工具 | 页面地址实际落到 | 直接抓 favicon 会得到 |
| --- | --- | --- |
| Sourcegraph Cody | `ampcode.com`（Cody 已日落） | Amp 的标志 |
| Roo Code | `roomote.dev` | 无关站点图标 |
| Tabnine | `tricentis.com`（被收购） | Tricentis 的标志 |
| Qwen Code | `github.com` | GitHub 章鱼猫 |
| Crush / Goose | GitHub Pages | GitHub 章鱼猫 |
| Amazon Q | `aws.amazon.com` | AWS 微笑 |
| Qoder CN | `cn.aliyun.com` | 阿里云标志 |
| GitHub Copilot | `github.com` | 章鱼猫，不是 Copilot |

**贴错品牌的图标比没有图标更糟——那是错误信息。** 所以 `fetch_logos.py` 里是一份人工确认过的
`SOURCES` 表，每个 URL 都注明了归属。加新工具时必须自己指定来源，不要用自动发现。

### 两个已知的例外

- `LIGHT_BACKING = {"augment", "cline"}`：这两个品牌的官方资源是「透明背景 + 深色字形」，
  平均亮度 0 和 28，直接贴在深色卡片上等于隐形，因此合成到白底。
  这份名单是看图逐张确认的，**不要改成按亮度阈值自动判断**——Grok 的白斜杠、Qwen 的蓝丝带
  亮度值同样很低（43 / 52），但实际很清楚，自动化会把它们误伤成白色方块。

- SVG 来源（CodeBuddy 两站、Octicons 的 Copilot）用 Chrome headless 栅格化。
  两个坑：
  1. 必须**内联** SVG，不能用 `<img src="x.svg">`——通过 img 加载的 SVG 是隔离文档，
     不继承外层 CSS，`currentColor` 固定为黑色。
  2. Octicons 的 path 不写 `fill`，SVG 默认填充黑色，`color` 管不到，
     要在根节点注入 `fill="#ffffff"`。

### 刷新图标的时机

工具换 logo、新增工具、或某张图在某次上游改版后变糊时。重抓后**必须**看一眼
90×90 的缩略拼图再提交——自动化只能保证「抓到了图」，保证不了「是这个品牌的图」。

---

## 上游版本记录

| 同步日期 | 上游 commit | 上游 `style.css` 行数 | 本地总行数 |
| --- | --- | --- | --- |
| 2026-11-04 | `7f37a7b` | 252 | 335 |

下次同步后，在表里追加一行，方便以后判断本地追加区是否被改过。
