"""
AZALSCORE - XML Parser
Parser XML avec protection XXE
"""
from __future__ import annotations

import logging
import xml.etree.ElementTree as ET_std
import defusedxml.ElementTree as DefusedET
from typing import Generator

from .base import BaseParser

logger = logging.getLogger(__name__)

# Alias pour compatibilité
ET = type('ET', (), {
    'Element': ET_std.Element,
    'SubElement': ET_std.SubElement,
    'tostring': ET_std.tostring,
    'fromstring': DefusedET.fromstring,
    'parse': DefusedET.parse,
    'ParseError': ET_std.ParseError,
})()


class XMLParser(BaseParser):
    """Parser XML avec protection XXE"""

    MAX_XML_SIZE = 10 * 1024 * 1024  # 10 Mo

    def _safe_parse_xml(self, xml_content: bytes) -> ET.Element:
        """Parse XML de manière sécurisée (protection XXE)"""
        if len(xml_content) > self.MAX_XML_SIZE:
            raise ValueError(f"Fichier XML trop volumineux (max {self.MAX_XML_SIZE // (1024*1024)} Mo)")

        try:
            return DefusedET.fromstring(xml_content)
        except ImportError:
            logger.warning("defusedxml non installé - utilisation du parser sécurisé manuel")

            xml_str = xml_content.decode("utf-8", errors="replace")
            dangerous_patterns = [
                "<!ENTITY", "<!DOCTYPE", "SYSTEM", "PUBLIC",
                "file://", "http://", "https://", "ftp://"
            ]
            xml_upper = xml_str.upper()
            for pattern in dangerous_patterns:
                if pattern.upper() in xml_upper:
                    raise ValueError(f"Contenu XML potentiellement dangereux détecté: {pattern}")

            return ET_std.fromstring(xml_content)

    def parse(self, content: bytes, options: dict) -> Generator[dict, None, None]:
        root_element = options.get("root_element", "record")
        encoding = options.get("encoding", "utf-8")

        try:
            xml_content = content if isinstance(content, bytes) else content.encode(encoding)
            root = self._safe_parse_xml(xml_content)
        except UnicodeDecodeError:
            root = self._safe_parse_xml(content)

        records = root.findall(f".//{root_element}")

        for row_num, elem in enumerate(records, start=1):
            record = self._element_to_dict(elem)
            record["__row_number__"] = row_num
            yield record

    def _element_to_dict(self, elem: ET_std.Element) -> dict:
        """Convertit un élément XML en dictionnaire"""
        result = {}

        result.update(elem.attrib)

        for child in elem:
            if len(child) > 0:
                result[child.tag] = self._element_to_dict(child)
            else:
                result[child.tag] = child.text

        if elem.text and elem.text.strip():
            if not result:
                return {"__text__": elem.text.strip()}
            result["__text__"] = elem.text.strip()

        return result

    def get_headers(self, content: bytes, options: dict) -> list[str]:
        root_element = options.get("root_element", "record")

        try:
            root = self._safe_parse_xml(content)
        except (ET_std.ParseError, ValueError) as e:
            logger.warning(f"Erreur parsing XML headers: {e}")
            return []

        records = root.findall(f".//{root_element}")
        if records:
            first_record = self._element_to_dict(records[0])
            return list(first_record.keys())
        return []
