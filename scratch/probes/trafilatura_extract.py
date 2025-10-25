
import trafilatura
html = '<html><body><article><p>To jest test.</p></article></body></html>'
text = trafilatura.extract(html)
print((text or '').strip())
