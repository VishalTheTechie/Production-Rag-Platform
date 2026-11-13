"""Corpus version number. Bumped whenever documents or their permissions change,
so cached answers can never outlive the data they came from."""
from pathlib import Path

VERSION_FILE = Path("data/corpus_version.txt")


def get_version() -> int:
    try:
        return int(VERSION_FILE.read_text(encoding="utf-8").strip())
    except Exception:
        return 1


def bump_version() -> int:
    v = get_version() + 1
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(str(v), encoding="utf-8")
    return v
