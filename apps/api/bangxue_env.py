"""Load the repo-root .env without overriding variables already in the process."""

from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parents[2]


def load_repo_env() -> None:
    # override=False keeps a variable that the operator already exported.
    load_dotenv(_REPO_ROOT / ".env", override=False)
