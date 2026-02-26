"""
Service Training / Formation - GAP-064

Gestion des formations:
- Catalogue de formations
- Sessions et planning
- Inscriptions et présences
- Évaluations et certifications
- Formateurs et compétences
- Suivi des acquis
- E-learning intégré
- Budget formation
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class TrainingType(str, Enum):
    """Type de formation."""
    CLASSROOM = "classroom"
    ONLINE = "online"
    BLENDED = "blended"
    ON_THE_JOB = "on_the_job"
    WORKSHOP = "workshop"
    SEMINAR = "seminar"
    CERTIFICATION = "certification"


class TrainingLevel(str, Enum):
    """Niveau de formation."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class SessionStatus(str, Enum):
    """Statut d'une session."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EnrollmentStatus(str, Enum):
    """Statut d'inscription."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    WAITLISTED = "waitlisted"
    ATTENDED = "attended"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    CANCELLED = "cancelled"


class EvaluationType(str, Enum):
    """Type d'évaluation."""
    PRE_ASSESSMENT = "pre_assessment"
    POST_ASSESSMENT = "post_assessment"
    QUIZ = "quiz"
    PRACTICAL = "practical"
    PROJECT = "project"
    CERTIFICATION = "certification"


class ContentType(str, Enum):
    """Type de contenu e-learning."""
    VIDEO = "video"
    DOCUMENT = "document"
    PRESENTATION = "presentation"
    QUIZ = "quiz"
    INTERACTIVE = "interactive"
    SCORM = "scorm"


class CertificateStatus(str, Enum):
    """Statut de certification."""
    PENDING = "pending"
    ISSUED = "issued"
    EXPIRED = "expired"
    REVOKED = "revoked"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class TrainingCategory:
    """Catégorie de formation."""
    id: str
    tenant_id: str
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True


@dataclass
class TrainingCourse:
    """Un cours de formation."""
    id: str
    tenant_id: str
    code: str
    name: str
    description: str
    category_id: Optional[str] = None
    training_type: TrainingType = TrainingType.CLASSROOM
    level: TrainingLevel = TrainingLevel.BEGINNER
    duration_hours: int = 0
    min_participants: int = 1
    max_participants: int = 20
    objectives: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    target_audience: List[str] = field(default_factory=list)
    skills_acquired: List[str] = field(default_factory=list)
    materials_required: List[str] = field(default_factory=list)
    cost_per_participant: Decimal = Decimal("0")
    cost_per_session: Decimal = Decimal("0")
    currency: str = "EUR"
    certification_available: bool = False
    certification_validity_months: Optional[int] = None
    has_elearning: bool = False
    elearning_modules: List[str] = field(default_factory=list)
    rating_avg: Decimal = Decimal("0")
    rating_count: int = 0
    total_sessions: int = 0
    total_participants: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Trainer:
    """Un formateur."""
    id: str
    tenant_id: str
    user_id: Optional[str] = None
    first_name: str = ""
    last_name: str = ""
    email: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    specializations: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    hourly_rate: Decimal = Decimal("0")
    daily_rate: Decimal = Decimal("0")
    currency: str = "EUR"
    is_internal: bool = True
    company_name: Optional[str] = None
    rating_avg: Decimal = Decimal("0")
    rating_count: int = 0
    total_sessions: int = 0
    total_hours: int = 0
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrainingSession:
    """Une session de formation."""
    id: str
    tenant_id: str
    course_id: str
    course_name: str
    trainer_id: Optional[str] = None
    trainer_name: Optional[str] = None
    status: SessionStatus = SessionStatus.DRAFT
    start_date: date = field(default_factory=date.today)
    end_date: Optional[date] = None
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None
    location: Optional[str] = None
    room: Optional[str] = None
    is_virtual: bool = False
    virtual_link: Optional[str] = None
    max_participants: int = 20
    enrolled_count: int = 0
    waitlist_count: int = 0
    attendance_count: int = 0
    cost_total: Decimal = Decimal("0")
    materials_provided: List[str] = field(default_factory=list)
    schedule: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Enrollment:
    """Une inscription à une session."""
    id: str
    tenant_id: str
    session_id: str
    participant_id: str
    participant_name: str
    participant_email: Optional[str] = None
    department: Optional[str] = None
    status: EnrollmentStatus = EnrollmentStatus.PENDING
    enrolled_at: datetime = field(default_factory=datetime.now)
    confirmed_at: Optional[datetime] = None
    attendance_dates: List[date] = field(default_factory=list)
    completion_date: Optional[date] = None
    completion_rate: Decimal = Decimal("0")
    pre_assessment_score: Optional[Decimal] = None
    post_assessment_score: Optional[Decimal] = None
    score_improvement: Optional[Decimal] = None
    certificate_id: Optional[str] = None
    feedback_submitted: bool = False
    manager_approval_required: bool = False
    manager_approved: bool = False
    manager_approved_by: Optional[str] = None
    cost_charged: Decimal = Decimal("0")
    notes: Optional[str] = None


@dataclass
class Attendance:
    """Présence à une session."""
    id: str
    enrollment_id: str
    session_id: str
    participant_id: str
    date: date
    check_in_time: Optional[datetime] = None
    check_out_time: Optional[datetime] = None
    duration_minutes: int = 0
    is_present: bool = True
    is_late: bool = False
    absence_reason: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class Evaluation:
    """Évaluation d'un participant."""
    id: str
    tenant_id: str
    session_id: str
    participant_id: str
    evaluation_type: EvaluationType
    title: str
    max_score: int = 100
    passing_score: int = 60
    score: Optional[int] = None
    passed: bool = False
    time_taken_minutes: Optional[int] = None
    attempts: int = 1
    max_attempts: int = 3
    questions: List[Dict[str, Any]] = field(default_factory=list)
    answers: List[Dict[str, Any]] = field(default_factory=list)
    feedback: Optional[str] = None
    evaluated_by: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Certificate:
    """Certificat de formation."""
    id: str
    tenant_id: str
    participant_id: str
    participant_name: str
    course_id: str
    course_name: str
    session_id: str
    certificate_number: str
    status: CertificateStatus = CertificateStatus.PENDING
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    score: Optional[int] = None
    grade: Optional[str] = None
    skills_certified: List[str] = field(default_factory=list)
    issued_by: Optional[str] = None
    file_id: Optional[str] = None
    verification_url: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ELearningModule:
    """Module e-learning."""
    id: str
    tenant_id: str
    course_id: str
    title: str
    description: Optional[str] = None
    order: int = 0
    content_type: ContentType = ContentType.VIDEO
    content_url: Optional[str] = None
    file_id: Optional[str] = None
    duration_minutes: int = 0
    is_mandatory: bool = True
    passing_score: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ModuleProgress:
    """Progression sur un module."""
    id: str
    participant_id: str
    module_id: str
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress_percent: Decimal = Decimal("0")
    time_spent_minutes: int = 0
    score: Optional[int] = None
    attempts: int = 0


@dataclass
class SessionFeedback:
    """Feedback sur une session."""
    id: str
    session_id: str
    participant_id: str
    overall_rating: int  # 1-5
    content_rating: int
    trainer_rating: int
    materials_rating: int
    venue_rating: Optional[int] = None
    would_recommend: bool = True
    strengths: Optional[str] = None
    improvements: Optional[str] = None
    additional_comments: Optional[str] = None
    submitted_at: datetime = field(default_factory=datetime.now)


@dataclass
class TrainingBudget:
    """Budget formation."""
    id: str
    tenant_id: str
    year: int
    department: Optional[str] = None
    allocated_amount: Decimal = Decimal("0")
    spent_amount: Decimal = Decimal("0")
    committed_amount: Decimal = Decimal("0")
    remaining_amount: Decimal = Decimal("0")
    currency: str = "EUR"
    target_hours_per_employee: int = 0
    actual_hours_per_employee: Decimal = Decimal("0")


@dataclass
class TrainingStats:
    """Statistiques de formation."""
    tenant_id: str
    period_start: date
    period_end: date
    total_courses: int = 0
    total_sessions: int = 0
    sessions_completed: int = 0
    total_participants: int = 0
    unique_participants: int = 0
    total_hours: int = 0
    completion_rate: Decimal = Decimal("0")
    avg_satisfaction: Decimal = Decimal("0")
    avg_score_improvement: Decimal = Decimal("0")
    certificates_issued: int = 0
    total_cost: Decimal = Decimal("0")
    cost_per_hour: Decimal = Decimal("0")


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class TrainingService:
    """Service de gestion des formations."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (simulation)
        self._categories: Dict[str, TrainingCategory] = {}
        self._courses: Dict[str, TrainingCourse] = {}
        self._trainers: Dict[str, Trainer] = {}
        self._sessions: Dict[str, TrainingSession] = {}
        self._enrollments: Dict[str, Enrollment] = {}
        self._attendance: Dict[str, Attendance] = {}
        self._evaluations: Dict[str, Evaluation] = {}
        self._certificates: Dict[str, Certificate] = {}
        self._modules: Dict[str, ELearningModule] = {}
        self._progress: Dict[str, ModuleProgress] = {}
        self._feedback: Dict[str, SessionFeedback] = {}
        self._budgets: Dict[str, TrainingBudget] = {}

        self._certificate_counter = 0

    # -------------------------------------------------------------------------
    # Cours
    # -------------------------------------------------------------------------

    def create_course(
        self,
        code: str,
        name: str,
        description: str,
        training_type: TrainingType = TrainingType.CLASSROOM,
        level: TrainingLevel = TrainingLevel.BEGINNER,
        **kwargs
    ) -> TrainingCourse:
        """Crée un cours."""
        course_id = str(uuid4())

        course = TrainingCourse(
            id=course_id,
            tenant_id=self.tenant_id,
            code=code,
            name=name,
            description=description,
            training_type=training_type,
            level=level,
            **kwargs
        )

        self._courses[course_id] = course
        return course

    def get_course(self, course_id: str) -> Optional[TrainingCourse]:
        """Récupère un cours."""
        course = self._courses.get(course_id)
        if course and course.tenant_id == self.tenant_id:
            return course
        return None

    def list_courses(
        self,
        *,
        category_id: Optional[str] = None,
        training_type: Optional[TrainingType] = None,
        level: Optional[TrainingLevel] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TrainingCourse], int]:
        """Liste les cours."""
        results = []

        for course in self._courses.values():
            if course.tenant_id != self.tenant_id:
                continue
            if not course.is_active:
                continue
            if category_id and course.category_id != category_id:
                continue
            if training_type and course.training_type != training_type:
                continue
            if level and course.level != level:
                continue
            if search:
                search_lower = search.lower()
                if (search_lower not in course.name.lower() and
                    search_lower not in course.description.lower()):
                    continue
            results.append(course)

        results.sort(key=lambda x: x.name)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    # -------------------------------------------------------------------------
    # Formateurs
    # -------------------------------------------------------------------------

    def create_trainer(
        self,
        first_name: str,
        last_name: str,
        email: Optional[str] = None,
        **kwargs
    ) -> Trainer:
        """Crée un formateur."""
        trainer_id = str(uuid4())

        trainer = Trainer(
            id=trainer_id,
            tenant_id=self.tenant_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            **kwargs
        )

        self._trainers[trainer_id] = trainer
        return trainer

    def get_trainer(self, trainer_id: str) -> Optional[Trainer]:
        """Récupère un formateur."""
        trainer = self._trainers.get(trainer_id)
        if trainer and trainer.tenant_id == self.tenant_id:
            return trainer
        return None

    def list_trainers(
        self,
        *,
        specialization: Optional[str] = None,
        is_internal: Optional[bool] = None,
        is_active: bool = True
    ) -> List[Trainer]:
        """Liste les formateurs."""
        results = []

        for trainer in self._trainers.values():
            if trainer.tenant_id != self.tenant_id:
                continue
            if trainer.is_active != is_active:
                continue
            if is_internal is not None and trainer.is_internal != is_internal:
                continue
            if specialization and specialization not in trainer.specializations:
                continue
            results.append(trainer)

        results.sort(key=lambda x: (x.last_name, x.first_name))
        return results

    # -------------------------------------------------------------------------
    # Sessions
    # -------------------------------------------------------------------------

    def create_session(
        self,
        course_id: str,
        start_date: date,
        trainer_id: Optional[str] = None,
        **kwargs
    ) -> Optional[TrainingSession]:
        """Crée une session."""
        course = self.get_course(course_id)
        if not course:
            return None

        trainer = None
        trainer_name = None
        if trainer_id:
            trainer = self.get_trainer(trainer_id)
            if trainer:
                trainer_name = f"{trainer.first_name} {trainer.last_name}"

        session_id = str(uuid4())

        session = TrainingSession(
            id=session_id,
            tenant_id=self.tenant_id,
            course_id=course_id,
            course_name=course.name,
            trainer_id=trainer_id,
            trainer_name=trainer_name,
            start_date=start_date,
            max_participants=course.max_participants,
            **kwargs
        )

        self._sessions[session_id] = session

        # Mettre à jour compteur du cours
        course.total_sessions += 1

        return session

    def get_session(self, session_id: str) -> Optional[TrainingSession]:
        """Récupère une session."""
        session = self._sessions.get(session_id)
        if session and session.tenant_id == self.tenant_id:
            return session
        return None

    def update_session_status(
        self,
        session_id: str,
        status: SessionStatus
    ) -> Optional[TrainingSession]:
        """Met à jour le statut d'une session."""
        session = self.get_session(session_id)
        if not session:
            return None

        session.status = status
        session.updated_at = datetime.now()

        if status == SessionStatus.COMPLETED:
            # Mettre à jour les statistiques du formateur
            if session.trainer_id:
                trainer = self.get_trainer(session.trainer_id)
                if trainer:
                    trainer.total_sessions += 1

        return session

    def list_sessions(
        self,
        *,
        course_id: Optional[str] = None,
        trainer_id: Optional[str] = None,
        status: Optional[SessionStatus] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[TrainingSession], int]:
        """Liste les sessions."""
        results = []

        for session in self._sessions.values():
            if session.tenant_id != self.tenant_id:
                continue
            if course_id and session.course_id != course_id:
                continue
            if trainer_id and session.trainer_id != trainer_id:
                continue
            if status and session.status != status:
                continue
            if from_date and session.start_date < from_date:
                continue
            if to_date and session.start_date > to_date:
                continue
            results.append(session)

        results.sort(key=lambda x: x.start_date, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    # -------------------------------------------------------------------------
    # Inscriptions
    # -------------------------------------------------------------------------

    def enroll_participant(
        self,
        session_id: str,
        participant_id: str,
        participant_name: str,
        participant_email: Optional[str] = None,
        **kwargs
    ) -> Optional[Enrollment]:
        """Inscrit un participant."""
        session = self.get_session(session_id)
        if not session:
            return None

        # Vérifier si déjà inscrit
        for enrollment in self._enrollments.values():
            if (enrollment.session_id == session_id and
                enrollment.participant_id == participant_id and
                enrollment.status not in [EnrollmentStatus.CANCELLED]):
                return None

        enrollment_id = str(uuid4())
        status = EnrollmentStatus.PENDING

        # Gérer la liste d'attente
        if session.enrolled_count >= session.max_participants:
            status = EnrollmentStatus.WAITLISTED
            session.waitlist_count += 1
        else:
            session.enrolled_count += 1

        enrollment = Enrollment(
            id=enrollment_id,
            tenant_id=self.tenant_id,
            session_id=session_id,
            participant_id=participant_id,
            participant_name=participant_name,
            participant_email=participant_email,
            status=status,
            **kwargs
        )

        self._enrollments[enrollment_id] = enrollment

        return enrollment

    def confirm_enrollment(
        self,
        enrollment_id: str
    ) -> Optional[Enrollment]:
        """Confirme une inscription."""
        enrollment = self._enrollments.get(enrollment_id)
        if not enrollment or enrollment.tenant_id != self.tenant_id:
            return None

        if enrollment.status != EnrollmentStatus.PENDING:
            return None

        enrollment.status = EnrollmentStatus.CONFIRMED
        enrollment.confirmed_at = datetime.now()

        return enrollment

    def cancel_enrollment(
        self,
        enrollment_id: str
    ) -> Optional[Enrollment]:
        """Annule une inscription."""
        enrollment = self._enrollments.get(enrollment_id)
        if not enrollment or enrollment.tenant_id != self.tenant_id:
            return None

        was_confirmed = enrollment.status == EnrollmentStatus.CONFIRMED
        enrollment.status = EnrollmentStatus.CANCELLED

        # Libérer la place
        session = self.get_session(enrollment.session_id)
        if session and was_confirmed:
            session.enrolled_count -= 1

            # Promouvoir quelqu'un de la liste d'attente
            self._promote_from_waitlist(session.id)

        return enrollment

    def _promote_from_waitlist(self, session_id: str):
        """Promeut le premier de la liste d'attente."""
        session = self.get_session(session_id)
        if not session:
            return

        # Trouver le premier en liste d'attente
        waitlisted = [
            e for e in self._enrollments.values()
            if e.session_id == session_id and e.status == EnrollmentStatus.WAITLISTED
        ]

        if waitlisted:
            waitlisted.sort(key=lambda x: x.enrolled_at)
            first = waitlisted[0]
            first.status = EnrollmentStatus.PENDING
            session.waitlist_count -= 1
            session.enrolled_count += 1

    def record_attendance(
        self,
        enrollment_id: str,
        date: date,
        is_present: bool = True,
        check_in_time: Optional[datetime] = None,
        **kwargs
    ) -> Optional[Attendance]:
        """Enregistre une présence."""
        enrollment = self._enrollments.get(enrollment_id)
        if not enrollment:
            return None

        attendance_id = str(uuid4())

        attendance = Attendance(
            id=attendance_id,
            enrollment_id=enrollment_id,
            session_id=enrollment.session_id,
            participant_id=enrollment.participant_id,
            date=date,
            is_present=is_present,
            check_in_time=check_in_time,
            **kwargs
        )

        self._attendance[attendance_id] = attendance

        # Mettre à jour l'inscription
        if is_present:
            enrollment.attendance_dates.append(date)
            enrollment.status = EnrollmentStatus.ATTENDED

            # Mettre à jour la session
            session = self.get_session(enrollment.session_id)
            if session:
                session.attendance_count = len(set(
                    a.participant_id for a in self._attendance.values()
                    if a.session_id == session.id and a.is_present
                ))

        return attendance

    def complete_enrollment(
        self,
        enrollment_id: str,
        score: Optional[int] = None
    ) -> Optional[Enrollment]:
        """Termine une inscription (formation complétée)."""
        enrollment = self._enrollments.get(enrollment_id)
        if not enrollment or enrollment.tenant_id != self.tenant_id:
            return None

        enrollment.status = EnrollmentStatus.COMPLETED
        enrollment.completion_date = date.today()
        enrollment.completion_rate = Decimal("100")
        enrollment.post_assessment_score = Decimal(score) if score else None

        # Calculer l'amélioration
        if enrollment.pre_assessment_score and enrollment.post_assessment_score:
            enrollment.score_improvement = (
                enrollment.post_assessment_score - enrollment.pre_assessment_score
            )

        # Mettre à jour le cours
        session = self.get_session(enrollment.session_id)
        if session:
            course = self.get_course(session.course_id)
            if course:
                course.total_participants += 1

        return enrollment

    def list_enrollments(
        self,
        session_id: Optional[str] = None,
        participant_id: Optional[str] = None,
        status: Optional[EnrollmentStatus] = None
    ) -> List[Enrollment]:
        """Liste les inscriptions."""
        results = []

        for enrollment in self._enrollments.values():
            if enrollment.tenant_id != self.tenant_id:
                continue
            if session_id and enrollment.session_id != session_id:
                continue
            if participant_id and enrollment.participant_id != participant_id:
                continue
            if status and enrollment.status != status:
                continue
            results.append(enrollment)

        results.sort(key=lambda x: x.enrolled_at, reverse=True)
        return results

    # -------------------------------------------------------------------------
    # Évaluations
    # -------------------------------------------------------------------------

    def create_evaluation(
        self,
        session_id: str,
        participant_id: str,
        evaluation_type: EvaluationType,
        title: str,
        max_score: int = 100,
        passing_score: int = 60,
        questions: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Evaluation]:
        """Crée une évaluation."""
        evaluation_id = str(uuid4())

        evaluation = Evaluation(
            id=evaluation_id,
            tenant_id=self.tenant_id,
            session_id=session_id,
            participant_id=participant_id,
            evaluation_type=evaluation_type,
            title=title,
            max_score=max_score,
            passing_score=passing_score,
            questions=questions or []
        )

        self._evaluations[evaluation_id] = evaluation
        return evaluation

    def submit_evaluation(
        self,
        evaluation_id: str,
        answers: List[Dict[str, Any]],
        score: int,
        time_taken_minutes: Optional[int] = None
    ) -> Optional[Evaluation]:
        """Soumet une évaluation."""
        evaluation = self._evaluations.get(evaluation_id)
        if not evaluation or evaluation.tenant_id != self.tenant_id:
            return None

        evaluation.answers = answers
        evaluation.score = score
        evaluation.passed = score >= evaluation.passing_score
        evaluation.time_taken_minutes = time_taken_minutes
        evaluation.evaluated_at = datetime.now()

        # Mettre à jour l'inscription
        for enrollment in self._enrollments.values():
            if (enrollment.session_id == evaluation.session_id and
                enrollment.participant_id == evaluation.participant_id):

                if evaluation.evaluation_type == EvaluationType.PRE_ASSESSMENT:
                    enrollment.pre_assessment_score = Decimal(score)
                elif evaluation.evaluation_type == EvaluationType.POST_ASSESSMENT:
                    enrollment.post_assessment_score = Decimal(score)

        return evaluation

    # -------------------------------------------------------------------------
    # Certificats
    # -------------------------------------------------------------------------

    def issue_certificate(
        self,
        enrollment_id: str,
        issued_by: Optional[str] = None
    ) -> Optional[Certificate]:
        """Délivre un certificat."""
        enrollment = self._enrollments.get(enrollment_id)
        if not enrollment or enrollment.tenant_id != self.tenant_id:
            return None

        if enrollment.status != EnrollmentStatus.COMPLETED:
            return None

        session = self.get_session(enrollment.session_id)
        if not session:
            return None

        course = self.get_course(session.course_id)
        if not course:
            return None

        self._certificate_counter += 1
        cert_number = f"CERT-{datetime.now().strftime('%Y')}-{self._certificate_counter:06d}"

        certificate_id = str(uuid4())

        # Calculer expiration
        expiry_date = None
        if course.certification_validity_months:
            expiry_date = date.today() + timedelta(days=course.certification_validity_months * 30)

        certificate = Certificate(
            id=certificate_id,
            tenant_id=self.tenant_id,
            participant_id=enrollment.participant_id,
            participant_name=enrollment.participant_name,
            course_id=course.id,
            course_name=course.name,
            session_id=session.id,
            certificate_number=cert_number,
            status=CertificateStatus.ISSUED,
            issue_date=date.today(),
            expiry_date=expiry_date,
            score=int(enrollment.post_assessment_score) if enrollment.post_assessment_score else None,
            skills_certified=course.skills_acquired,
            issued_by=issued_by
        )

        self._certificates[certificate_id] = certificate

        # Lier à l'inscription
        enrollment.certificate_id = certificate_id

        return certificate

    def get_certificate(self, certificate_id: str) -> Optional[Certificate]:
        """Récupère un certificat."""
        cert = self._certificates.get(certificate_id)
        if cert and cert.tenant_id == self.tenant_id:
            return cert
        return None

    def verify_certificate(self, certificate_number: str) -> Optional[Certificate]:
        """Vérifie un certificat par son numéro."""
        for cert in self._certificates.values():
            if cert.certificate_number == certificate_number:
                return cert
        return None

    def list_certificates(
        self,
        participant_id: Optional[str] = None,
        course_id: Optional[str] = None,
        status: Optional[CertificateStatus] = None
    ) -> List[Certificate]:
        """Liste les certificats."""
        results = []

        for cert in self._certificates.values():
            if cert.tenant_id != self.tenant_id:
                continue
            if participant_id and cert.participant_id != participant_id:
                continue
            if course_id and cert.course_id != course_id:
                continue
            if status and cert.status != status:
                continue
            results.append(cert)

        results.sort(key=lambda x: x.issue_date or date.min, reverse=True)
        return results

    # -------------------------------------------------------------------------
    # E-Learning
    # -------------------------------------------------------------------------

    def create_module(
        self,
        course_id: str,
        title: str,
        content_type: ContentType,
        **kwargs
    ) -> Optional[ELearningModule]:
        """Crée un module e-learning."""
        course = self.get_course(course_id)
        if not course:
            return None

        module_id = str(uuid4())

        # Déterminer l'ordre
        existing = [m for m in self._modules.values() if m.course_id == course_id]
        order = len(existing)

        module = ELearningModule(
            id=module_id,
            tenant_id=self.tenant_id,
            course_id=course_id,
            title=title,
            content_type=content_type,
            order=order,
            **kwargs
        )

        self._modules[module_id] = module
        course.elearning_modules.append(module_id)
        course.has_elearning = True

        return module

    def track_progress(
        self,
        module_id: str,
        participant_id: str,
        progress_percent: Decimal,
        time_spent_minutes: int = 0
    ) -> Optional[ModuleProgress]:
        """Enregistre la progression sur un module."""
        module = self._modules.get(module_id)
        if not module or module.tenant_id != self.tenant_id:
            return None

        # Chercher progression existante
        progress_key = f"{module_id}:{participant_id}"
        progress = self._progress.get(progress_key)

        if not progress:
            progress = ModuleProgress(
                id=str(uuid4()),
                participant_id=participant_id,
                module_id=module_id,
                started_at=datetime.now()
            )
            self._progress[progress_key] = progress

        progress.progress_percent = progress_percent
        progress.time_spent_minutes += time_spent_minutes

        if progress_percent >= Decimal("100") and not progress.completed_at:
            progress.completed_at = datetime.now()

        return progress

    # -------------------------------------------------------------------------
    # Feedback
    # -------------------------------------------------------------------------

    def submit_feedback(
        self,
        session_id: str,
        participant_id: str,
        overall_rating: int,
        content_rating: int,
        trainer_rating: int,
        materials_rating: int,
        **kwargs
    ) -> Optional[SessionFeedback]:
        """Soumet un feedback."""
        session = self.get_session(session_id)
        if not session:
            return None

        feedback_id = str(uuid4())

        feedback = SessionFeedback(
            id=feedback_id,
            session_id=session_id,
            participant_id=participant_id,
            overall_rating=overall_rating,
            content_rating=content_rating,
            trainer_rating=trainer_rating,
            materials_rating=materials_rating,
            **kwargs
        )

        self._feedback[feedback_id] = feedback

        # Marquer feedback soumis
        for enrollment in self._enrollments.values():
            if (enrollment.session_id == session_id and
                enrollment.participant_id == participant_id):
                enrollment.feedback_submitted = True

        # Mettre à jour moyennes
        self._update_ratings(session)

        return feedback

    def _update_ratings(self, session: TrainingSession):
        """Met à jour les moyennes de notation."""
        feedbacks = [f for f in self._feedback.values() if f.session_id == session.id]

        if not feedbacks:
            return

        # Cours
        course = self.get_course(session.course_id)
        if course:
            total_rating = sum(f.overall_rating for f in feedbacks)
            course.rating_avg = Decimal(total_rating) / len(feedbacks)
            course.rating_count += len(feedbacks)

        # Formateur
        if session.trainer_id:
            trainer = self.get_trainer(session.trainer_id)
            if trainer:
                trainer_feedbacks = [f for f in feedbacks]
                total_rating = sum(f.trainer_rating for f in trainer_feedbacks)
                trainer.rating_avg = Decimal(total_rating) / len(trainer_feedbacks)
                trainer.rating_count += len(trainer_feedbacks)

    # -------------------------------------------------------------------------
    # Statistiques
    # -------------------------------------------------------------------------

    def get_statistics(
        self,
        period_start: date,
        period_end: date
    ) -> TrainingStats:
        """Calcule les statistiques."""
        stats = TrainingStats(
            tenant_id=self.tenant_id,
            period_start=period_start,
            period_end=period_end
        )

        participants = set()
        satisfaction_scores = []
        improvements = []

        stats.total_courses = len([
            c for c in self._courses.values()
            if c.tenant_id == self.tenant_id and c.is_active
        ])

        for session in self._sessions.values():
            if session.tenant_id != self.tenant_id:
                continue
            if session.start_date < period_start or session.start_date > period_end:
                continue

            stats.total_sessions += 1

            if session.status == SessionStatus.COMPLETED:
                stats.sessions_completed += 1

            stats.total_participants += session.enrolled_count

            # Durée
            course = self.get_course(session.course_id)
            if course:
                stats.total_hours += course.duration_hours

        for enrollment in self._enrollments.values():
            if enrollment.tenant_id != self.tenant_id:
                continue

            session = self.get_session(enrollment.session_id)
            if not session:
                continue

            if session.start_date < period_start or session.start_date > period_end:
                continue

            participants.add(enrollment.participant_id)

            if enrollment.status == EnrollmentStatus.COMPLETED:
                if enrollment.score_improvement:
                    improvements.append(float(enrollment.score_improvement))

        stats.unique_participants = len(participants)

        # Satisfaction
        for feedback in self._feedback.values():
            session = self.get_session(feedback.session_id)
            if not session:
                continue
            if session.start_date < period_start or session.start_date > period_end:
                continue
            satisfaction_scores.append(feedback.overall_rating)

        if satisfaction_scores:
            stats.avg_satisfaction = Decimal(sum(satisfaction_scores)) / len(satisfaction_scores)

        if improvements:
            stats.avg_score_improvement = Decimal(sum(improvements)) / len(improvements)

        # Certificats
        stats.certificates_issued = len([
            c for c in self._certificates.values()
            if c.tenant_id == self.tenant_id and
               c.issue_date and
               period_start <= c.issue_date <= period_end
        ])

        # Taux de complétion
        total_enrolled = stats.total_participants
        completed = len([
            e for e in self._enrollments.values()
            if e.status == EnrollmentStatus.COMPLETED
        ])

        if total_enrolled > 0:
            stats.completion_rate = Decimal(completed) / Decimal(total_enrolled) * 100

        return stats


# ============================================================================
# FACTORY
# ============================================================================

def create_training_service(tenant_id: str) -> TrainingService:
    """Factory pour créer un service de formation."""
    return TrainingService(tenant_id)
