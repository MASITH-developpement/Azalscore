"""
Module de Gestion des Temps et Activités (Timesheet) - GAP-034

Fonctionnalités complètes:
- Saisie des temps par projet/tâche/client
- Chronomètre temps réel
- Feuilles de temps hebdomadaires/mensuelles
- Workflow de validation manager
- Calcul heures supplémentaires (Code du travail)
- Gestion absences et congés
- Export paie
- Reporting projet

Conformité: Code du travail (durées max, repos), Convention collective
"""

from .service import (
    # Énumérations
    TimeEntryType,
    AbsenceType,
    TimesheetStatus,
    WorkScheduleType,
    OvertimeType,

    # Data classes
    WorkSchedule,
    TimeEntry,
    AbsenceEntry,
    Timesheet,
    OvertimeCalculation,
    Timer,
    LeaveBalance,

    # Constantes
    LEGAL_LIMITS,
    OVERTIME_RATES,
    PUBLIC_HOLIDAYS_FR_2024,

    # Service
    TimesheetService,
    create_timesheet_service,
)

__all__ = [
    "TimeEntryType",
    "AbsenceType",
    "TimesheetStatus",
    "WorkScheduleType",
    "OvertimeType",
    "WorkSchedule",
    "TimeEntry",
    "AbsenceEntry",
    "Timesheet",
    "OvertimeCalculation",
    "Timer",
    "LeaveBalance",
    "LEGAL_LIMITS",
    "OVERTIME_RATES",
    "PUBLIC_HOLIDAYS_FR_2024",
    "TimesheetService",
    "create_timesheet_service",
]
