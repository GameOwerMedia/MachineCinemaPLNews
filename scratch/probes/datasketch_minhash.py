
from datasketch import MinHash
tokens_a = {'openai', 'anthropic', 'meta'}
tokens_b = {'openai', 'meta', 'google'}
m1, m2 = MinHash(), MinHash()
for t in tokens_a:
    m1.update(t.encode('utf-8'))
for t in tokens_b:
    m2.update(t.encode('utf-8'))
print(round(m1.jaccard(m2), 3))
