from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


class SourceLoadError(ValueError):
    pass


def load_json_source(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text())
    except OSError as exc:
        raise SourceLoadError(f"Unable to read source: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SourceLoadError(f"Invalid JSON in source: {path}") from exc
    if "items" not in data:
        raise SourceLoadError(f"Source missing items: {path}")
    return data


def load_sources(paths: List[Path]) -> List[Dict[str, Any]]:
    return [load_json_source(path) for path in paths]
