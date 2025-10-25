
from rapidfuzz import fuzz
s1 = 'OpenAI ogłasza nowy model'
s2 = 'OpenAI zapowiada nowy model'
print(fuzz.ratio(s1, s2))
