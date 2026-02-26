"""
AZALSCORE - JSON Exporter
Exporter JSON
"""
from __future__ import annotations

import json
from datetime import datetime, date
from decimal import Decimal

from .base import BaseExporter


class JSONExporter(BaseExporter):
    """Exporter JSON"""

    def export(self, data: list[dict], options: dict) -> bytes:
        encoding = options.get("encoding", "utf-8")
        indent = options.get("indent", 2)
        root_key = options.get("root_key")
        date_format = options.get("date_format", "%Y-%m-%d")
        datetime_format = options.get("datetime_format", "%Y-%m-%dT%H:%M:%S")

        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.strftime(datetime_format)
            elif isinstance(obj, date):
                return obj.strftime(date_format)
            elif isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        filtered_data = []
        for record in data:
            filtered_record = {k: v for k, v in record.items() if not k.startswith("__")}
            filtered_data.append(filtered_record)

        if root_key:
            output_data = {root_key: filtered_data}
        else:
            output_data = filtered_data

        return json.dumps(
            output_data,
            ensure_ascii=False,
            indent=indent,
            default=json_serializer
        ).encode(encoding)
