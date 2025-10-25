import os
import sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

def test_config_loads():
    cfg = yaml.safe_load(Path("config.yaml").read_text(encoding="utf-8"))
    assert "newsletter" in cfg

def test_guard_and_paths():
    # dry run should be importable without executing
    import generate_all, make_posts, fetch_ai_news, filters, utils
    assert hasattr(utils, "today_pl_date")
