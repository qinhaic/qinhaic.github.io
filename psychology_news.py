#!/usr/bin/env python3
"""每日国际心理学与心理治疗行业新闻推送 + 网页生成"""

import warnings
warnings.filterwarnings("ignore", category=Warning)

import smtplib
import urllib.request
import xml.etree.ElementTree as ET
import html as html_mod
import json
import os
import time
import re
from email.mime.text import MIMEText
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "email_config.json")
DIGEST_DIR = os.path.join(SCRIPT_DIR, "digest")


def load_config():
    with open(CONFIG_PATH) as f:
        return json.load(f)


def translate_text(text, retries=2):
    if not text or not text.strip():
        return ""
    try:
        from deep_translator import GoogleTranslator
        translator = GoogleTranslator(source="en", target="zh-CN")
        if len(text) > 4000:
            text = text[:4000]
        result = translator.translate(text)
        return result if result else ""
    except Exception as e:
        if retries > 0:
            time.sleep(2)
            return translate_text(text, retries - 1)
        return ""


def fetch_sciencedaily():
    url = "https://www.sciencedaily.com/rss/mind_brain.xml"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    root = ET.fromstring(resp.read())
    news = []
    for item in root.findall(".//item")[:10]:
        title = (item.find("title").text or "") if item.find("title") is not None else ""
        raw = (item.find("description").text or "") if item.find("description") is not None else ""
        desc = re.sub(r'<[^>]+>', '', raw)
        link = (item.find("link").text or "") if item.find("link") is not None else ""
        if not title:
            continue
        news.append({"title": title, "desc": desc, "link": link, "source": "ScienceDaily"})
    return news


def fetch_google_news():
    url = ("https://news.google.com/rss/search?"
           "q=psychotherapy+counseling+mental+health+psychology+therapy&"
           "hl=en-US&gl=US&ceid=US:en")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=15)
    root = ET.fromstring(resp.read())
    news = []
    for item in root.findall(".//item")[:10]:
        title = (item.find("title").text or "") if item.find("title") is not None else ""
        link = (item.find("link").text or "") if item.find("link") is not None else ""
        source = "Google News"
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            title = parts[0]
            source = parts[1]
        if not title:
            continue
        news.append({"title": title, "desc": "", "link": link, "source": source})
    return news


def esc(text):
    return html_mod.escape(text or "")


# ─── 邮件 HTML ───

def build_email_body(sci_news, ind_news):
    lines = ["""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,'Noto Sans SC','PingFang SC',sans-serif;padding:20px;max-width:700px;margin:0 auto;background:#f5f7fa;">
<div style="background:#fff;border-radius:12px;padding:32px;box-shadow:0 2px 8px rgba(0,0,0,0.06);">""",
    """<div style="text-align:center;margin-bottom:28px;">
<h2 style="color:#2c3e50;margin:0 0 4px 0;">🧠 国际心理学资讯速递</h2>
<p style="color:#95a5a6;font-size:13px;margin:0;">心理学研究 · 心理治疗 · 行业动态</p>
</div>"""
    ]
    _append_sci_section(lines, sci_news)
    _append_ind_section(lines, ind_news)
    lines.append(f"""<div style="text-align:center;padding-top:16px;border-top:1px solid #eee;">
<p style="color:#aaa;font-size:11px;margin:0;">每日自动推送 · {datetime.now().strftime('%Y-%m-%d')}</p>
</div></div></body></html>""")
    return "\n".join(lines)


def _append_sci_section(lines, news):
    if not news:
        return
    lines.append("""<div style="margin-bottom:28px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #3498db;">
<span style="font-size:18px;">🔬</span><h3 style="color:#2c3e50;margin:0;font-size:16px;">心理学与脑科学研究</h3>
</div>""")
    for i, item in enumerate(news, 1):
        t, d, l, s = esc(item["title"]), esc(item["desc"]), esc(item["link"]), esc(item["source"])
        tc = esc(translate_text(item["title"])) if item["title"] else ""
        lines.append(f"""<div style="margin-bottom:18px;padding:12px 14px;background:#f8f9fa;border-radius:8px;border-left:3px solid #3498db;">
<div style="display:flex;gap:8px;align-items:flex-start;">
<span style="background:#3498db;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;flex-shrink:0;">{i}</span>
<div style="flex:1;">
<strong style="font-size:14px;color:#2c3e50;">{t}</strong>""")
        if tc:
            lines.append(f'<p style="color:#555;font-size:13px;margin:4px 0 0 0;line-height:1.5;">📝 {tc}</p>')
        if d:
            lines.append(f'<p style="color:#777;font-size:12px;margin:4px 0 0 0;line-height:1.5;">{d[:200]}{"…" if len(d)>200 else ""}</p>')
        lines.append(f"""</div></div>
<div style="margin-top:6px;font-size:11px;text-align:right;">
<span style="background:#e8f4f8;padding:2px 6px;border-radius:3px;color:#2980b9;">{s}</span>""")
        if l:
            lines.append(f'<a href="{l}" style="color:#3498db;margin-left:6px;text-decoration:none;">阅读原文 →</a>')
        lines.append("</div></div>")
    lines.append("</div>")


def _append_ind_section(lines, news):
    if not news:
        return
    lines.append("""<div style="margin-bottom:28px;">
<div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #27ae60;">
<span style="font-size:18px;">💬</span><h3 style="color:#2c3e50;margin:0;font-size:16px;">心理咨询与治疗行业动态</h3>
</div>""")
    for i, item in enumerate(news, 1):
        t, l, s = esc(item["title"]), esc(item["link"]), esc(item["source"])
        tc = esc(translate_text(item["title"])) if item["title"] else ""
        lines.append(f"""<div style="margin-bottom:14px;padding:10px 14px;background:#f8f9fa;border-radius:8px;border-left:3px solid #27ae60;">
<div style="display:flex;gap:8px;align-items:flex-start;">
<span style="background:#27ae60;color:#fff;border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;flex-shrink:0;">{i}</span>
<div style="flex:1;">
<strong style="font-size:14px;color:#2c3e50;">{t}</strong>""")
        if tc:
            lines.append(f'<p style="color:#555;font-size:13px;margin:4px 0 0 0;line-height:1.5;">📝 {tc}</p>')
        lines.append(f"""</div></div>
<div style="margin-top:4px;font-size:11px;text-align:right;">
<span style="background:#e8f8ee;padding:2px 6px;border-radius:3px;color:#27ae60;">{s}</span>""")
        if l:
            lines.append(f'<a href="{l}" style="color:#27ae60;margin-left:6px;text-decoration:none;">阅读原文 →</a>')
        lines.append("</div></div>")
    lines.append("</div>")


# ─── 邮件发送 ───

def send_email(config, html_body, retries=3):
    msg = MIMEText(html_body, "html", "utf-8")
    msg["Subject"] = f"🧠 国际心理学资讯速递 ({datetime.now().strftime('%m/%d')})"
    msg["From"] = config["from_email"]
    msg["To"] = config["to_email"]
    last_err = None
    for attempt in range(retries):
        try:
            with smtplib.SMTP(config["smtp_server"], config["smtp_port"], timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(config["email"], config["password"])
                server.sendmail(config["from_email"], [config["to_email"]], msg.as_string())
                return
        except Exception as e:
            last_err = e
            if attempt < retries - 1:
                time.sleep(3)
    raise last_err


# ─── 网页生成 ───

def build_webpage(sci_news, ind_news, date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
    today_cn = datetime.now().strftime("%Y 年 %m 月 %d 日")

    items_html = []

    if sci_news:
        items_html.append("""<section class="section research">
<h2 class="section-title"><span class="icon">🔬</span> 心理学与脑科学研究</h2>""")
        for i, item in enumerate(sci_news, 1):
            t, d, l, s = esc(item["title"]), esc(item["desc"]), esc(item["link"]), esc(item["source"])
            tc = esc(translate_text(item["title"])) if item["title"] else ""
            items_html.append(f"""<article class="card research-card">
<div class="card-number">{i}</div>
<div class="card-body">
<h3 class="card-title">{t}</h3>""")
            if tc:
                items_html.append(f'<p class="card-trans">{tc}</p>')
            if d:
                items_html.append(f'<p class="card-desc">{d[:250]}{"…" if len(d)>250 else ""}</p>')
            items_html.append(f"""<div class="card-meta">
<span class="source-tag research-tag">{s}</span>
<a class="read-link research-link" href="{l}" target="_blank" rel="noopener">阅读原文 ↗</a>
</div></div></article>""")
        items_html.append("</section>")

    if ind_news:
        items_html.append("""<section class="section industry">
<h2 class="section-title"><span class="icon">💬</span> 心理咨询与治疗行业动态</h2>""")
        for i, item in enumerate(ind_news, 1):
            t, l, s = esc(item["title"]), esc(item["link"]), esc(item["source"])
            tc = esc(translate_text(item["title"])) if item["title"] else ""
            items_html.append(f"""<article class="card industry-card">
<div class="card-number">{i}</div>
<div class="card-body">
<h3 class="card-title">{t}</h3>""")
            if tc:
                items_html.append(f'<p class="card-trans">{tc}</p>')
            items_html.append(f"""<div class="card-meta">
<span class="source-tag industry-tag">{s}</span>
<a class="read-link industry-link" href="{l}" target="_blank" rel="noopener">阅读原文 ↗</a>
</div></div></article>""")
        items_html.append("</section>")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>国际心理学资讯速递 · {date_str}</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
  font-family: -apple-system, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  color: #2c3e50;
  line-height: 1.6;
  min-height: 100vh;
}}
.container {{ max-width: 800px; margin: 0 auto; padding: 32px 20px; }}
/* Header */
.header {{
  text-align: center;
  padding: 40px 0 32px;
  position: relative;
}}
.header::after {{
  content: '';
  display: block;
  width: 60px;
  height: 3px;
  background: linear-gradient(90deg, #3498db, #27ae60);
  margin: 20px auto 0;
  border-radius: 2px;
}}
.header h1 {{
  font-size: 24px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 6px;
}}
.header .subtitle {{
  font-size: 14px;
  color: #95a5a6;
}}
.header .date-badge {{
  display: inline-block;
  margin-top: 10px;
  padding: 4px 16px;
  background: #fff;
  border-radius: 20px;
  font-size: 13px;
  color: #7f8c8d;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}
/* Section */
.section {{ margin-top: 32px; }}
.section-title {{
  font-size: 17px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 16px;
  padding-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}}
.section-title .icon {{ font-size: 20px; }}
.research .section-title {{ border-bottom: 2px solid #3498db; }}
.industry .section-title {{ border-bottom: 2px solid #27ae60; }}
/* Card */
.card {{
  display: flex;
  gap: 14px;
  background: #fff;
  border-radius: 12px;
  padding: 18px 20px;
  margin-bottom: 14px;
  box-shadow: 0 1px 6px rgba(0,0,0,0.05);
  transition: transform 0.15s, box-shadow 0.15s;
}}
.card:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
.research-card {{ border-left: 3px solid #3498db; }}
.industry-card {{ border-left: 3px solid #27ae60; }}
.card-number {{
  flex-shrink: 0;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 700;
  color: #fff;
}}
.research-card .card-number {{ background: #3498db; }}
.industry-card .card-number {{ background: #27ae60; }}
.card-body {{ flex: 1; min-width: 0; }}
.card-title {{
  font-size: 14px;
  font-weight: 600;
  color: #1a1a2e;
  line-height: 1.5;
}}
.card-title a {{ color: inherit; text-decoration: none; }}
.card-title a:hover {{ color: #3498db; }}
.card-trans {{
  font-size: 13px;
  color: #555;
  margin-top: 6px;
  line-height: 1.6;
}}
.card-desc {{
  font-size: 12px;
  color: #888;
  margin-top: 6px;
  line-height: 1.6;
}}
.card-meta {{
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  font-size: 12px;
}}
.source-tag {{
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}}
.research-tag {{ background: #e8f4f8; color: #2980b9; }}
.industry-tag {{ background: #e8f8ee; color: #27ae60; }}
.read-link {{
  text-decoration: none;
  font-size: 12px;
  font-weight: 500;
  transition: opacity 0.15s;
}}
.read-link:hover {{ opacity: 0.7; }}
.research-link {{ color: #3498db; }}
.industry-link {{ color: #27ae60; }}
/* Footer */
.footer {{
  text-align: center;
  padding: 40px 0 20px;
  color: #bbb;
  font-size: 12px;
}}
.footer a {{ color: #95a5a6; text-decoration: none; }}
.footer a:hover {{ color: #3498db; }}
@media (max-width: 600px) {{
  .container {{ padding: 16px 12px; }}
  .card {{ padding: 14px 16px; }}
  .header h1 {{ font-size: 20px; }}
}}
</style>
</head>
<body>
<div class="container">
<header class="header">
<h1>🧠 国际心理学资讯速递</h1>
<p class="subtitle">心理学研究 · 心理咨询 · 心理治疗 · 行业动态</p>
<div class="date-badge">{today_cn}</div>
</header>
{"".join(items_html)}
<footer class="footer">
<p>每日自动更新 · 来源：ScienceDaily / Google News</p>
<p style="margin-top:4px;"><a href="#">返回顶部 ↑</a></p>
</footer>
</div>
</body>
</html>"""
    return html


def save_webpage(html):
    os.makedirs(DIGEST_DIR, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    filename = f"{date_str}.html"
    filepath = os.path.join(DIGEST_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    return filepath, date_str


def build_index_page(digests):
    """生成 digest 索引页，列出所有历史 digest"""
    cards = []
    for d in digests:
        cards.append(f"""<a href="{d['file']}" class="digest-card">
  <div class="digest-date">{d['date']}</div>
  <div class="digest-count">{d['count']} 条资讯</div>
</a>""")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>心理学资讯速递 · 每日荟萃</title>
<style>
*,*::before,*::after {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
  font-family: -apple-system, "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf1 100%);
  color: #2c3e50;
  min-height: 100vh;
}}
.container {{ max-width: 700px; margin: 0 auto; padding: 40px 20px; }}
.header {{ text-align: center; padding: 30px 0; }}
.header h1 {{ font-size: 26px; color: #1a1a2e; }}
.header p {{ color: #95a5a6; margin-top: 8px; font-size: 14px; }}
.archive {{ display: grid; gap: 12px; margin-top: 24px; }}
.digest-card {{
  display: flex; justify-content: space-between; align-items: center;
  background: #fff; border-radius: 10px; padding: 16px 20px;
  text-decoration: none; color: inherit;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  transition: transform 0.15s, box-shadow 0.15s;
}}
.digest-card:hover {{ transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
.digest-date {{ font-size: 15px; font-weight: 600; color: #2c3e50; }}
.digest-count {{ font-size: 13px; color: #95a5a6; }}
.empty {{ text-align: center; color: #bbb; padding: 60px 0; font-size: 14px; }}
.footer {{ text-align: center; padding: 40px 0; color: #ccc; font-size: 12px; }}
</style>
</head>
<body>
<div class="container">
<div class="header">
<h1>🧠 国际心理学资讯速递</h1>
<p>每日荟萃 · 心理学研究 / 心理咨询 / 治疗行业动态</p>
</div>
<div class="archive">
{"".join(cards) if cards else '<div class="empty">暂无内容</div>'}
</div>
<div class="footer"><p>每日自动更新</p></div>
</div>
</body>
</html>"""
    return html


def update_index_page(date_str, sci_count, ind_count):
    """重新生成索引页"""
    files = []
    if os.path.isdir(DIGEST_DIR):
        for f in sorted(os.listdir(DIGEST_DIR), reverse=True):
            if f.endswith(".html") and f != "index.html":
                files.append(f)
    digests = []
    for f in files:
        fpath = os.path.join(DIGEST_DIR, f)
        size = os.path.getsize(fpath) if os.path.isfile(fpath) else 0
        # 估算条数: 约 1KB 一条
        est = max(10, size // 1000)
        digests.append({
            "file": f,
            "date": f.replace(".html", ""),
            "count": est
        })
    # 确保当前日期在列表里
    date_exists = any(d["date"] == date_str for d in digests)
    if not date_exists:
        digests.insert(0, {"file": f"{date_str}.html", "date": date_str, "count": sci_count + ind_count})
    index_html = build_index_page(digests)
    indexPath = os.path.join(DIGEST_DIR, "index.html")
    with open(indexPath, "w", encoding="utf-8") as f:
        f.write(index_html)
    return indexPath


def git_push():
    """提交并推送到 GitHub Pages"""
    import subprocess
    repo_dir = SCRIPT_DIR
    try:
        subprocess.run(["git", "-C", repo_dir, "add", "digest/"], capture_output=True, check=True)
        subprocess.run(["git", "-C", repo_dir, "diff", "--cached", "--quiet"], capture_output=True, check=True)
        # 没有变更，跳过
        return False
    except subprocess.CalledProcessError:
        pass
    try:
        subprocess.run(
            ["git", "-C", repo_dir, "commit", "-m", f"📰 每日心理学资讯 {datetime.now().strftime('%Y-%m-%d')}"],
            capture_output=True, check=True
        )
        subprocess.run(["git", "-C", repo_dir, "push"], capture_output=True, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ⚠️ Git 操作失败: {e.stderr.decode() if e.stderr else str(e)}")
        return False


# ─── 主流程 ───

def main():
    config = load_config()
    print("📡 正在获取心理学研究新闻...")
    sci_news = fetch_sciencedaily()
    print(f"   获取到 {len(sci_news)} 条研究新闻")
    print("📡 正在获取行业动态...")
    ind_news = fetch_google_news()
    print(f"   获取到 {len(ind_news)} 条行业动态")

    print("🔄 正在翻译并生成内容...")
    email_body = build_email_body(sci_news, ind_news)
    webpage_html = build_webpage(sci_news, ind_news)

    print("📧 正在发送邮件...")
    send_email(config, email_body)
    print(f"✅ 邮件已发送至 {config['to_email']}")

    filepath, date_str = save_webpage(webpage_html)
    print(f"✅ 网页已生成: {filepath}")

    indexPath = update_index_page(date_str, len(sci_news), len(ind_news))
    print(f"✅ 索引页已更新: {indexPath}")

    print("📤 正在推送到 GitHub Pages...")
    pushed = git_push()
    if pushed:
        print(f"✅ 已发布到 https://qinhaic.github.io/digest/")
    else:
        print(f"   digest 已是最新，无需推送")

    total = len(sci_news) + len(ind_news)
    print(f"📊 共 {total} 条资讯")


if __name__ == "__main__":
    main()
