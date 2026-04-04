import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

CACHE_FILE = Path("generator/cache/llm_cache.json")


class LLMCache:
    def __init__(self):
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, "r") as f:
                    self.cache = json.load(f)
            except Exception:
                logger.warning("Cache file corrupted. Initializing empty cache.")
                self.cache = {}
        else:
            self.cache = {}

        # 🔥 Metrics
        self.hits = 0
        self.misses = 0

    def get(self, prompt):
        result = self.cache.get(prompt)

        if result is not None:
            self.hits += 1
            logger.info("Cache HIT")
        else:
            self.misses += 1
            logger.info("Cache MISS — calling LLM")

        return result

    def set(self, prompt, response):
        self.cache[prompt] = response
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to write cache: {e}")

    def stats(self):
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            "cache_hits": self.hits,
            "cache_misses": self.misses,
            "hit_rate": round(hit_rate, 3),
        }

    def log_stats(self):
        stats = self.stats()
        logger.info(
            f"Cache Stats -> Hits: {stats['cache_hits']}, "
            f"Misses: {stats['cache_misses']}, "
            f"Hit Rate: {stats['hit_rate']}"
        )
