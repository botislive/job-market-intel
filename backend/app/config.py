from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    database_url: str = f"sqlite:///{DATA_DIR / 'jobs.db'}"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    user_agent: str = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    linkedin_searches: list[dict] = [
        {"keywords": "SAP", "location": "India", "label": "SAP — India"},
        {"keywords": "DevOps", "location": "United States", "label": "DevOps — US", "f_WT": "2"},
        {"keywords": "Java Developer", "location": "India", "label": "Java — India"},
        {"keywords": "ServiceNow", "location": "United States", "label": "ServiceNow — US"},
        {"keywords": "Python Developer", "location": "India", "label": "Python — India"},
    ]
    linkedin_max_pages: int = 2
    request_delay_seconds: float = 1.5
    careers_request_delay_seconds: float = 0.35


settings = Settings()
