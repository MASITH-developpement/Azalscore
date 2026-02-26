"""
AZALSCORE - CSV Exporter
Exporter CSV
"""
from __future__ import annotations

import csv
import io

from .base import BaseExporter


class CSVExporter(BaseExporter):
    """Exporter CSV"""

    def export(self, data: list[dict], options: dict) -> bytes:
        if not data:
            return b""

        encoding = options.get("encoding", "utf-8")
        delimiter = options.get("delimiter", ";")
        quotechar = options.get("quotechar", '"')
        include_bom = options.get("include_bom", False)
        columns = options.get("columns")

        output = io.StringIO()

        if columns:
            headers = columns
        else:
            headers = [k for k in data[0].keys() if not k.startswith("__")]

        writer = csv.DictWriter(
            output,
            fieldnames=headers,
            delimiter=delimiter,
            quotechar=quotechar,
            extrasaction="ignore"
        )

        writer.writeheader()

        for record in data:
            filtered_record = {k: v for k, v in record.items() if not k.startswith("__")}
            writer.writerow(filtered_record)

        content = output.getvalue()

        if include_bom and encoding.lower() in ("utf-8", "utf8"):
            return b'\xef\xbb\xbf' + content.encode(encoding)
        return content.encode(encoding)
