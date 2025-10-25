# MachineCinemaPLNews

Daily static newsletter in Polish about AI. Builds at **09:00 Europe/Warsaw**, outputs HTML to `/site` and appends to `/site/archive.html`. Deploys via GitHub Pages.

## Quickstart

```bash
python -m pip install pyyaml
python generate_all.py
# outputs: out/YYYY-MM-DD_ALL.md, site/YYYY-MM-DD.html, site/index.html, site/archive.html
```

## Config

Configuration lives in `config.yaml`.

- `newsletter.mode`: `top` or `segments`
- `newsletter.per_bucket`: default 5
- `seen_cache.record_only_published`: true by default
- `link_policy.allow_google_news`: true (never strip uncertain links)

## CI

- `.github/workflows/daily-0900.yml`: cron at 07:00 & 08:00 UTC to approximate 09:00 PL across DST, runs build and commits.
- `.github/workflows/pages.yml`: deploys `/site` on push.

## Idempotency

`generate_all.py` checks if `site/YYYY-MM-DD.html` exists and exits (unless `FORCE_RUN=1`).

## Email (optional)

Set secrets as env in workflow: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `SMTP_FROM`. Then call `send_email.py` with latest HTML. Disabled by default.

## Subscribe workflow (optional)

Opening an Issue titled “Subscribe” with an email in the body appends it to `data/subscribers.txt`.

## Troubleshooting

- Empty build? Live fetch is placeholder; curated fallback is used.
- Reset seen-cache: set `RESET_SEEN=1` in environment (or delete `data/seen.json`).
