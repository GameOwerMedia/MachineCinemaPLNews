# Dependency & Model Check Report

- Python: 3.12.10 (main, Aug 28 2025, 21:54:05) [GCC 13.3.0]
- OS: Linux-6.12.13-x86_64-with-glibc2.39
- Online: True
- pip method: venv (existing)

## PyPI Packages

name | status | version | import_ok | notes
--- | --- | --- | --- | ---
feedparser | installed | 6.0.12 | True | 
trafilatura | installed | 2.0.0 | True | 
readability-lxml | installed | 0.8.4.1 | True | 
newspaper4k[gnews] | installed | 0.9.3.1 | True | 
tldextract | installed | 5.3.0 | True | 
url-normalize | installed | 2.2.1 | True | 
rapidfuzz | installed | 3.14.1 | True | 
datasketch | installed | 1.6.5 | True | 
sentence-transformers | failed |  | False | TIMEOUT after 60s
requests-cache | installed | 1.2.1 | True | 

## Hugging Face Models

model | status | notes
--- | --- | ---
sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2 | fail | Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sentence_transformers'
intfloat/multilingual-e5-base | fail | Traceback (most recent call last):
  File "<string>", line 2, in <module>
ModuleNotFoundError: No module named 'sentence_transformers'

## Integration Probes

- url_normalize_tldextract: OK | stdout: example.com | google.com | stderr: /workspace/MachineCinemaPLNews/scratch/probes/url_normalize_tldextract.py:9: DeprecationWarning: The 'registered_domain' property is deprecated and will be removed in the next major version. Use 'top_domain_under_public_suffix' instead, which has the same behavior but a more accurate name.
  domains = [tldextract.extract(u).registered_domain for u in normalized]
- newspaper_gnews: OK | stdout: https://news.google.com
- trafilatura_extract: OK | stdout: To jest test.
- rapidfuzz_ratio: OK | stdout: 80.76923076923077
- datasketch_minhash: OK | stdout: 0.547
- requests_cache_session: OK | stdout: backend: scratch/cache

## Recommendations

### Ready now

- feedparser, trafilatura, readability-lxml, newspaper4k[gnews], tldextract, url-normalize, rapidfuzz, datasketch, requests-cache

### Require attention

- sentence-transformers: TIMEOUT after 60s

### Suggested requirements.txt block

feedparser
trafilatura
readability-lxml
newspaper4k
tldextract
url-normalize
rapidfuzz
datasketch
requests-cache
