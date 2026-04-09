# Minimal dotenv shim for demo environments
from pathlib import Path


def dotenv_values(path: str | None = None):
    env_path = Path(path) if path else Path(".env")
    if not env_path.exists():
        return {}

    values = {}
    for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def load_dotenv(path: str | None = None):
    for key, value in dotenv_values(path).items():
        if key and key not in __import__("os").environ:
            __import__("os").environ[key] = value
    return True
