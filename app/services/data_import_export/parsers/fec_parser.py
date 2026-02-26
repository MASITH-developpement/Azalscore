"""
AZALSCORE - FEC Parser
Parser FEC (Fichier des Écritures Comptables)
"""
from __future__ import annotations

import csv
import io
from typing import Generator

from .base import BaseParser


class FECParser(BaseParser):
    """Parser FEC (Fichier des Écritures Comptables)"""

    FEC_COLUMNS = [
        "JournalCode", "JournalLib", "EcritureNum", "EcritureDate",
        "CompteNum", "CompteLib", "CompAuxNum", "CompAuxLib",
        "PieceRef", "PieceDate", "EcritureLib", "Debit", "Credit",
        "EcritureLet", "DateLet", "ValidDate", "Montantdevise", "Idevise"
    ]

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        delimiter = options.get("delimiter", "\t")

        for enc in ["utf-8", "latin-1", "cp1252"]:
            try:
                text_content = content.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        else:
            raise ValueError("Impossible de décoder le fichier FEC")

        reader = csv.reader(io.StringIO(text_content), delimiter=delimiter)

        try:
            headers = [h.strip() for h in next(reader)]
        except StopIteration:
            return

        for row_num, row in enumerate(reader, start=2):
            if not any(row):
                continue

            record = {}
            for i, header in enumerate(headers):
                record[header] = row[i] if i < len(row) else ""

            record["__row_number__"] = row_num
            yield record

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        return self.FEC_COLUMNS
