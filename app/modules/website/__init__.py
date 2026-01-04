"""
AZALS MODULE T8 - Site Web Officiel AZALS
==========================================

Module de gestion du site web public:
- Pages de présentation
- Blog et actualités
- Formulaires de contact
- Témoignages clients
- Documentation publique
- SEO et analytics

Version: 1.0.0
"""

__version__ = "1.0.0"
__module_code__ = "T8"
__module_name__ = "Site Web Officiel AZALS"
__module_type__ = "TRANSVERSE"
__dependencies__ = ["T0", "T7"]

# Types de pages
PAGE_TYPES = [
    "LANDING",
    "PRODUCT",
    "PRICING",
    "ABOUT",
    "CONTACT",
    "BLOG",
    "DOCUMENTATION",
    "LEGAL",
    "CUSTOM",
]

# Statuts de publication
PUBLISH_STATUS = [
    "DRAFT",
    "PENDING_REVIEW",
    "PUBLISHED",
    "ARCHIVED",
]

# Types de contenu
CONTENT_TYPES = [
    "ARTICLE",
    "NEWS",
    "CASE_STUDY",
    "TESTIMONIAL",
    "FAQ",
    "TUTORIAL",
    "RELEASE_NOTE",
]

# Catégories de formulaire
FORM_CATEGORIES = [
    "CONTACT",
    "DEMO_REQUEST",
    "QUOTE_REQUEST",
    "SUPPORT",
    "NEWSLETTER",
    "FEEDBACK",
]
