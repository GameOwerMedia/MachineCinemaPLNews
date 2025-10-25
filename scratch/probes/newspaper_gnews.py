
from newspaper import Article
url = 'https://news.google.com/rss/articles/CBMiRmh0dHBzOi8vZXhhbXBsZS5jb20vYXJ0aWNsZS_SAQA?hl=pl&gl=PL&ceid=PL:pl'
art = Article(url)
print(art.source_url)
