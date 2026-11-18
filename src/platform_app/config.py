import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env", override=False)


@dataclass(frozen=True)
class Settings:
    root: Path = ROOT
    seed: int = 42
    users: int = 10000
    start: date = date(2025, 1, 1)
    end: date = date(2025, 9, 30)

    def __post_init__(self):
        if self.users < 10 or (self.end - self.start).days < 180:
            raise ValueError("Use at least 10 users and 181 calendar days for temporal ML splits")

    @property
    def generated(self) -> Path:
        return self.root / "data" / "generated"

    @property
    def outputs(self) -> Path:
        return self.root / "outputs"

    @classmethod
    def from_env(cls):
        return cls(
            seed=int(os.getenv("SYNTHETIC_SEED", "42")),
            users=int(os.getenv("SYNTHETIC_USERS", "10000")),
            start=date.fromisoformat(os.getenv("HISTORY_START", "2025-01-01")),
            end=date.fromisoformat(os.getenv("HISTORY_END", "2025-09-30")),
        )
