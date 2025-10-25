
import requests_cache
session = requests_cache.CachedSession('scratch/cache', expire_after=1800)
cache = getattr(session, 'cache', None)
name = getattr(session, 'cache_name', None)
if not name and cache is not None:
    name = getattr(cache, 'cache_name', None) or cache.__class__.__name__
print('backend:', name)
