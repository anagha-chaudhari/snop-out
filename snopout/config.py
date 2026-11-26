import os

from dotenv import load_dotenv

load_dotenv()  


def get_github_token() -> str | None:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    return token or None