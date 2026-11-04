#!/usr/bin/env python3
"""下载 ai-coding-deals 各工具的官方品牌图标，规范化为 88×88 PNG。

为什么不自动抓 favicon：
    37 个工具里有 12 个的 product URL 会跳到别的品牌域名（Cody → ampcode.com、
    Tabnine → tricentis.com、Qwen Code → GitHub、Amazon Q → AWS 首页……）。
    按 URL 自动取 favicon 会把别家的图标贴上来，比没有图标更糟——那是错误信息。
    所以这里维护一份显式来源表，每个 URL 都是人工确认过属于该品牌的资产。

    表里的优先级是「官方方形 app icon > 该产品 GitHub 组织头像（200×200）> 站点
    apple-touch-icon」。三者都不是时宁可留空，模板会退回字母标记。

用法：
    python3 scripts/fetch_logos.py            # 下载并写入 ai-coding-deals/assets/logos/
    python3 scripts/fetch_logos.py --check    # 只校验已落盘文件是否齐全，不联网

依赖：Pillow。SVG 来源用本机 Chrome headless 栅格化（无 cairosvg 也能工作），
    找不到 Chrome 时只跳过 SVG 来源，其余照常下载。
"""
from __future__ import annotations

import argparse
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "ai-coding-deals" / "assets" / "logos"

CANVAS = 88          # 显示尺寸 44px，按 2x 出图
PAD_RATIO = 0.07     # 留白，避免图标顶到圆角边框
SVG_RENDER = 176     # SVG 先渲染到 2 倍再缩，避免锯齿

CHROME_CANDIDATES = [
    os.environ.get("CHROME_PATH", ""),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

# id -> 官方品牌图标地址。注释写明该 URL 归属，方便日后复核。
SOURCES: dict[str, str] = {
    "cursor": "https://cursor.com/marketing-static/apple-touch-icon-light.png",
    "devin": "https://devin.ai/apple-icon.png",
    "antigravity": "https://antigravity.google/apple-touch-icon.png",
    "kiro": "https://kiro.dev/apple-icon.png",
    # 官方站只给 48px 的 favicon.png，在 44px 槽位里够用，不做进一步放大
    "trae": "https://lf16-web-neutral.traecdn.ai/obj/trae-ai-static/trae_website/favicon.png",
    "zcode": "https://zcode.z.ai/apple-icon.png?v=20260707-transparent",
    # CodeBuddy 两站只提供 40×40 的 SVG app icon，没有栅格版本
    "codebuddy-intl": "https://codebuddy-1328495429.cos.accelerate.myqcloud.com/web/ide/logo.svg",
    "codebuddy-cn": "https://assets.workbuddy.cn/web/workbuddy/2d555459d623c206fdb8c6a492111abb97151910/assets/logo.svg",
    # Qoder 官方站 favIcon 是 SVG，用页面里声明的 412×412 品牌图
    "qoder": "https://img.alicdn.com/imgextra/i4/O1CN01QkSxiCocd3D0prc8_!!6000000008124-2-tps-412-412.png",
    # Zed 官方 favicon 只有 16px，用其 GitHub 组织头像（200×200）
    "zed": "https://github.com/zed-industries.png?size=200",
    # Copilot 页面 favicon 是 GitHub 通用图标（章鱼猫），会变成错误品牌。
    # 改用 Primer Octicons 的官方 Copilot 字形（MIT 许可，SVG 由 Chrome 栅格化）
    "copilot": "https://raw.githubusercontent.com/primer/octicons/main/icons/copilot-24.svg",
    "continue": "https://continue.dev/favicon.png",
    "cline": "https://cline.bot/assets/branding/favicons/apple-touch-icon.png",
    # roocode.com 已被 SPA 接管且 favicon 404，用官方 GitHub 组织头像
    "roo": "https://github.com/RooCodeInc.png?size=200",
    "augment": "https://www.augmentcode.com/apple-touch-icon.png",
    # Amazon Q 是 AWS 产品，官方站点只提供 AWS smile 触控图标（144×144）
    "amazonq": "https://a0.awsstatic.com/libra-css/images/site/touch-icon-ipad-144-smile.png",
    "supermaven": "https://supermaven.com/apple-touch-icon.png",
    "qodo": "https://www.qodo.ai/wp-content/uploads/2025/03/qodo-fav-300x300.png",
    # Cody 官网已重定向到 Amp，用 Sourcegraph 官方组织头像
    "cody": "https://github.com/sourcegraph.png?size=200",
    # tabnine.com 目前返回 502，用官方 GitHub 组织头像
    "tabnine": "https://github.com/Tabnine.png?size=200",
    "freebuff": "https://freebuff.com/favicon/apple-touch-icon.png",
    "codebuff": "https://www.codebuff.com/favicon/apple-touch-icon.png",
    "claude-code": "https://claude.com/apple-touch-icon.png",
    "grok": "https://grok.com/images/apple-touch-icon.png",
    "kimi-code": "https://www.kimi.com/pwa-192.png",
    # openai.com 对非浏览器 UA 返回 403，用官方组织头像
    "codex": "https://github.com/openai.png?size=200",
    "gemini-cli": "https://www.gstatic.com/lamda/images/gemini_sparkle_4g_512_lt_f94943af3be039176192d.png",
    # aider.chat 无声明图标且 /favicon.ico 404，用官方组织头像
    "aider": "https://github.com/Aider-AI.png?size=200",
    "amp": "https://ampcode.com/app-icon.png",
    "opencode": "https://opencode.ai/apple-touch-icon-v3.png",
    "crush": "https://github.com/charmbracelet.png?size=200",
    "goose": "https://github.com/block.png?size=200",
    "qwen-code": "https://github.com/QwenLM.png?size=200",
    "warp": "https://www.warp.dev/apple-touch-icon.png",
    "ollama": "https://ollama.com/public/apple-touch-icon.png",
    "tencent-models": "https://cloud.tencent.com/favicon.ico?t=201902181234",
    "nvidia-nim": "https://build.nvidia.com/favicon.ico?favicon.40e0a499ra0f3.ico",
}

# 这两个品牌的官方资源是「透明背景 + 深色字形」，直接贴在深色卡片上等于隐形
# （augment 平均亮度 0，cline 28）。合成到白底后变成正常的浅色 app icon。
# 这份名单是看图逐张确认出来的，不是按亮度阈值自动算的——饱和色字形（Grok 的
# 白斜杠、Qwen 的蓝丝带）亮度值也很低，但实际很清楚，自动化会误伤它们。
LIGHT_BACKING: frozenset[str] = frozenset({"augment", "cline"})


def find_chrome() -> str | None:
    for cand in CHROME_CANDIDATES:
        if cand and Path(cand).exists():
            return cand
    for name in ("google-chrome", "chromium", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def render_svg(data: bytes) -> Image.Image:
    """用 Chrome headless 把 SVG 渲染成透明背景的 PNG。"""
    chrome = find_chrome()
    if not chrome:
        raise RuntimeError("SVG 来源需要 Chrome，但未找到可执行文件（可设 CHROME_PATH）")

    # 必须内联 SVG 而不是放 <img src="...svg">：通过 img 加载的 SVG 是隔离文档，
    # 无法继承外层 CSS，currentColor 会固定为黑色。内联后 color 才能生效，
    # 让 Octicons 这类 currentColor 字形在深色卡片上显示为白色。
    svg = data.decode("utf-8", "ignore")
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg)
    svg = re.sub(r"<!DOCTYPE[^>]*>", "", svg, flags=re.I)
    # Octicons 这类图标的 path 不写 fill，SVG 默认填充是黑色——注入根节点 fill 才能变白。
    # 显式写了 fill 的元素（如 CodeBuddy 的渐变 rect）不受影响，仍按原样渲染。
    svg = svg.replace("<svg", '<svg fill="#ffffff"', 1)
    html = (
        "<!doctype html><meta charset='utf-8'>"
        "<style>html,body{margin:0;background:transparent;color:#ffffff}"
        f"svg{{width:{SVG_RENDER}px;height:{SVG_RENDER}px;display:block}}"
        "</style>"
        f"<body>{svg}</body>"
    )
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "logo.html"
        shot = Path(tmp) / "logo.png"
        page.write_text(html, encoding="utf-8")
        subprocess.run(
            [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
             "--default-background-color=00000000",
             f"--window-size={SVG_RENDER},{SVG_RENDER}",
             f"--screenshot={shot}", page.as_uri()],
            check=True, capture_output=True, timeout=90,
        )
        return Image.open(shot).convert("RGBA")


def download(url: str, timeout: int = 20) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "image/*,*/*;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read(2_000_000)

    head = data.lstrip()[:120].lower()
    if head.startswith(b"<svg") or b"<svg" in head:
        return render_svg(data)

    im = Image.open(io.BytesIO(data))
    if getattr(im, "n_frames", 1) > 1:      # 多尺寸 .ico，挑最大的一帧
        best = (0, 0)
        for i in range(im.n_frames):
            im.seek(i)
            if im.size[0] * im.size[1] > best[0]:
                best = (im.size[0] * im.size[1], i)
        im.seek(best[1])
    return im.convert("RGBA")


def normalize(im: Image.Image, light_backing: bool = False) -> tuple[Image.Image, bool]:
    """裁掉透明边、按比例缩放到 CANVAS 画布内。返回 (图, 是否含透明像素)。"""
    alpha = im.getchannel("A")
    bbox = alpha.getbbox() if im.mode == "RGBA" else None
    has_alpha = bbox is not None and alpha.getextrema()[0] < 250
    if bbox and (bbox[2] - bbox[0]) > 4 and (bbox[3] - bbox[1]) > 4:
        im = im.crop(bbox)

    if light_backing:
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        bg.alpha_composite(im)
        im = bg

    inner = round(CANVAS * (1 - PAD_RATIO * 2))
    w, h = im.size
    scale = min(inner / w, inner / h)
    new = (max(1, round(w * scale)), max(1, round(h * scale)))
    im = im.resize(new, Image.LANCZOS)

    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    canvas.paste(im, ((CANVAS - new[0]) // 2, (CANVAS - new[1]) // 2), im)
    return canvas, has_alpha


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="只校验落盘文件，不联网")
    ap.add_argument("--only", help="只处理指定的 id，逗号分隔（调试用）")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.check:
        missing = [f"{tid}.png" for tid in SOURCES if not (OUT_DIR / f"{tid}.png").exists()]
        if missing:
            print(f"缺少 {len(missing)} 个图标：{', '.join(missing)}", file=sys.stderr)
            print("运行 python3 scripts/fetch_logos.py 重新下载。", file=sys.stderr)
            return 1
        print(f"{len(SOURCES)} 个品牌图标齐全：{OUT_DIR.relative_to(ROOT)}")
        return 0

    targets = SOURCES
    if args.only:
        want = {t.strip() for t in args.only.split(",") if t.strip()}
        unknown = want - set(SOURCES)
        if unknown:
            print(f"未知 id：{', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        targets = {k: v for k, v in SOURCES.items() if k in want}

    ok, failed = 0, []
    for tid, url in targets.items():
        try:
            img, transparent = normalize(download(url), light_backing=tid in LIGHT_BACKING)
            path = OUT_DIR / f"{tid}.png"
            img.save(path, "PNG", optimize=True)
            size = path.stat().st_size
            flag = "透明" if transparent else "实底"
            print(f"✓ {tid:16} {size:6}B {flag}  {url[:70]}")
            ok += 1
        except Exception as exc:
            failed.append((tid, f"{type(exc).__name__}: {exc}"))
            print(f"✗ {tid:16} {type(exc).__name__}: {str(exc)[:70]}")

    total = sum((OUT_DIR / f"{p}.png").stat().st_size for p in SOURCES if (OUT_DIR / f"{p}.png").exists())
    print(f"\n成功 {ok} / {len(targets)}，图标总量 {total / 1024:.0f} KB")
    for tid, err in failed:
        print(f"  失败 {tid}: {err}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
