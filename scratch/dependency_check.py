import json
import os
import platform
import subprocess
import sys
import textwrap
from pathlib import Path
from urllib import request, error

BASE_DIR = Path(__file__).resolve().parents[1]
SCRATCH = BASE_DIR / "scratch"
PROBES_DIR = SCRATCH / "probes"
REPORTS_DIR = BASE_DIR / "reports"
VENv_DIR = SCRATCH / "venv"

PYPI_PACKAGES = [
    {"name": "feedparser", "pip": "feedparser", "import": "feedparser"},
    {"name": "trafilatura", "pip": "trafilatura", "import": "trafilatura"},
    {"name": "readability-lxml", "pip": "readability-lxml", "import": "readability"},
    {"name": "newspaper4k[gnews]", "pip": "newspaper4k[gnews]", "import": "newspaper"},
    {"name": "tldextract", "pip": "tldextract", "import": "tldextract"},
    {"name": "url-normalize", "pip": "url-normalize", "import": "url_normalize"},
    {"name": "rapidfuzz", "pip": "rapidfuzz", "import": "rapidfuzz"},
    {"name": "datasketch", "pip": "datasketch", "import": "datasketch"},
    {"name": "sentence-transformers", "pip": "sentence-transformers", "import": "sentence_transformers"},
    {"name": "requests-cache", "pip": "requests-cache", "import": "requests_cache"},
]

HF_MODELS = [
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    "intfloat/multilingual-e5-base",
]

REPORTS_DIR.mkdir(exist_ok=True)
PROBES_DIR.mkdir(exist_ok=True)


def run(cmd, timeout=60):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(cmd, returncode=124, stdout=getattr(exc, "stdout", "") or "", stderr=(getattr(exc, "stderr", "") or "") + f"\nTIMEOUT after {timeout}s")


def ensure_venv():
    created = False
    if not VENv_DIR.exists():
        run([sys.executable, "-m", "venv", str(VENv_DIR)], timeout=120).check_returncode()
        created = True
    python = VENv_DIR / "bin" / "python"
    pip = VENv_DIR / "bin" / "pip"
    if not python.exists():
        raise RuntimeError("Virtualenv python not found")
    return created, str(python), str(pip)


def detect_online():
    try:
        req = request.Request("https://pypi.org/simple/", method="HEAD")
        with request.urlopen(req, timeout=5) as resp:
            return resp.status < 500
    except Exception:
        return False


def check_import(python, module):
    code = textwrap.dedent(
        f"""
        import importlib, json
        try:
            mod = importlib.import_module('{module}')
            ver = getattr(mod, '__version__', getattr(mod, 'VERSION', 'unknown'))
            print(json.dumps({{"ok": True, "version": str(ver)}}))
        except Exception as exc:
            print(json.dumps({{"ok": False, "error": str(exc)}}))
        """
    )
    res = run([python, "-c", code])
    data = json.loads(res.stdout.strip() or '{}')
    return data


def install_package(pip, pkg):
    cmd = [
        pip,
        "install",
        "--disable-pip-version-check",
        "--no-input",
        "--quiet",
        pkg,
    ]
    return run(cmd, timeout=60)


def main():
    python_version = sys.version.replace("\n", " ")
    os_name = platform.platform()
    online = detect_online()
    venv_created, vpython, vpip = ensure_venv()

    env_info = {
        "python": python_version,
        "os": os_name,
        "online": online,
        "pip_method": "venv" + (" (new)" if venv_created else " (existing)"),
    }

    pypi_results = []
    for pkg in PYPI_PACKAGES:
        print(f"[PyPI] Installing {pkg['name']}...")
        sys.stdout.flush()
        result = {
            "name": pkg["name"],
            "status": "N/A (env)" if not online else "",  # fill later
            "version": None,
            "import_ok": None,
            "notes": "",
        }
        if not online:
            result["notes"] = "offline"
            pypi_results.append(result)
            continue
        install_res = install_package(vpip, pkg["pip"])
        if install_res.returncode != 0:
            result["status"] = "failed"
            result["notes"] = install_res.stderr.strip()[-200:]
            result["import_ok"] = False
        else:
            result["status"] = "installed"
            import_data = check_import(vpython, pkg["import"])
            if import_data.get("ok"):
                result["import_ok"] = True
                result["version"] = import_data.get("version")
            else:
                result["import_ok"] = False
                result["notes"] = import_data.get("error")
        pypi_results.append(result)

    hf_results = []
    if online:
        for model in HF_MODELS:
            print(f"[HF] Loading {model}...")
            sys.stdout.flush()
            status = {"model": model, "status": "fail", "notes": ""}
            code = textwrap.dedent(
                f"""
                from sentence_transformers import SentenceTransformer
                model_name = '{model}'
                try:
                    SentenceTransformer(model_name, device='cpu')
                    print('ok')
                except Exception as exc:
                    print('fail:' + type(exc).__name__ + ':' + str(exc))
                """
            )
            res = run([vpython, "-c", code], timeout=120)
            out = res.stdout.strip()
            if out.startswith("ok"):
                status["status"] = "ok"
            elif out.startswith("fail:"):
                status["notes"] = out[5:]
            else:
                status["notes"] = out or res.stderr.strip()
            hf_results.append(status)
    else:
        for model in HF_MODELS:
            hf_results.append({"model": model, "status": "N/A (env)", "notes": "offline"})

    probe_notes = []

    def write_and_run_probe(name, code, required):
        script_path = PROBES_DIR / f"{name}.py"
        script_path.write_text(code, encoding="utf-8")
        res = run([vpython, str(script_path)], timeout=30)
        output = res.stdout.strip()
        err = res.stderr.strip()
        note = f"{name}: {'OK' if res.returncode == 0 else 'ERR'}"
        if output:
            note += f" | stdout: {output}"
        if err:
            note += f" | stderr: {err}"
        probe_notes.append(note)

    installed = {p["name"]: p for p in pypi_results if p["status"] == "installed" and p.get("import_ok")}

    if installed.get("url-normalize") and installed.get("tldextract"):
        code = textwrap.dedent(
            """
            from url_normalize import url_normalize
            import tldextract
            urls = [
                'HTTPS://Example.com:80/path?utm_source=test',
                'https://news.google.com/articles/CBMiN2h0dHBzOi8vZXhhbXBsZS5jb20vbmV3cz9ocmVmPXJzcy0x0gEA'
            ]
            normalized = [url_normalize(u) for u in urls]
            domains = [tldextract.extract(u).registered_domain for u in normalized]
            print(' | '.join(domains))
            """
        )
        write_and_run_probe("url_normalize_tldextract", code, ["url-normalize", "tldextract"])
    else:
        probe_notes.append("url_normalize_tldextract: skipped (dependency missing)")

    if installed.get("newspaper4k[gnews]"):
        code = textwrap.dedent(
            """
            from newspaper import Article
            url = 'https://news.google.com/rss/articles/CBMiRmh0dHBzOi8vZXhhbXBsZS5jb20vYXJ0aWNsZS_SAQA?hl=pl&gl=PL&ceid=PL:pl'
            art = Article(url)
            print(art.source_url)
            """
        )
        write_and_run_probe("newspaper_gnews", code, ["newspaper4k[gnews]"])
    else:
        probe_notes.append("newspaper_gnews: skipped (dependency missing)")

    if installed.get("trafilatura"):
        code = textwrap.dedent(
            """
            import trafilatura
            html = '<html><body><article><p>To jest test.</p></article></body></html>'
            text = trafilatura.extract(html)
            print((text or '').strip())
            """
        )
        write_and_run_probe("trafilatura_extract", code, ["trafilatura"])
    else:
        probe_notes.append("trafilatura_extract: skipped (dependency missing)")

    if installed.get("rapidfuzz"):
        code = textwrap.dedent(
            """
            from rapidfuzz import fuzz
            s1 = 'OpenAI ogłasza nowy model'
            s2 = 'OpenAI zapowiada nowy model'
            print(fuzz.ratio(s1, s2))
            """
        )
        write_and_run_probe("rapidfuzz_ratio", code, ["rapidfuzz"])
    else:
        probe_notes.append("rapidfuzz_ratio: skipped (dependency missing)")

    if installed.get("datasketch"):
        code = textwrap.dedent(
            """
            from datasketch import MinHash
            tokens_a = {'openai', 'anthropic', 'meta'}
            tokens_b = {'openai', 'meta', 'google'}
            m1, m2 = MinHash(), MinHash()
            for t in tokens_a:
                m1.update(t.encode('utf-8'))
            for t in tokens_b:
                m2.update(t.encode('utf-8'))
            print(round(m1.jaccard(m2), 3))
            """
        )
        write_and_run_probe("datasketch_minhash", code, ["datasketch"])
    else:
        probe_notes.append("datasketch_minhash: skipped (dependency missing)")

    if installed.get("requests-cache"):
        code = textwrap.dedent(
            """
            import requests_cache
            session = requests_cache.CachedSession('scratch/cache', expire_after=1800)
            cache = getattr(session, 'cache', None)
            name = getattr(session, 'cache_name', None)
            if not name and cache is not None:
                name = getattr(cache, 'cache_name', None) or cache.__class__.__name__
            print('backend:', name)
            """
        )
        write_and_run_probe("requests_cache_session", code, ["requests-cache"])
    else:
        probe_notes.append("requests_cache_session: skipped (dependency missing)")

    report = {
        "env": env_info,
        "pypi": pypi_results,
        "hf": hf_results,
        "probes": probe_notes,
    }

    REPORTS_DIR.mkdir(exist_ok=True)
    (REPORTS_DIR / "dependency_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    def format_table(rows, headers):
        out = [' | '.join(headers), ' | '.join(['---'] * len(headers))]
        out.extend(' | '.join(str(row.get(h.lower(), '')) for h in headers) for row in rows)
        return '\n'.join(out)

    pypi_rows = []
    for item in pypi_results:
        pypi_rows.append({
            'name': item['name'],
            'status': item['status'],
            'version': item.get('version') or '',
            'import_ok': item.get('import_ok'),
            'notes': item.get('notes', '')[:120],
        })

    hf_rows = []
    for item in hf_results:
        hf_rows.append({
            'model': item['model'],
            'status': item['status'],
            'notes': item.get('notes', '')[:200],
        })

    report_md = []
    report_md.append("# Dependency & Model Check Report")
    report_md.append("")
    report_md.append(f"- Python: {env_info['python']}")
    report_md.append(f"- OS: {env_info['os']}")
    report_md.append(f"- Online: {env_info['online']}")
    report_md.append(f"- pip method: {env_info['pip_method']}")
    report_md.append("")
    report_md.append("## PyPI Packages")
    report_md.append("")
    report_md.append(format_table(pypi_rows, ["name", "status", "version", "import_ok", "notes"]))
    report_md.append("")
    report_md.append("## Hugging Face Models")
    report_md.append("")
    report_md.append(format_table(hf_rows, ["model", "status", "notes"]))
    report_md.append("")
    report_md.append("## Integration Probes")
    report_md.append("")
    for note in probe_notes:
        report_md.append(f"- {note}")
    report_md.append("")
    ok_ready = [p['name'] for p in pypi_results if p['status'] == 'installed' and p.get('import_ok')]
    not_ready = [p['name'] for p in pypi_results if p['status'] != 'installed']
    report_md.append("## Recommendations")
    report_md.append("")
    report_md.append("### Ready now")
    report_md.append("")
    report_md.append("- " + (", ".join(ok_ready) if ok_ready else "None"))
    report_md.append("")
    report_md.append("### Require attention")
    report_md.append("")
    if not_ready:
        for name in not_ready:
            matching = next((p for p in pypi_results if p['name'] == name), None)
            note = matching.get('notes', '') if matching else ''
            report_md.append(f"- {name}: {note or 'check installation logs'}")
    else:
        report_md.append("- None")
    report_md.append("")
    if ok_ready:
        report_md.append("### Suggested requirements.txt block")
        report_md.append("")
        for name in ok_ready:
            base = name.split('[')[0]
            report_md.append(base)
        report_md.append("")

    (REPORTS_DIR / "dependency_report.md").write_text('\n'.join(report_md), encoding="utf-8")

    ok_pypi = sum(1 for p in pypi_results if p['status'] == 'installed' and p.get('import_ok'))
    fail_pypi = sum(1 for p in pypi_results if p['status'] == 'failed')
    na_pypi = sum(1 for p in pypi_results if p['status'].startswith('N/A'))

    ok_hf = sum(1 for h in hf_results if h['status'] == 'ok')
    fail_hf = sum(1 for h in hf_results if h['status'] == 'fail')
    na_hf = sum(1 for h in hf_results if h['status'].startswith('N/A'))

    summary = {
        'PyPI': {'ok': ok_pypi, 'fail': fail_pypi, 'na': na_pypi},
        'HF': {'ok': ok_hf, 'fail': fail_hf, 'na': na_hf},
    }

    print(json.dumps(summary))


if __name__ == "__main__":
    main()
