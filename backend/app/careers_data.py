import json
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "fortune100_careers.json"


@lru_cache
def load_fortune100_companies() -> list[dict]:
    with DATA_FILE.open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload["companies"]


def fortune100_company_names() -> set[str]:
    return {c["name"] for c in load_fortune100_companies()}
