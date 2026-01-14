"""
AZALS MODULE T1 - Profils Métier Prédéfinis
===========================================

Définitions des profils métier standard pour l'auto-configuration.
"""

from typing import Any

# ============================================================================
# PROFILS MÉTIER PRÉDÉFINIS
# ============================================================================

PREDEFINED_PROFILES: dict[str, dict[str, Any]] = {
    # ========================================================================
    # DIRECTION (Niveau 0-2)
    # ========================================================================
    "CEO": {
        "code": "CEO",
        "name": "Président / Directeur Général",
        "description": "Direction générale de l'entreprise",
        "level": "EXECUTIVE",
        "hierarchy_order": 0,
        "title_patterns": [
            "PDG", "DG", "CEO", "Président", "President",
            "Directeur Général", "Directrice Générale",
            "Chief Executive Officer", "Managing Director"
        ],
        "department_patterns": ["Direction", "Executive", "General Management"],
        "default_roles": ["DIRIGEANT", "TENANT_ADMIN"],
        "default_permissions": ["*"],
        "default_modules": ["*"],
        "max_data_access_level": 0,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 1
    },

    "FOUNDER": {
        "code": "FOUNDER",
        "name": "Fondateur / Associé",
        "description": "Fondateur ou associé de l'entreprise",
        "level": "EXECUTIVE",
        "hierarchy_order": 1,
        "title_patterns": [
            "Fondateur", "Fondatrice", "Founder", "Co-founder",
            "Associé", "Partner", "Actionnaire", "Shareholder"
        ],
        "department_patterns": ["Direction", "Board"],
        "default_roles": ["DIRIGEANT"],
        "default_permissions": [],
        "default_modules": ["*"],
        "max_data_access_level": 0,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 2
    },

    # ========================================================================
    # DIRECTEURS (Niveau 3)
    # ========================================================================
    "CFO": {
        "code": "CFO",
        "name": "Directeur Administratif et Financier",
        "description": "Direction finance et administration",
        "level": "DIRECTOR",
        "hierarchy_order": 3,
        "title_patterns": [
            "DAF", "CFO", "Directeur Financier", "Directrice Financière",
            "Chief Financial Officer", "Finance Director",
            "Directeur Administratif", "VP Finance"
        ],
        "department_patterns": ["Finance", "Comptabilité", "Administration"],
        "default_roles": ["DAF", "COMPTABLE"],
        "default_permissions": [
            "treasury.*", "accounting.*", "tax.*",
            "sales.invoice.*", "purchase.invoice.*"
        ],
        "default_modules": ["treasury", "accounting", "tax", "sales", "purchase"],
        "max_data_access_level": 1,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 10
    },

    "CHRO": {
        "code": "CHRO",
        "name": "Directeur des Ressources Humaines",
        "description": "Direction des ressources humaines",
        "level": "DIRECTOR",
        "hierarchy_order": 3,
        "title_patterns": [
            "DRH", "CHRO", "Directeur RH", "Directrice RH",
            "Chief Human Resources Officer", "HR Director",
            "VP RH", "VP Human Resources"
        ],
        "department_patterns": ["RH", "Ressources Humaines", "Human Resources", "HR"],
        "default_roles": ["DRH", "RH"],
        "default_permissions": ["hr.*", "iam.user.read", "iam.invitation.*"],
        "default_modules": ["hr"],
        "max_data_access_level": 1,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 11
    },

    "CSO": {
        "code": "CSO",
        "name": "Directeur Commercial",
        "description": "Direction commerciale et ventes",
        "level": "DIRECTOR",
        "hierarchy_order": 3,
        "title_patterns": [
            "Directeur Commercial", "Directrice Commerciale",
            "Chief Sales Officer", "Sales Director",
            "VP Sales", "VP Commercial", "CSO"
        ],
        "department_patterns": ["Commercial", "Ventes", "Sales"],
        "default_roles": ["RESPONSABLE_COMMERCIAL", "COMMERCIAL"],
        "default_permissions": ["sales.*", "stock.item.read"],
        "default_modules": ["sales", "stock"],
        "max_data_access_level": 2,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 12
    },

    "CPO": {
        "code": "CPO",
        "name": "Directeur des Achats",
        "description": "Direction des achats et approvisionnements",
        "level": "DIRECTOR",
        "hierarchy_order": 3,
        "title_patterns": [
            "Directeur Achats", "Directrice Achats",
            "Chief Procurement Officer", "Purchasing Director",
            "VP Achats", "VP Procurement", "CPO"
        ],
        "department_patterns": ["Achats", "Procurement", "Purchasing", "Supply Chain"],
        "default_roles": ["RESPONSABLE_ACHATS", "ACHETEUR"],
        "default_permissions": ["purchase.*", "stock.item.read"],
        "default_modules": ["purchase", "stock"],
        "max_data_access_level": 2,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 13
    },

    "COO": {
        "code": "COO",
        "name": "Directeur des Opérations",
        "description": "Direction des opérations et production",
        "level": "DIRECTOR",
        "hierarchy_order": 3,
        "title_patterns": [
            "Directeur Opérations", "Directrice Opérations",
            "Chief Operating Officer", "Operations Director",
            "Directeur Production", "Directrice Production",
            "VP Operations", "COO"
        ],
        "department_patterns": ["Opérations", "Production", "Operations", "Manufacturing"],
        "default_roles": ["RESPONSABLE_PRODUCTION", "MAGASINIER"],
        "default_permissions": ["stock.*", "purchase.order.read"],
        "default_modules": ["stock", "purchase"],
        "max_data_access_level": 2,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 14
    },

    "CTO": {
        "code": "CTO",
        "name": "Directeur Technique / IT",
        "description": "Direction technique et systèmes d'information",
        "level": "DIRECTOR",
        "hierarchy_order": 3,
        "title_patterns": [
            "DSI", "CTO", "Directeur IT", "Directrice IT",
            "Chief Technology Officer", "IT Director",
            "Directeur Informatique", "Directeur Technique",
            "VP Technology", "VP IT"
        ],
        "department_patterns": ["IT", "Informatique", "Technology", "DSI"],
        "default_roles": ["TENANT_ADMIN"],
        "default_permissions": ["iam.*", "admin.*"],
        "default_modules": ["admin"],
        "max_data_access_level": 1,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 15
    },

    "CLO": {
        "code": "CLO",
        "name": "Directeur Juridique",
        "description": "Direction juridique et conformité",
        "level": "DIRECTOR",
        "hierarchy_order": 3,
        "title_patterns": [
            "Directeur Juridique", "Directrice Juridique",
            "Chief Legal Officer", "Legal Director",
            "General Counsel", "VP Legal", "CLO"
        ],
        "department_patterns": ["Juridique", "Legal", "Compliance"],
        "default_roles": ["AUDITEUR"],
        "default_permissions": ["legal.*", "accounting.report.read"],
        "default_modules": ["legal", "accounting"],
        "max_data_access_level": 2,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 16
    },

    # ========================================================================
    # MANAGERS (Niveau 4)
    # ========================================================================
    "SALES_MANAGER": {
        "code": "SALES_MANAGER",
        "name": "Responsable Commercial",
        "description": "Responsable équipe commerciale",
        "level": "MANAGER",
        "hierarchy_order": 4,
        "title_patterns": [
            "Responsable Commercial", "Sales Manager",
            "Chef des Ventes", "Team Leader Sales",
            "Responsable Grands Comptes"
        ],
        "department_patterns": ["Commercial", "Ventes", "Sales"],
        "default_roles": ["COMMERCIAL"],
        "default_permissions": [
            "sales.quote.*", "sales.order.*", "sales.customer.*",
            "stock.item.read"
        ],
        "default_modules": ["sales", "stock"],
        "max_data_access_level": 3,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 20
    },

    "ACCOUNTING_MANAGER": {
        "code": "ACCOUNTING_MANAGER",
        "name": "Responsable Comptable",
        "description": "Responsable équipe comptabilité",
        "level": "MANAGER",
        "hierarchy_order": 4,
        "title_patterns": [
            "Responsable Comptable", "Chef Comptable",
            "Accounting Manager", "Senior Accountant"
        ],
        "department_patterns": ["Comptabilité", "Accounting", "Finance"],
        "default_roles": ["COMPTABLE"],
        "default_permissions": [
            "accounting.*", "treasury.forecast.read",
            "sales.invoice.read", "purchase.invoice.read"
        ],
        "default_modules": ["accounting", "treasury"],
        "max_data_access_level": 2,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 21
    },

    "HR_MANAGER": {
        "code": "HR_MANAGER",
        "name": "Responsable RH",
        "description": "Responsable équipe ressources humaines",
        "level": "MANAGER",
        "hierarchy_order": 4,
        "title_patterns": [
            "Responsable RH", "HR Manager",
            "Responsable Recrutement", "Responsable Paie"
        ],
        "department_patterns": ["RH", "Ressources Humaines", "Human Resources"],
        "default_roles": ["RH"],
        "default_permissions": ["hr.employee.*", "hr.leave.*"],
        "default_modules": ["hr"],
        "max_data_access_level": 3,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 22
    },

    "WAREHOUSE_MANAGER": {
        "code": "WAREHOUSE_MANAGER",
        "name": "Responsable Logistique",
        "description": "Responsable entrepôt et logistique",
        "level": "MANAGER",
        "hierarchy_order": 4,
        "title_patterns": [
            "Responsable Logistique", "Chef d'Entrepôt",
            "Warehouse Manager", "Logistics Manager",
            "Responsable Stock"
        ],
        "department_patterns": ["Logistique", "Entrepôt", "Warehouse", "Stock"],
        "default_roles": ["MAGASINIER"],
        "default_permissions": ["stock.*"],
        "default_modules": ["stock"],
        "max_data_access_level": 3,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 23
    },

    # ========================================================================
    # SPÉCIALISTES (Niveau 5)
    # ========================================================================
    "ACCOUNTANT": {
        "code": "ACCOUNTANT",
        "name": "Comptable",
        "description": "Comptable opérationnel",
        "level": "SPECIALIST",
        "hierarchy_order": 5,
        "title_patterns": [
            "Comptable", "Accountant", "Assistant Comptable",
            "Comptable Fournisseurs", "Comptable Clients"
        ],
        "department_patterns": ["Comptabilité", "Accounting", "Finance"],
        "default_roles": ["COMPTABLE"],
        "default_permissions": [
            "accounting.entry.create", "accounting.entry.read",
            "accounting.entry.update", "accounting.report.read"
        ],
        "default_modules": ["accounting"],
        "max_data_access_level": 4,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 30
    },

    "SALES_REP": {
        "code": "SALES_REP",
        "name": "Commercial",
        "description": "Commercial terrain ou sédentaire",
        "level": "SPECIALIST",
        "hierarchy_order": 5,
        "title_patterns": [
            "Commercial", "Sales Representative",
            "Attaché Commercial", "Conseiller Commercial",
            "Account Manager", "Business Developer"
        ],
        "department_patterns": ["Commercial", "Ventes", "Sales"],
        "default_roles": ["COMMERCIAL"],
        "default_permissions": [
            "sales.quote.create", "sales.quote.read", "sales.quote.update",
            "sales.customer.create", "sales.customer.read",
            "stock.item.read"
        ],
        "default_modules": ["sales"],
        "max_data_access_level": 4,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 31
    },

    "BUYER": {
        "code": "BUYER",
        "name": "Acheteur",
        "description": "Acheteur opérationnel",
        "level": "SPECIALIST",
        "hierarchy_order": 5,
        "title_patterns": [
            "Acheteur", "Buyer", "Approvisionneur",
            "Assistant Achats", "Purchasing Agent"
        ],
        "department_patterns": ["Achats", "Procurement", "Purchasing"],
        "default_roles": ["ACHETEUR"],
        "default_permissions": [
            "purchase.order.create", "purchase.order.read",
            "purchase.supplier.create", "purchase.supplier.read",
            "stock.item.read"
        ],
        "default_modules": ["purchase"],
        "max_data_access_level": 4,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 32
    },

    "HR_OFFICER": {
        "code": "HR_OFFICER",
        "name": "Chargé RH",
        "description": "Chargé des ressources humaines",
        "level": "SPECIALIST",
        "hierarchy_order": 5,
        "title_patterns": [
            "Chargé RH", "HR Officer", "Gestionnaire RH",
            "Assistant RH", "Chargé de Recrutement"
        ],
        "department_patterns": ["RH", "Ressources Humaines", "Human Resources"],
        "default_roles": ["RH"],
        "default_permissions": [
            "hr.employee.read", "hr.employee.update",
            "hr.leave.create", "hr.leave.read"
        ],
        "default_modules": ["hr"],
        "max_data_access_level": 4,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 33
    },

    # ========================================================================
    # OPÉRATEURS (Niveau 6)
    # ========================================================================
    "WAREHOUSE_OPERATOR": {
        "code": "WAREHOUSE_OPERATOR",
        "name": "Magasinier / Préparateur",
        "description": "Opérateur logistique",
        "level": "OPERATOR",
        "hierarchy_order": 6,
        "title_patterns": [
            "Magasinier", "Préparateur", "Cariste",
            "Warehouse Operator", "Stock Handler"
        ],
        "department_patterns": ["Logistique", "Entrepôt", "Warehouse", "Stock"],
        "default_roles": ["MAGASINIER"],
        "default_permissions": [
            "stock.item.read", "stock.movement.create", "stock.movement.read"
        ],
        "default_modules": ["stock"],
        "max_data_access_level": 5,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 40
    },

    "RECEPTIONIST": {
        "code": "RECEPTIONIST",
        "name": "Accueil / Secrétariat",
        "description": "Accueil et secrétariat",
        "level": "OPERATOR",
        "hierarchy_order": 6,
        "title_patterns": [
            "Réceptionniste", "Secrétaire", "Accueil",
            "Receptionist", "Secretary", "Administrative Assistant"
        ],
        "department_patterns": ["Accueil", "Administration", "Reception"],
        "default_roles": ["CONSULTANT"],
        "default_permissions": [],
        "default_modules": [],
        "max_data_access_level": 5,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 41
    },

    # ========================================================================
    # EXTERNES (Niveau 7)
    # ========================================================================
    "AUDITOR": {
        "code": "AUDITOR",
        "name": "Auditeur",
        "description": "Auditeur externe ou interne",
        "level": "EXTERNAL",
        "hierarchy_order": 7,
        "title_patterns": [
            "Auditeur", "Auditor", "Commissaire aux Comptes",
            "Expert Comptable", "Contrôleur"
        ],
        "department_patterns": ["Audit", "External", "Contrôle"],
        "default_roles": ["AUDITEUR"],
        "default_permissions": [
            "iam.audit.read", "accounting.entry.read", "accounting.report.read",
            "treasury.report.read", "decision.journal.read"
        ],
        "default_modules": ["accounting", "treasury"],
        "max_data_access_level": 3,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 50
    },

    "CONSULTANT": {
        "code": "CONSULTANT",
        "name": "Consultant",
        "description": "Consultant externe",
        "level": "EXTERNAL",
        "hierarchy_order": 7,
        "title_patterns": [
            "Consultant", "Conseiller", "Expert",
            "Contractor", "Freelance"
        ],
        "department_patterns": ["External", "Consulting"],
        "default_roles": ["CONSULTANT"],
        "default_permissions": [],
        "default_modules": [],
        "max_data_access_level": 4,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 51
    },

    "INTERN": {
        "code": "INTERN",
        "name": "Stagiaire",
        "description": "Stagiaire ou alternant",
        "level": "EXTERNAL",
        "hierarchy_order": 7,
        "title_patterns": [
            "Stagiaire", "Alternant", "Apprenti",
            "Intern", "Trainee"
        ],
        "department_patterns": [],  # Tous départements
        "default_roles": ["CONSULTANT"],
        "default_permissions": [],
        "default_modules": [],
        "max_data_access_level": 5,
        "requires_mfa": False,
        "requires_training": True,
        "priority": 52
    },

    "IT_ADMIN": {
        "code": "IT_ADMIN",
        "name": "Administrateur IT",
        "description": "Administrateur système/réseau",
        "level": "SPECIALIST",
        "hierarchy_order": 5,
        "title_patterns": [
            "Administrateur", "Admin IT", "Sysadmin",
            "IT Administrator", "System Administrator",
            "Responsable IT", "Technicien IT"
        ],
        "department_patterns": ["IT", "Informatique", "DSI"],
        "default_roles": ["TENANT_ADMIN"],
        "default_permissions": ["iam.*", "admin.*"],
        "default_modules": ["admin"],
        "max_data_access_level": 2,
        "requires_mfa": True,
        "requires_training": True,
        "priority": 25
    },
}


# ============================================================================
# FONCTIONS UTILITAIRES
# ============================================================================

def get_profile_by_code(code: str) -> dict[str, Any]:
    """Retourne un profil par son code."""
    return PREDEFINED_PROFILES.get(code)


def get_all_profiles() -> dict[str, dict[str, Any]]:
    """Retourne tous les profils."""
    return PREDEFINED_PROFILES


def get_profiles_by_level(level: str) -> dict[str, dict[str, Any]]:
    """Retourne les profils d'un niveau donné."""
    return {
        code: profile for code, profile in PREDEFINED_PROFILES.items()
        if profile["level"] == level
    }


def match_profile_by_title(title: str) -> list[dict[str, Any]]:
    """
    Trouve les profils correspondant à un titre.
    Retourne les profils triés par priorité (plus bas = plus prioritaire).
    """
    import re
    title_lower = title.lower()
    matches = []

    for code, profile in PREDEFINED_PROFILES.items():
        for pattern in profile.get("title_patterns", []):
            pattern_lower = pattern.lower()
            # Convertir le pattern en regex (support du *)
            regex_pattern = pattern_lower.replace("*", ".*")
            if re.search(regex_pattern, title_lower):
                matches.append({"code": code, **profile})
                break

    # Trier par priorité
    return sorted(matches, key=lambda x: x["priority"])


def match_profile_by_department(department: str) -> list[dict[str, Any]]:
    """
    Trouve les profils correspondant à un département.
    """
    department_lower = department.lower()
    matches = []

    for code, profile in PREDEFINED_PROFILES.items():
        for pattern in profile.get("department_patterns", []):
            if pattern.lower() in department_lower or department_lower in pattern.lower():
                matches.append({"code": code, **profile})
                break

    return sorted(matches, key=lambda x: x["priority"])


def get_best_profile_match(title: str, department: str = None) -> dict[str, Any]:
    """
    Trouve le meilleur profil correspondant à un titre et département.
    """
    # D'abord essayer par titre
    title_matches = match_profile_by_title(title)

    if title_matches:
        # Si département fourni, affiner
        if department:
            for match in title_matches:
                dept_patterns = match.get("department_patterns", [])
                if not dept_patterns:  # Profil applicable à tous départements
                    return match
                for pattern in dept_patterns:
                    if pattern.lower() in department.lower() or department.lower() in pattern.lower():
                        return match
        # Retourner le premier match par titre
        return title_matches[0]

    # Si pas de match par titre, essayer par département
    if department:
        dept_matches = match_profile_by_department(department)
        if dept_matches:
            return dept_matches[0]

    # Profil par défaut
    return PREDEFINED_PROFILES.get("CONSULTANT")
