#!/usr/bin/env python3
"""把 data/ai-coding-deals.json 烘焙为 ai-coding-deals/index.html 静态页面。

页面结构位于 scripts/templates/acd.html.j2，样式与浏览器脚本位于
ai-coding-deals/assets/（从 telegram-bots 站点同步而来，见该文件末尾的
acd-ext 追加区）。数据全部预渲染进 HTML，无运行时数据请求；只要数据不变，
生成结果就逐字节一致，因此 --check 可以放进 CI 拦截手工改产物。

用法：
    python3 scripts/build_acd.py            # 生成
    python3 scripts/build_acd.py --check    # 校验产物是否与数据源同步，不同步退出码 1
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "ai-coding-deals.json"
TEMPLATE_DIR = ROOT / "scripts" / "templates"
OUT_FILE = ROOT / "ai-coding-deals" / "index.html"

TEMPLATE_ENV = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)

PRICE_RE = re.compile(r"[¥$]\s?[\d,]+(?:\.\d+)?")
STATUS_LABELS = {"ended": "已停售", "legacy": "旧版"}

# 首屏速览面板的条目数，超过这个数量在 320px 宽的侧栏里会溢出。
FEATURED_IN_PANEL = 4


def initial(text: str) -> str:
    """头像占位字：中文取首字，拉丁字母取大写首字母。"""
    text = (text or "").strip()
    return text[0].upper() if text else "?"


def price_short(tool: dict) -> str:
    """速览面板用的极简价格：取第一个付费档位的数值，而非 from 全文。"""
    source = tool.get("from", "")
    match = PRICE_RE.search(source)
    if match:
        return f"{match.group(0)}起"
    return "免费" if "免费" in source else "订阅"


def tool_view(tool: dict, cat_labels: dict) -> dict:
    view = dict(tool)
    view["initial"] = initial(tool.get("name"))
    view["cat_label"] = cat_labels.get(tool.get("cat", ""), tool.get("cat", ""))
    view["badge"] = STATUS_LABELS.get(tool.get("status", ""), "")
    return view


def sort_tools(tools: list[dict]) -> list[dict]:
    """精选优先，其余保持数据源顺序（sorted 稳定排序保证这一点）。"""
    return sorted(tools, key=lambda t: 0 if t.get("featured") else 1)


def join_names(names: list[str], limit: int = 3) -> str:
    head = " · ".join(names[:limit])
    return f"{head} 等" if len(names) > limit else head


def build_context(data: dict) -> dict:
    tools = data.get("tools", [])
    categories = data.get("categories", [])
    cat_labels = {c["id"]: c["label"] for c in categories}
    index = {t["id"]: t for t in tools}

    by_cat: dict[str, list[dict]] = {}
    for tool in tools:
        by_cat.setdefault(tool.get("cat", ""), []).append(tool)

    sections = []
    for category in categories:
        bucket = by_cat.get(category["id"], [])
        if not bucket:
            continue
        sections.append(
            {
                "key": category["id"],
                "title": category["label"],
                "desc": category.get("desc", ""),
                "count": len(bucket),
                "groups": [
                    {
                        "title": "",
                        "tools": [tool_view(t, cat_labels) for t in sort_tools(bucket)],
                    }
                ],
            }
        )

    featured_tools = [
        tool_view(t, cat_labels) for t in tools if t.get("featured")
    ][:FEATURED_IN_PANEL]
    for tool in featured_tools:
        tool["price_short"] = price_short(tool)

    picks = []
    for pick in data.get("picks", []):
        names = [index[i]["name"] for i in pick.get("tools", []) if i in index]
        picks.append(
            {
                "kicker": pick.get("kicker", ""),
                "title": pick.get("title", ""),
                "price": pick.get("price", ""),
                "why": pick.get("why", ""),
                "tool_names": join_names(names),
            }
        )

    free_paths = []
    for path in data.get("freePaths", []):
        ids = path.get("tools", [])
        names = [index[i]["name"] for i in ids if i in index]
        first = index.get(ids[0]) if ids else None
        free_paths.append(
            {
                "title": path.get("title", ""),
                "body": path.get("body", ""),
                "initial": initial(path.get("title")),
                "url": (first or {}).get("url", ""),
                "tool_count": len(names),
                "tool_names": join_names(names),
            }
        )

    promos = [
        {
            "tool": p.get("tool", ""),
            "title": p.get("title", ""),
            "body": p.get("body", ""),
            "deadline_label": p.get("deadlineLabel") or p.get("deadline", ""),
            "url": p.get("url", ""),
            "url_label": p.get("urlLabel", ""),
        }
        for p in data.get("promos", [])
    ]

    students = [
        {
            "tool": s.get("tool", ""),
            "benefit": s.get("benefit", ""),
            "url": s.get("url", ""),
            "url_label": s.get("urlLabel", ""),
        }
        for s in data.get("students", [])
    ]

    sources = [
        {"label": s.get("label", ""), "url": s.get("url", "")}
        for s in data.get("sources", [])
    ]

    verified = data.get("meta", {}).get("verified", "")
    last_label = verified.replace("-", " 年 ") + " 月" if "-" in verified else verified

    return {
        "total": len(tools),
        "cat_count": len(sections),
        "free_count": len(free_paths),
        "promo_count": len(promos),
        "last_label": last_label,
        "verified_time": last_label,
        "featured_tools": featured_tools,
        "picks": picks,
        "free_paths": free_paths,
        "matrix": data.get("matrix", []),
        "promos": promos,
        "expired": data.get("expired", []),
        "students": students,
        "rules": data.get("rules", []),
        "sources": sources,
        "sections": sections,
    }


def build_html(data: dict) -> str:
    return TEMPLATE_ENV.get_template("acd.html.j2").render(**build_context(data))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成 ai-coding-deals 静态页")
    parser.add_argument(
        "--check",
        action="store_true",
        help="只校验产物是否与数据源同步，不同步则退出码 1（供 CI 使用）",
    )
    args = parser.parse_args()

    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    html = build_html(data)
    current = OUT_FILE.read_text(encoding="utf-8") if OUT_FILE.exists() else None

    if args.check:
        if current == html:
            print(f"页面与数据源同步：{OUT_FILE.relative_to(ROOT)}")
            return 0
        print(
            "::error file=data/ai-coding-deals.json::ai-coding-deals/index.html 与数据源不同步。"
            "请在本地运行 python3 scripts/build_acd.py 后提交生成结果。",
            file=sys.stderr,
        )
        return 1

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    if current == html:
        print(f"页面未变化：{OUT_FILE.relative_to(ROOT)}")
    else:
        OUT_FILE.write_text(html, encoding="utf-8")
        print(f"页面已生成：{OUT_FILE.relative_to(ROOT)}")
    print(f"  - 工具 {len(data.get('tools', []))} 款 · 分类 {len(data.get('categories', []))} 类")
    print(f"  - 输出体积 {OUT_FILE.stat().st_size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
