"""
AZALSCORE - XML Exporter
Exporter XML
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import defusedxml.minidom as minidom
from datetime import datetime, date
from decimal import Decimal

from .base import BaseExporter


class XMLExporter(BaseExporter):
    """Exporter XML"""

    def export(self, data: list[dict], options: dict) -> bytes:
        encoding = options.get("encoding", "utf-8")
        root_element = options.get("root_element", "data")
        record_element = options.get("record_element", "record")
        pretty_print = options.get("pretty_print", True)

        root = ET.Element(root_element)

        for record in data:
            record_elem = ET.SubElement(root, record_element)

            for key, value in record.items():
                if key.startswith("__"):
                    continue

                field_elem = ET.SubElement(record_elem, self._sanitize_xml_tag(key))

                if isinstance(value, datetime):
                    field_elem.text = value.strftime("%Y-%m-%dT%H:%M:%S")
                elif isinstance(value, date):
                    field_elem.text = value.strftime("%Y-%m-%d")
                elif isinstance(value, Decimal):
                    field_elem.text = str(value)
                elif isinstance(value, dict):
                    self._dict_to_xml(value, field_elem)
                elif value is not None:
                    field_elem.text = str(value)

        if pretty_print:
            xml_string = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
            xml_lines = xml_string.split("\n")[1:]
            return "\n".join(xml_lines).encode(encoding)

        return ET.tostring(root, encoding=encoding)

    def _sanitize_xml_tag(self, tag: str) -> str:
        """Nettoie un nom de tag XML"""
        tag = re.sub(r'[^a-zA-Z0-9_\-.]', '_', str(tag))
        if tag and tag[0].isdigit():
            tag = f"_{tag}"
        return tag or "field"

    def _dict_to_xml(self, d: dict, parent: ET.Element) -> None:
        """Convertit un dictionnaire en éléments XML"""
        for key, value in d.items():
            child = ET.SubElement(parent, self._sanitize_xml_tag(key))
            if isinstance(value, dict):
                self._dict_to_xml(value, child)
            elif value is not None:
                child.text = str(value)
