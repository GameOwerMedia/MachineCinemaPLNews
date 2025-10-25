from __future__ import annotations
from typing import List, Dict
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import feedparser

from utils import LOG, canonical_or_allowed, now_pl

TZ = ZoneInfo("Europe/Warsaw")

RSS_FEEDS = [
    "https://news.google.com/rss/search?q=sztuczna%20inteligencja&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=AI%20technologia&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=uczenie%20maszynowe&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=genAI%20OR%20\"generatywna%20sztuczna%20inteligencja\"&hl=pl&gl=PL&ceid=PL:pl",
    "https://news.google.com/rss/search?q=OpenAI%20OR%20Anthropic%20OR%20Google%20AI%20OR%20Meta%20AI%20OR%20Hugging%20Face&hl=pl&gl=PL&ceid=PL:pl",
]


def _live_fetch_24h(window_hours: int) -> List[Dict]:
    cutoff = now_pl() - timedelta(hours=window_hours)
    out: List[Dict] = []
    for url in RSS_FEEDS:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:50]:
                link = entry.get("link") or entry.get("id") or ""
                title = (entry.get("title") or "").strip()
                summary = (entry.get("summary") or entry.get("description") or "").strip()
                dt = None
                if getattr(entry, "published_parsed", None):
                    dt = datetime(*entry.published_parsed[:6], tzinfo=TZ)
                elif getattr(entry, "updated_parsed", None):
                    dt = datetime(*entry.updated_parsed[:6], tzinfo=TZ)
                else:
                    dt = now_pl()
                if dt < cutoff:
                    continue
                out.append(
                    {
                        "title": title,
                        "summary": summary,
                        "url": canonical_or_allowed(link),
                        "source": feed.feed.get("title", "Google News"),
                        "published_at": dt.isoformat(),
                        "topic": "Ogólne",
                    }
                )
        except Exception as ex:
            LOG.warning("RSS fetch failed for %s: %s", url, ex)
    return out


def _load_curated() -> List[Dict]:
    import json
    from pathlib import Path

    p = Path("data/curated.json")
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def normalize(items: List[Dict]) -> List[Dict]:
    out: List[Dict] = []
    for it in items:
        url = canonical_or_allowed((it.get("url") or "").strip())
        if not url:
            continue
        out.append(
            {
                "title": (it.get("title") or "").strip(),
                "summary": (it.get("summary") or "").strip(),
                "url": url,
                "source": (it.get("source") or "unknown").strip(),
                "published_at": it.get("published_at") or now_pl().isoformat(),
                "topic": it.get("topic") or "Ogólne",
            }
        )
    return out


def fetch(config) -> List[Dict]:
    items: List[Dict] = []
    if config["sources"]["live_enabled"]:
        items = _live_fetch_24h(int(config["time"]["window_hours"]))
    if not items and config["sources"]["curated_first"]:
        items = _load_curated()
    return normalize(items)
