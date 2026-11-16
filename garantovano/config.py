"""The single place for paths, thresholds and rules (DRY). Change behaviour here, not in modules."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
PACKAGES_CSV = DATA_DIR / "packages.csv"
FACILITIES_CSV = DATA_DIR / "facilities.csv"
RIGHTS_JSON = DATA_DIR / "rights.json"
META_JSON = DATA_DIR / "meta.json"

# LLM (need -> package ids). Model is configurable; Haiku 5.5 ("claude-haiku-5-5") is the cheaper/faster option.
MODEL = os.getenv("GARANTOVANO_MODEL", "claude-opus-5-5")
# Which LLM adapter the app uses: "gemma" (Google Gemini API, key GEMINI_API_KEY) or "anthropic" (ANTHROPIC_API_KEY).
LLM_PROVIDER = os.getenv("GARANTOVANO_PROVIDER", "gemma")
GEMMA_MODEL_DEFAULT = "gemini-3.8-flash"  # Gemma is not served for our AI Studio key; Gemini Flash is (16.11)
GEMMA_MODEL = os.getenv("GARANTOVANO_GEMMA_MODEL", GEMMA_MODEL_DEFAULT)


def gemma_model() -> str:
    """Read at call time: Streamlit Cloud applies changed Secrets to env without restarting the process."""
    return os.getenv("GARANTOVANO_GEMMA_MODEL", GEMMA_MODEL_DEFAULT)


# One retry on another model when Google says "overloaded" (503) or "rate limited" (429).
GEMMA_FALLBACK_CODES = frozenset({429, 503})
_FALLBACK_PAIR = ("gemini-3.5-flash-lite", "gemini-3.8-flash")


def gemma_fallback_model(primary: str) -> str:
    """GARANTOVANO_GEMMA_FALLBACK if set, else the other model of the pair (never the primary itself)."""
    explicit = os.getenv("GARANTOVANO_GEMMA_FALLBACK")
    if explicit:
        return explicit
    return _FALLBACK_PAIR[1] if primary == _FALLBACK_PAIR[0] else _FALLBACK_PAIR[0]
LLM_TIMEOUT_S = float(os.getenv("GARANTOVANO_LLM_TIMEOUT", "15"))
MIN_CONFIDENCE = 0.6
MAX_PACKAGES = 3
MAX_INPUT_CHARS = 500

# Deterministic emergency rule: checked BEFORE and INDEPENDENTLY of the model.
EMERGENCY_KEYWORDS = (
    "інсульт", "інфаркт", "не дихає", "задиха", "кровотеч", "втратив свідомість", "втратила свідомість",
    "без свідомості", "біль у грудях", "болить серце", "судом", "отруєн", "перекосило обличчя",
)
EMERGENCY_NUMBER = "103"
# Ambulance packages ("Екстрена медична допомога", incl. COVID variant): served by 103, not by a facility
# you walk into, and never contracted together with hospital packages -> combining them yields "not found".
# The 103 banner already covers them, so match() drops them from the model's answer.
AMBULANCE_PACKAGE_IDS = frozenset({"2", "28"})
NSZU_HOTLINE = "16-77"

# Search
DEFAULT_LIMIT = 10
FLAGSHIP_EXAMPLES = (
    "Я вагітна, 10 тижнів, живу на Оболоні. Де стати на облік і народжувати безкоштовно?",
    "Я ветеран, мені треба поставити зуби",
    "Мамі потрібна мамографія",
)
DISCLAIMER = "Договір з НСЗУ не гарантує вільного місця сьогодні — зателефонуйте перед візитом."

# UI: one-tap examples (label, query); each runs the search at once.
EXAMPLES = (
    ("🤰 Вагітність", FLAGSHIP_EXAMPLES[0]),
    ("🦷 Ветеран: зуби", FLAGSHIP_EXAMPLES[1]),
    ("🩻 Мамографія", FLAGSHIP_EXAMPLES[2]),
    ("🧠 Інсульт", "У тата інсульт, куди їхати?"),
)
DEFAULT_REGION = "М.КИЇВ"
NEONATAL_PACKAGE_ID = "8"

# Deterministic fast path, checked before the model: common needs -> NSZU package ids.
# Rule = (groups, package_ids): every group must match (any lower-case stem from it is in the text).
# The model handles everything else. Ids verified against data/packages.csv on 16.11.2026.
KEYWORD_RULES = (
    ((("вагітн", "на облік"),), ("35",)),
    ((("народж", "пологи", "пологах", "пологов"),), ("7",)),
    ((("ветеран", "убд", "захисни", "військов"), ("зуб", "протез")), ("66",)),
    ((("мамограф",),), ("10",)),
    ((("колоноскоп",),), ("13",)),
    ((("гастроскоп", "фгдс", "езофаго"),), ("12",)),
    ((("гемодіаліз", "діаліз"),), ("16",)),
    ((("хіміотерап",),), ("17",)),
    ((("інсульт",),), ("5",)),
    ((("інфаркт",),), ("6",)),
    ((("психолог", "психіатр", "депрес", "птср"),), ("72",)),
    ((("реабіліт",),), ("54",)),
)
