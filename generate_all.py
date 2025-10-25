from __future__ import annotations
import os
from pathlib import Path

from utils import (ensure_dirs, load_config, today_pl_date, idempotent_guard_for_today,
                   read_json, write_json, now_pl, LOG)
from fetch_ai_news import fetch
from filters import is_relevant, dedup
from make_posts import to_md, to_html_page

def apply_seen(items, cfg):
    seen_path = cfg["seen_cache"]["path"]
    seen = read_json(seen_path, {})
    reset_env = cfg["seen_cache"].get("allow_reset_env")
    if reset_env and os.getenv(reset_env, "0") == "1":
        seen = {}
    ttl_days = cfg["seen_cache"]["ttl_days"]
    if ttl_days:
        cutoff = now_pl().timestamp() - (ttl_days*86400)
        seen = {k:v for k,v in seen.items() if v.get("ts",0) >= cutoff}

    out = []
    for it in items:
        url = it["url"]
        if url in seen:
            continue
        out.append(it)

    return out, seen

def commit_seen(items_to_record, cfg, prev):
    seen_path = cfg["seen_cache"]["path"]
    now = now_pl().timestamp()
    for it in items_to_record:
        prev[it["url"]] = {"ts": now}
    write_json(seen_path, prev)

def select_items(items, cfg):
    mode = cfg["newsletter"]["mode"]
    per_bucket = int(cfg["newsletter"]["per_bucket"])
    if mode == "top":
        # naive score (recent first), deterministic tie-break by URL
        items = sorted(items, key=lambda x: (x.get("published_at",""), x["url"]), reverse=True)
        return items[:max(per_bucket, cfg["newsletter"]["total_fallback"])]
    # segments (future: split by topic); for now, take first N deterministically
    items = sorted(items, key=lambda x: (x.get("topic",""), x.get("published_at",""), x["url"]), reverse=True)
    return items[:per_bucket]

def update_archive(date_str, title):
    arch = Path("site/archive.html")
    if arch.exists():
        html = arch.read_text(encoding="utf-8")
    else:
        html = """<!doctype html>\n<html lang=\"pl\">\n<head>\n<meta charset=\"utf-8\" />\n<title>Archiwum — Machine Cinema</title>\n<link rel=\"stylesheet\" href=\"assets/custom.css\" />\n</head>\n<body>\n<header><h1>Archiwum</h1></header>\n<main>\n<ul class=\"archive\">\n</ul>\n</main>\n</body>\n</html>\n"""
    # Insert newest on top of <ul class="archive">
    link = f'<li><a href="{date_str}.html">{date_str}</a></li>'
    if link in html:
        return
    html = html.replace('<ul class="archive">\n', '<ul class="archive">\n' + link + '\n')
    arch.write_text(html if html.endswith("\n") else html + "\n", encoding="utf-8")

def main():
    ensure_dirs()
    cfg = load_config()
    date_str = today_pl_date()

    # Idempotent guard at 09:00 PL
    if os.environ.get("FORCE_RUN","0") != "1" and idempotent_guard_for_today():
        LOG.info("Today’s issue already exists. Exiting.")
        return

    raw = fetch(cfg)
    raw = [it for it in raw if is_relevant(it)]
    raw = dedup(raw)

    # apply seen-cache before selection
    cand, prev_seen = apply_seen(raw, cfg)

    sel = select_items(cand, cfg)
    if not sel:
        LOG.warning("No items selected; aborting without writing outputs.")
        return

    # Write outputs
    out_md = Path(f"out/{date_str}_ALL.md")
    out_md.write_text(to_md(sel), encoding="utf-8")

    site_html = Path(f"site/{date_str}.html")
    page_html = to_html_page(date_str, cfg["html"]["title"], cfg["html"]["banner_text"], sel, cfg["html"]["footer_links"])
    site_html.write_text(page_html, encoding="utf-8")

    # Overwrite index.html
    Path("site/index.html").write_text(page_html, encoding="utf-8")

    # Update archive
    update_archive(date_str, cfg["html"]["title"])

    record_only = cfg["seen_cache"].get("record_only_published", True)
    items_for_cache = sel if record_only else cand
    commit_seen(items_for_cache, cfg, prev_seen)

    LOG.info("Wrote %s, %s, site/index.html and updated archive.", out_md, site_html)

if __name__ == "__main__":
    main()
