"""
Module Time Tracking - GAP-080

Suivi du temps:
- Pointage entrée/sortie
- Feuilles de temps
- Projets et tâches
- Heures facturables
- Approbations
- Overtime et congés
- Rapports et analytics
"""

from .service import (
    # Énumérations
    EntryType,
    TimesheetStatus,
    TimeEntryStatus,
    BillableType,
    OvertimeType,
    AbsenceType,

    # Data classes
    TimePolicy,
    Project,
    Task,
    ClockEntry,
    TimeEntry,
    Timesheet,
    Absence,
    UserTimeBalance,
    TimeReport,

    # Service
    TimeTrackingService,
    create_timetracking_service,
)

__all__ = [
    "EntryType",
    "TimesheetStatus",
    "TimeEntryStatus",
    "BillableType",
    "OvertimeType",
    "AbsenceType",
    "TimePolicy",
    "Project",
    "Task",
    "ClockEntry",
    "TimeEntry",
    "Timesheet",
    "Absence",
    "UserTimeBalance",
    "TimeReport",
    "TimeTrackingService",
    "create_timetracking_service",
]
