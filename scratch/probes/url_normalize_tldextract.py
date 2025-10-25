
from url_normalize import url_normalize
import tldextract
urls = [
    'HTTPS://Example.com:80/path?utm_source=test',
    'https://news.google.com/articles/CBMiN2h0dHBzOi8vZXhhbXBsZS5jb20vbmV3cz9ocmVmPXJzcy0x0gEA'
]
normalized = [url_normalize(u) for u in urls]
domains = [tldextract.extract(u).registered_domain for u in normalized]
print(' | '.join(domains))
