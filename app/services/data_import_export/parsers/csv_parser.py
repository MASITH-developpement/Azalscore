"""
AZALSCORE - CSV Parser
Parser CSV avec protection DoS
"""
from __future__ import annotations

import csv
import io
import logging
from typing import Generator

from .base import BaseParser

logger = logging.getLogger(__name__)


class CSVParser(BaseParser):
    """Parser CSV avec protection DoS"""

    MAX_CSV_SIZE = 50 * 1024 * 1024  # 50 Mo
    MAX_COLUMNS = 500
    MAX_ROWS = 1_000_000

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        if len(content) > self.MAX_CSV_SIZE:
            raise ValueError(f"Fichier CSV trop volumineux (max {self.MAX_CSV_SIZE // (1024*1024)} Mo)")

        encoding = options.get("encoding", "utf-8")
        delimiter = options.get("delimiter", ";")
        quotechar = options.get("quotechar", '"')
        skip_rows = options.get("skip_rows", 0)
        has_header = options.get("has_header", True)

        try:
            text_content = content.decode(encoding)
        except UnicodeDecodeError:
            for enc in ["utf-8", "latin-1", "cp1252", "iso-8859-1"]:
                try:
                    text_content = content.decode(enc)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Impossible de décoder le fichier")

        reader = csv.reader(
            io.StringIO(text_content),
            delimiter=delimiter,
            quotechar=quotechar
        )

        for _ in range(skip_rows):
            try:
                next(reader)
            except StopIteration:
                return

        headers = []
        if has_header:
            try:
                headers = [h.strip() for h in next(reader)]
                if len(headers) > self.MAX_COLUMNS:
                    raise ValueError(f"Trop de colonnes ({len(headers)} > {self.MAX_COLUMNS})")
            except StopIteration:
                return

        row_count = 0
        for row_num, row in enumerate(reader, start=skip_rows + 2 if has_header else skip_rows + 1):
            row_count += 1
            if row_count > self.MAX_ROWS:
                logger.warning(f"Limite de lignes atteinte ({self.MAX_ROWS})")
                break
            if not any(row):
                continue

            if headers:
                record = {}
                for i, header in enumerate(headers):
                    record[header] = row[i] if i < len(row) else ""
            else:
                record = {f"col_{i}": val for i, val in enumerate(row)}

            record["__row_number__"] = row_num
            yield record

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        encoding = options.get("encoding", "utf-8")
        delimiter = options.get("delimiter", ";")
        skip_rows = options.get("skip_rows", 0)

        try:
            text_content = content.decode(encoding)
        except UnicodeDecodeError:
            text_content = content.decode("latin-1")

        reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)

        for _ in range(skip_rows):
            try:
                next(reader)
            except StopIteration:
                return []

        try:
            return [h.strip() for h in next(reader)]
        except StopIteration:
            return []
