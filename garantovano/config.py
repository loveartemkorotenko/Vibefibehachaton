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
NSZU_HOTLINE = "16-77"

# Search
DEFAULT_LIMIT = 10
FLAGSHIP_EXAMPLES = (
    "Я вагітна, 10 тижнів, живу на Оболоні. Де стати на облік і народжувати безкоштовно?",
    "Я ветеран, мені треба поставити зуби",
    "Мамі потрібна мамографія",
)
DISCLAIMER = "Договір з НСЗУ не гарантує вільного місця сьогодні — зателефонуйте перед візитом."
