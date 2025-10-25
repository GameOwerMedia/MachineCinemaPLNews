from __future__ import annotations
from typing import List, Dict

def to_md(items: List[Dict]) -> str:
    lines = []
    for it in items:
        t = it["title"].strip()
        s = it.get("summary","" ).strip()
        u = it["url"]
        lines.append(f"- **{t}** — {s} [Czytaj]({u})")
    return "\n".join(lines)

def to_html_page(date_str: str, title: str, banner: str, items: List[Dict], footer_links: list) -> str:
    lis = []
    for it in items:
        lis.append(f"""<li><a href=\"{it['url']}\" target=\"_blank\" rel=\"noopener\">{it['title']}</a>
        <span class=\"src\">({it.get('source','')})</span></li>""")
    links = " | ".join([f'<a href="{u}">{t}</a>' for t,u in footer_links])
    return f"""<!doctype html>
<html lang="pl">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>{title} — {date_str}</title>
<link rel="stylesheet" href="assets/custom.css" />
</head>
<body>
<header><h1>{banner}</h1><div class="date">{date_str}</div></header>
<main>
  <ul class="news">
    {''.join(lis)}
  </ul>
</main>
<footer>
  <nav>{links} | <a href="archive.html">Archiwum</a></nav>
</footer>
</body>
</html>"""
