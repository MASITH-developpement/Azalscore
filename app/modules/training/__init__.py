"""
Module Training / Formation - GAP-064

Gestion des formations:
- Catalogue de formations
- Sessions et planning
- Inscriptions et présences
- Évaluations et certifications
- Formateurs et compétences
- E-learning intégré
"""

from .service import (
    # Énumérations
    TrainingType,
    TrainingLevel,
    SessionStatus,
    EnrollmentStatus,
    EvaluationType,
    ContentType,
    CertificateStatus,

    # Data classes
    TrainingCategory,
    TrainingCourse,
    Trainer,
    TrainingSession,
    Enrollment,
    Attendance,
    Evaluation,
    Certificate,
    ELearningModule,
    ModuleProgress,
    SessionFeedback,
    TrainingBudget,
    TrainingStats,

    # Service
    TrainingService,
    create_training_service,
)

__all__ = [
    "TrainingType",
    "TrainingLevel",
    "SessionStatus",
    "EnrollmentStatus",
    "EvaluationType",
    "ContentType",
    "CertificateStatus",
    "TrainingCategory",
    "TrainingCourse",
    "Trainer",
    "TrainingSession",
    "Enrollment",
    "Attendance",
    "Evaluation",
    "Certificate",
    "ELearningModule",
    "ModuleProgress",
    "SessionFeedback",
    "TrainingBudget",
    "TrainingStats",
    "TrainingService",
    "create_training_service",
]
