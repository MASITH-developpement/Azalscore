"""
AZALSCORE - JSON Parser
Parser JSON avec protection DoS
"""
from __future__ import annotations

import json
from typing import Generator

from .base import BaseParser


class JSONParser(BaseParser):
    """Parser JSON avec protection DoS"""

    MAX_JSON_SIZE = 50 * 1024 * 1024  # 50 Mo
    MAX_DEPTH = 50

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        if len(content) > self.MAX_JSON_SIZE:
            raise ValueError(f"Fichier JSON trop volumineux (max {self.MAX_JSON_SIZE // (1024*1024)} Mo)")

        encoding = options.get("encoding", "utf-8")
        root_path = options.get("root_path")

        data = json.loads(content.decode(encoding))

        if root_path:
            for key in root_path.split("."):
                if isinstance(data, dict):
                    data = data.get(key, [])
                elif isinstance(data, list) and key.isdigit():
                    data = data[int(key)]

        if not isinstance(data, list):
            data = [data]

        for row_num, record in enumerate(data, start=1):
            if isinstance(record, dict):
                record["__row_number__"] = row_num
                yield record

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        encoding = options.get("encoding", "utf-8")
        root_path = options.get("root_path")

        data = json.loads(content.decode(encoding))

        if root_path:
            for key in root_path.split("."):
                if isinstance(data, dict):
                    data = data.get(key, [])

        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
            return list(data[0].keys())
        elif isinstance(data, dict):
            return list(data.keys())
        return []
