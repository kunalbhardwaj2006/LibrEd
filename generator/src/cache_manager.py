import json
import os
from pathlib import Path

CACHE_FILE = Path("generator/cache/llm_cache.json")


class LLMCache:
    def __init__(self):
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r") as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def get(self, prompt):
        return self.cache.get(prompt)

    def set(self, prompt, response):
        self.cache[prompt] = response
        with open(CACHE_FILE, "w") as f:
            json.dump(self.cache, f, indent=2)
