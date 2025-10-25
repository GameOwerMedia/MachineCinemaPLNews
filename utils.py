from __future__ import annotations
import json, os, hashlib, logging
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import urllib.parse as _up

LOG = logging.getLogger("mcpl")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

TZ = ZoneInfo("Europe/Warsaw")

def today_pl_date():
    return datetime.now(TZ).date().isoformat()

def now_pl():
    return datetime.now(TZ)

def ensure_dirs():
    for p in ["out", "site", "site/assets", "data"]:
        Path(p).mkdir(parents=True, exist_ok=True)

def read_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        LOG.warning("Failed reading %s: %s", path, e)
        return default

def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    tmp = f"{path}.tmp"
    Path(tmp).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)

def stable_hash(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:12]

def canonical_or_allowed(url: str) -> str:
    if not url:
        return url
    if "news.google." in url:
        try:
            parsed = _up.urlparse(url)
            qs = _up.parse_qs(parsed.query)
            cand = qs.get("url", [None])[0]
            if cand and cand.startswith(("http://", "https://")):
                return cand
        except Exception:
            pass
        return url
    try:
        p = _up.urlparse(url)
        cleaned_qs = _up.parse_qsl(p.query, keep_blank_values=False)
        cleaned_qs = [
            (k, v)
            for (k, v) in cleaned_qs
            if k.lower() not in {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content", "gclid", "fbclid"}
        ]
        new_query = _up.urlencode(cleaned_qs)
        return _up.urlunparse((p.scheme, p.netloc, p.path, p.params, new_query, p.fragment))
    except Exception:
        return url

def idempotent_guard_for_today():
    d = today_pl_date()
    target = Path(f"site/{d}.html")
    return target.exists()

def load_config():
    import yaml
    return yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))

def read_textfile(path: str) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
