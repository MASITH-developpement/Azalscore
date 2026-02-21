"""
Module Templates et Document Builder - GAP-057

Gestion des modèles de documents:
- Éditeur de templates WYSIWYG
- Variables dynamiques
- Sections conditionnelles
- Boucles (lignes de facture, etc.)
- Multi-formats (PDF, DOCX, HTML)
- Versioning des templates
"""

from .service import (
    # Énumérations
    TemplateType,
    OutputFormat,
    VariableType,
    TemplateStatus,
    SectionType,

    # Data classes
    TemplateVariable,
    ConditionalSection,
    LoopSection,
    TemplateSection,
    TemplateStyle,
    Template,
    GeneratedDocument,
    TemplatePreset,

    # Service
    TemplateService,
    create_template_service,
)

__all__ = [
    "TemplateType",
    "OutputFormat",
    "VariableType",
    "TemplateStatus",
    "SectionType",
    "TemplateVariable",
    "ConditionalSection",
    "LoopSection",
    "TemplateSection",
    "TemplateStyle",
    "Template",
    "GeneratedDocument",
    "TemplatePreset",
    "TemplateService",
    "create_template_service",
]
