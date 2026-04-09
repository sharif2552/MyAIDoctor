# Minimal dotenv shim for demo environments
import os

def load_dotenv(path: str | None = None):
    # No-op for local/demo runs; real projects should install python-dotenv
    return None


def dotenv_values(path: str | None = None):
    return {}
