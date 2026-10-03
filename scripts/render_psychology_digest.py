#!/usr/bin/env python3
"""Render a psychology-industry digest from a reviewed JSON file.

Input schema:
{
  "date": "YYYY-MM-DD",
  "coverage": "过去36小时",
  "international": [
    {
      "title": "中文标题",
      "summary": "60—120字摘要",
      "source": "来源名称",
      "published_at": "YYYY-MM-DD",
      "url": "https://...",
      "topic": "政策与监管"
    }
  ],
  "domestic": [ ... ]
}
"""

from __future__ import annotations

import argparse
import html
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


REPO_DIR = Path(__file__).resolve().parent.parent
DIGEST_DIR = REPO_DIR / "digest"
DATA_DIR = DIGEST_DIR / "data"
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def esc(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def load_and_validate(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    date = data.get("date", "")
    if not DATE_RE.match(date):
        raise ValueError("date 必须使用 YYYY-MM-DD")
    datetime.strptime(date, "%Y-%m-%d")

    seen_urls: set[str] = set()
    for section in ("international", "domestic"):
        items = data.get(section)
        if not isinstance(items, list):
            raise ValueError(f"{section} 必须是列表")
        for number, item in enumerate(items, 1):
            missing = [key for key in ("title", "summary", "source", "published_at", "url") if not item.get(key)]
            if missing:
                raise ValueError(f"{section} 第 {number} 条缺少：{', '.join(missing)}")
            parsed = urlparse(item["url"])
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(f"{section} 第 {number} 条 URL 无效")
            normalized = item["url"].rstrip("/")
            if normalized in seen_urls:
                raise ValueError(f"重复 URL：{item['url']}")
            seen_urls.add(normalized)

    if not data["international"] and not data["domestic"]:
        raise ValueError("本期没有可发布内容")
    return data


def render_cards(items: list[dict], accent: str) -> str:
    cards = []
    for index, item in enumerate(items, 1):
        topic = item.get("topic") or "行业动态"
        cards.append(f"""
<article class="card" style="--accent:{accent}">
  <div class="number">{index}</div>
  <div class="content">
    <div class="eyebrow">{esc(topic)} · {esc(item['published_at'])}</div>
    <h3>{esc(item['title'])}</h3>
    <p>{esc(item['summary'])}</p>
    <div class="meta"><span>{esc(item['source'])}</span><a href="{esc(item['url'])}" target="_blank" rel="noopener noreferrer">查看原文 ↗</a></div>
  </div>
</article>""")
    return "".join(cards) if cards else '<p class="empty">本期没有符合收录标准的新动态。</p>'


def render_page(data: dict) -> str:
    date = data["date"]
    display_date = datetime.strptime(date, "%Y-%m-%d").strftime("%Y 年 %m 月 %d 日")
    coverage = esc(data.get("coverage") or "过去 36 小时")
    return f"""<!DOCTYPE html>
<html lang="zh-CN"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>心理行业每日动态 · {date}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#f3f5f7;color:#24313b;font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.65}}
.wrap{{max-width:860px;margin:auto;padding:42px 18px 60px}} header{{background:#132d36;color:white;border-radius:18px;padding:38px 34px;box-shadow:0 14px 36px #1233}}
.kicker{{color:#9ed6cf;font-size:13px;letter-spacing:.12em}} h1{{font-size:29px;margin:8px 0 6px}} header p{{margin:0;color:#d5e5e7;font-size:14px}} .date{{display:inline-block;margin-top:18px;padding:6px 12px;border:1px solid #ffffff38;border-radius:999px;font-size:13px}}
section{{margin-top:34px}} h2{{font-size:19px;margin:0 0 14px;display:flex;align-items:center;gap:9px}} h2:after{{content:"";height:1px;background:#ccd4d7;flex:1}}
.card{{--accent:#287d8e;display:flex;gap:15px;background:white;border-radius:13px;margin:0 0 13px;padding:20px;border-left:4px solid var(--accent);box-shadow:0 2px 10px #17313b0c}}
.number{{width:28px;height:28px;border-radius:50%;background:var(--accent);color:white;display:grid;place-items:center;font-size:13px;font-weight:700;flex:none}}
.content{{min-width:0;flex:1}} .eyebrow{{font-size:11px;color:#7b8b91;margin-bottom:3px}} h3{{font-size:16px;line-height:1.45;margin:0;color:#17272d}} .card p{{font-size:14px;margin:8px 0 12px;color:#4e5e64}}
.meta{{display:flex;align-items:center;justify-content:space-between;gap:12px;font-size:12px;color:#75858a}} a{{color:var(--accent);text-decoration:none;font-weight:600}} .empty{{color:#89969a;background:white;padding:18px;border-radius:10px}}
footer{{margin-top:38px;text-align:center;color:#849398;font-size:12px}} footer a{{color:#526e77}} @media(max-width:600px){{header{{padding:30px 22px}}h1{{font-size:24px}}.card{{padding:17px 15px}}.meta{{align-items:flex-start;flex-direction:column;gap:4px}}}}
</style></head><body><main class="wrap">
<header><div class="kicker">PSYCHOLOGY INDUSTRY BRIEFING</div><h1>心理行业每日动态</h1><p>国际视野 · 国内现场 · 政策、机构、服务与专业实践</p><div class="date">{display_date} · 覆盖 {coverage}</div></header>
<section><h2>🌍 国际动态</h2>{render_cards(data['international'], '#287d8e')}</section>
<section><h2>🇨🇳 国内动态</h2>{render_cards(data['domestic'], '#b56b3d')}</section>
<footer><p>工作日北京时间 06:00 更新 · 内容仅作行业信息参考</p><p><a href="index.html">查看历史归档</a> · <a href="../index.html">返回首页</a></p></footer>
</main></body></html>"""


def count_items(path: Path) -> int:
    data_path = DATA_DIR / f"{path.stem}.json"
    if data_path.exists():
        try:
            data = json.loads(data_path.read_text(encoding="utf-8"))
            return len(data.get("international", [])) + len(data.get("domestic", []))
        except (OSError, json.JSONDecodeError):
            pass
    text = path.read_text(encoding="utf-8", errors="ignore")
    return max(text.count('class="card '), text.count('class="card"'))


def render_index() -> str:
    entries = []
    for page in sorted(DIGEST_DIR.glob("20??-??-??.html"), reverse=True):
        entries.append((page.name, page.stem, count_items(page)))
    cards = "".join(
        f'<a class="item" href="{esc(name)}"><strong>{esc(date)}</strong><span>{count} 条动态</span></a>'
        for name, date, count in entries
    )
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>心理行业每日动态 · 历史归档</title>
<style>*{{box-sizing:border-box}}body{{margin:0;background:#f3f5f7;color:#24313b;font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}main{{max-width:720px;margin:auto;padding:55px 18px}}header{{margin-bottom:28px}}h1{{margin:0 0 7px;font-size:27px}}p{{color:#748389}}.list{{display:grid;gap:10px}}.item{{display:flex;justify-content:space-between;background:white;padding:17px 19px;border-radius:11px;color:#24313b;text-decoration:none;box-shadow:0 2px 9px #17313b0c}}.item span{{color:#849398;font-size:13px}}footer{{text-align:center;margin-top:36px}}footer a{{color:#287d8e;text-decoration:none}}</style></head><body><main><header><h1>🧠 心理行业每日动态</h1><p>国际与国内心理行业资讯归档</p></header><div class="list">{cards}</div><footer><a href="../index.html">返回首页</a></footer></main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    source = args.input.resolve()
    data = load_and_validate(source)
    DIGEST_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    expected_data_path = DATA_DIR / f"{data['date']}.json"
    if source != expected_data_path.resolve():
        expected_data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    page_name = f"{data['date']}.html"
    (DIGEST_DIR / page_name).write_text(render_page(data), encoding="utf-8")
    (DIGEST_DIR / "today.html").write_text(
        f'<!DOCTYPE html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={page_name}"></head><body><p>跳转至 <a href="{page_name}">今日心理行业动态</a>…</p></body></html>\n',
        encoding="utf-8",
    )
    (DIGEST_DIR / "index.html").write_text(render_index(), encoding="utf-8")
    print(f"Rendered {page_name}: {len(data['international'])} international, {len(data['domestic'])} domestic")


if __name__ == "__main__":
    main()
