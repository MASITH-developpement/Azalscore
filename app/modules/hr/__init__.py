"""
AZALS MODULE M3 - RH (Ressources Humaines)
===========================================

Module métier complet pour la gestion des ressources humaines :
- Employés et contrats
- Départements et postes
- Paie et bulletins de salaire
- Congés et absences
- Temps de travail
- Formation et compétences
- Évaluations de performance
- Documents RH

Version: 1.0.0
Dépendances: T0 (IAM), T5 (Packs Pays), M2 (Finance)
"""

__version__ = "1.0.0"
__module_code__ = "M3"
__module_name__ = "RH - Ressources Humaines"
__dependencies__ = ["T0", "T5", "M2"]

# Types de contrats
CONTRACT_TYPES = [
    "CDI",           # Contrat à durée indéterminée
    "CDD",           # Contrat à durée déterminée
    "INTERIM",       # Intérimaire
    "STAGE",         # Stagiaire
    "APPRENTISSAGE", # Apprenti
    "FREELANCE",     # Indépendant
]

# Statuts employé
EMPLOYEE_STATUSES = [
    "ACTIVE",        # Actif
    "ON_LEAVE",      # En congé
    "SUSPENDED",     # Suspendu
    "TERMINATED",    # Fin de contrat
    "RETIRED",       # Retraité
]

# Types de congés
LEAVE_TYPES = [
    "PAID",          # Congés payés
    "UNPAID",        # Congés sans solde
    "SICK",          # Maladie
    "MATERNITY",     # Maternité
    "PATERNITY",     # Paternité
    "PARENTAL",      # Parental
    "RTT",           # Réduction temps de travail
    "TRAINING",      # Formation
    "SPECIAL",       # Événements familiaux
    "COMPENSATION",  # Récupération
]

# Statuts de demande de congé
LEAVE_STATUSES = [
    "PENDING",       # En attente
    "APPROVED",      # Approuvée
    "REJECTED",      # Refusée
    "CANCELLED",     # Annulée
]

# Statuts paie
PAYROLL_STATUSES = [
    "DRAFT",         # Brouillon
    "CALCULATED",    # Calculée
    "VALIDATED",     # Validée
    "PAID",          # Payée
    "CANCELLED",     # Annulée
]

# Types d'éléments de paie
PAY_ELEMENT_TYPES = [
    "GROSS_SALARY",      # Salaire brut
    "BONUS",             # Prime
    "COMMISSION",        # Commission
    "OVERTIME",          # Heures supplémentaires
    "ALLOWANCE",         # Indemnité
    "DEDUCTION",         # Retenue
    "SOCIAL_CHARGE",     # Charges sociales salarié
    "EMPLOYER_CHARGE",   # Charges patronales
    "TAX",               # Impôt à la source
    "ADVANCE",           # Acompte
    "REIMBURSEMENT",     # Remboursement frais
]

# Types de documents RH
HR_DOCUMENT_TYPES = [
    "CONTRACT",          # Contrat
    "AMENDMENT",         # Avenant
    "PAYSLIP",          # Bulletin de paie
    "CERTIFICATE",      # Attestation
    "WARNING",          # Avertissement
    "EVALUATION",       # Évaluation
    "TRAINING_CERT",    # Certificat formation
    "ID_DOCUMENT",      # Pièce d'identité
    "OTHER",            # Autre
]

# Types d'évaluations
EVALUATION_TYPES = [
    "ANNUAL",           # Annuelle
    "PROBATION",        # Période d'essai
    "PROJECT",          # Projet
    "PROMOTION",        # Promotion
    "EXIT",             # Départ
]

# Statuts évaluation
EVALUATION_STATUSES = [
    "SCHEDULED",        # Planifiée
    "IN_PROGRESS",      # En cours
    "COMPLETED",        # Terminée
    "CANCELLED",        # Annulée
]

# Types de formation
TRAINING_TYPES = [
    "INTERNAL",         # Interne
    "EXTERNAL",         # Externe
    "ONLINE",           # En ligne
    "ON_THE_JOB",       # Sur le poste
    "CERTIFICATION",    # Certification
]

# Catégories employé France (Convention collective)
EMPLOYEE_CATEGORIES_FR = [
    {"code": "EMP", "name": "Employé"},
    {"code": "AM", "name": "Agent de maîtrise"},
    {"code": "CADRE", "name": "Cadre"},
    {"code": "CADRE_SUP", "name": "Cadre supérieur"},
    {"code": "DIRIGEANT", "name": "Dirigeant"},
]

# Cotisations sociales France (simplifiées)
SOCIAL_CONTRIBUTIONS_FR = [
    {"code": "SECU_MAL", "name": "Sécurité Sociale - Maladie", "employee_rate": 0.0, "employer_rate": 7.0},
    {"code": "SECU_VIE", "name": "Sécurité Sociale - Vieillesse", "employee_rate": 6.9, "employer_rate": 8.55},
    {"code": "SECU_FAM", "name": "Allocations familiales", "employee_rate": 0.0, "employer_rate": 5.25},
    {"code": "CHOMAGE", "name": "Assurance chômage", "employee_rate": 0.0, "employer_rate": 4.05},
    {"code": "RETRAITE_C", "name": "Retraite complémentaire", "employee_rate": 3.15, "employer_rate": 4.72},
    {"code": "CSG", "name": "CSG déductible", "employee_rate": 6.8, "employer_rate": 0.0},
    {"code": "CRDS", "name": "CRDS", "employee_rate": 0.5, "employer_rate": 0.0},
]
