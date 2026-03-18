import os


# ---------------------------
# Environment Configuration
# ---------------------------
# Local LLM Only

# Ollama Configuration
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


# ---------------------------
# Ollama Host Configuration
# ---------------------------
_OLLAMA_HOST_ENV = os.getenv("OLLAMA_HOST")

if _OLLAMA_HOST_ENV:
    if _OLLAMA_HOST_ENV.startswith("http"):
        OLLAMA_BASE_URL = _OLLAMA_HOST_ENV
    else:
        OLLAMA_BASE_URL = f"http://{_OLLAMA_HOST_ENV}"
else:
    OLLAMA_BASE_URL = "http://localhost:11434"


# ---------------------------
# Base Paths
# ---------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_ROOT = os.path.dirname(BASE_DIR)


# ---------------------------
# Data Directories
# ---------------------------
DATA_DIR = os.path.join(REPO_ROOT, "data")
GATE_ASSETS_DIR = os.path.join(REPO_ROOT, "frontend", "public", "assets", "gate")

RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
DB_PATH = os.path.join(DATA_DIR, "app.duckdb")


# ---------------------------
# Stream Aliases
# ---------------------------
STREAM_ALIASES = {
    "computer-science-information-technology": "cs",
}


# ---------------------------
# Image Optimization Configuration
# ---------------------------

IMAGE_FORMAT = os.getenv("IMAGE_FORMAT", "webp").lower()

if IMAGE_FORMAT not in {"png", "webp"}:
    raise ValueError(
        f"Invalid IMAGE_FORMAT='{IMAGE_FORMAT}'. Supported formats are 'png' or 'webp'."
    )


def _get_int_env(name: str, default: int) -> int:
    """Safely parse integer environment variables."""
    value = os.getenv(name, str(default))
    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Environment variable {name} must be an integer, got '{value}'")


def _get_float_env(name: str, default: float) -> float:
    """Safely parse float environment variables."""
    value = os.getenv(name, str(default))
    try:
        return float(value)
    except ValueError:
        raise ValueError(f"Environment variable {name} must be a float, got '{value}'")


IMAGE_QUALITY = _get_int_env("IMAGE_QUALITY", 85)

if not 1 <= IMAGE_QUALITY <= 100:
    raise ValueError("IMAGE_QUALITY must be between 1 and 100")


IMAGE_LOSSLESS = os.getenv("IMAGE_LOSSLESS", "False").lower() == "true"


PDF_ZOOM_LEVEL = _get_float_env("PDF_ZOOM_LEVEL", 1.0)

if PDF_ZOOM_LEVEL <= 0:
    raise ValueError("PDF_ZOOM_LEVEL must be greater than 0")


# ---------------------------
# Processing Limitations
# ---------------------------

TEST_PROMPT_LIMIT = None
# TEST_PROMPT_LIMIT = 1


CLASSIFICATION_BATCH_SIZE = _get_int_env("CLASSIFICATION_BATCH_SIZE", 10)

if CLASSIFICATION_BATCH_SIZE <= 0:
    raise ValueError("CLASSIFICATION_BATCH_SIZE must be a positive integer")


# ---------------------------
# Scraping Configuration
# ---------------------------

TARGET_STREAMS = [
    "electrical-engineering",
    "mechanical-engineering",
    "electronics-and-communication-engineering",
    "instrumentation-engineering",
    "civil-engineering",
    "chemical-engineering",
    "computer-science-information-technology",
]


GATE_ACADEMY_URL = "https://www.gateacademy.co.in"
