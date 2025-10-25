from __future__ import annotations
from typing import List, Dict

NOISE = ["sponsorowany", "kupon", "rabaty", "benchmark", "plotka", "zniżka"]

KEY_TERMS = [
    "AI","sztuczna inteligencja","model językowy","LLM","uczenie maszynowe",
    "genAI","dyfuzja","multimodalny","wideo AI","rozpoznawanie","NLP","robotyka",
    "stabilność","OpenAI","Google","Anthropic","Meta","Stability","Hugging Face",
]

def is_relevant(item: Dict) -> bool:
    text = f"{item.get('title','')} {item.get('summary','')}".lower()
    if any(n in text for n in NOISE):
        # allow if KEY_TERMS present (AI value)
        if not any(k.lower() in text for k in KEY_TERMS):
            return False
    return True

def dedup(items: List[Dict]) -> List[Dict]:
    seen = set()
    out = []
    for it in items:
        key = it["url"].split("?")[0].rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out
