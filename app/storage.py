import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOG_FILE = DATA_DIR / "photo_logs.jsonl"
FEEDBACK_FILE = DATA_DIR / "feedback.jsonl"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def append_jsonl(path: Path, record: Dict[str, Any]) -> None:
    _ensure_data_dir()
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def log_photo(record: Dict[str, Any]) -> None:
    record = {"created_at": _utc_now(), **record}
    append_jsonl(LOG_FILE, record)


def log_feedback(record: Dict[str, Any]) -> None:
    record = {"created_at": _utc_now(), **record}
    append_jsonl(FEEDBACK_FILE, record)


def iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
