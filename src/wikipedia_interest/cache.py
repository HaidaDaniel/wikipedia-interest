from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable


class FileCache:
    def __init__(self, root: str | Path = ".cache") -> None:
        self.root = Path(root)

    def _path(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / namespace / f"{digest}.json"

    def get(self, namespace: str, key: str) -> Any | None:
        path = self._path(namespace, key)
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def put(self, namespace: str, key: str, value: Any) -> None:
        path = self._path(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        temp.replace(path)

    def get_or_set(self, namespace: str, key: str, factory: Callable[[], Any], use_cache: bool = True) -> Any:
        if use_cache:
            cached = self.get(namespace, key)
            if cached is not None:
                return cached
        value = factory()
        if use_cache:
            self.put(namespace, key, value)
        return value

