import os
import sys
from pathlib import Path
import yaml
import importlib

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_config_loads():
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    assert "newsletter" in cfg


def test_guard_and_paths():
    for module in ("generate_all", "make_posts", "fetch_ai_news", "filters", "utils"):
        importlib.import_module(module)


def test_idempotent_and_archive(monkeypatch):
    from generate_all import main as generate
    import fetch_ai_news

    class DummyFeed:
        entries: list = []

        def __init__(self):
            self.entries = []
            self.feed = {"title": "Dummy"}

    monkeypatch.setattr(fetch_ai_news, "feedparser", type("FP", (), {"parse": staticmethod(lambda url: DummyFeed())}))

    seen_path = Path("data/seen.json")
    original_seen = seen_path.read_text(encoding="utf-8") if seen_path.exists() else None

    for path in ["out", "site"]:
        if Path(path).exists():
            for target in Path(path).glob("*"):
                if target.is_file() and target.name != ".nojekyll":
                    target.unlink()

    os.environ["FORCE_RUN"] = "1"
    os.environ["RESET_SEEN"] = "1"
    generate()

    archive = Path("site/archive.html").read_text(encoding="utf-8")
    first_listing = sorted(p.name for p in Path("site").glob("*.html"))

    os.environ.pop("FORCE_RUN", None)
    os.environ["RESET_SEEN"] = "0"
    generate()

    archive_again = Path("site/archive.html").read_text(encoding="utf-8")
    second_listing = sorted(p.name for p in Path("site").glob("*.html"))

    assert archive == archive_again
    assert first_listing == second_listing

    os.environ.pop("RESET_SEEN", None)

    if original_seen is None:
        if seen_path.exists():
            seen_path.unlink()
    else:
        seen_path.write_text(original_seen, encoding="utf-8")
