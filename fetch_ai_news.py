from __future__ import annotations
import logging, time
from typing import List, Dict
from utils import LOG, canonical_or_allowed, now_pl

# Minimal implementation: two pathways:
# 1) Live fetch (placeholder - TODO wire real feeds/APIs)
# 2) Curated fallback (data/curated.json)

def _fake_live() -> List[Dict]:
    # Placeholder live fetch – returns empty to trigger curated during Slice 1
    LOG.info("Live fetch not yet configured; returning empty set.")
    return []

def _load_curated() -> List[Dict]:
    import json
    from pathlib import Path
    p = Path("data/curated.json")
    if not p.exists():
        return []
    data = json.loads(p.read_text(encoding="utf-8"))
    return data

def normalize(items: List[Dict]) -> List[Dict]:
    out = []
    for it in items:
        url = canonical_or_allowed(it.get("url","" ).strip())
        if not url:
            continue
        out.append({
            "title": it.get("title","" ).strip(),
            "summary": it.get("summary","" ).strip(),
            "url": url,
            "source": it.get("source","" ).strip() or "unknown",
            "published_at": it.get("published_at") or now_pl().isoformat(),
            "topic": it.get("topic") or "Ogólne",
        })
    return out

def fetch(config) -> List[Dict]:
    items: List[Dict] = []
    if config["sources"]["live_enabled"]:
        items = _fake_live()
    if not items and config["sources"]["curated_first"]:
        items = _load_curated()
    return normalize(items)
