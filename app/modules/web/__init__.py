"""
AZALS MODULE T7 - Module Web Transverse
========================================

Module transverse pour les composants web:
- Thèmes et personnalisation
- Widgets et dashboards
- Menus et navigation
- Composants UI réutilisables
- Préférences utilisateur interface

Version: 1.0.0
"""

__version__ = "1.0.0"
__module_code__ = "T7"
__module_name__ = "Module Web Transverse"
__module_type__ = "TRANSVERSE"
__dependencies__ = ["T0"]

# Thèmes disponibles
THEMES = [
    "light",
    "dark",
    "system",
    "high-contrast",
]

# Types de widgets
WIDGET_TYPES = [
    "KPI",
    "CHART",
    "TABLE",
    "LIST",
    "CALENDAR",
    "MAP",
    "GAUGE",
    "TIMELINE",
    "CUSTOM",
]

# Catégories de composants
COMPONENT_CATEGORIES = [
    "layout",
    "navigation",
    "forms",
    "data-display",
    "feedback",
    "charts",
    "actions",
]
