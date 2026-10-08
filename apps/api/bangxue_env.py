"""Load .env without overriding variables already in the process.

Local layout: apps/api/bangxue_env.py → repo-root .env
Docker layout: /app/bangxue_env.py → prefer process env (compose); optional /app/.env
"""

from pathlib import Path

from dotenv import load_dotenv


def _env_file_candidates() -> list[Path]:
    here = Path(__file__).resolve().parent
    paths: list[Path] = []
    # Local monorepo: .../apps/api → repo root
    if here.name == "api" and here.parent.name == "apps":
        paths.append(here.parent.parent / ".env")
    paths.append(here / ".env")
    return paths


def load_repo_env() -> None:
    # override=False keeps variables the operator already exported (e.g. compose).
    for path in _env_file_candidates():
        if path.is_file():
            load_dotenv(path, override=False)
            return
