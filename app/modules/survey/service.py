"""
Service Survey / Enquêtes et Feedback - GAP-082

Gestion des enquêtes et retours:
- Création d'enquêtes
- Types de questions variés
- Distribution et collecte
- Analyse des réponses
- Score NPS et satisfaction
- Rapports et tendances
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4


# ============== Énumérations ==============

class SurveyType(str, Enum):
    """Types d'enquête"""
    SATISFACTION = "satisfaction"
    NPS = "nps"
    FEEDBACK = "feedback"
    POLL = "poll"
    QUIZ = "quiz"
    ASSESSMENT = "assessment"
    RESEARCH = "research"
    EXIT_INTERVIEW = "exit_interview"
    ONBOARDING = "onboarding"


class SurveyStatus(str, Enum):
    """Statuts enquête"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


class QuestionType(str, Enum):
    """Types de question"""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_SHORT = "text_short"
    TEXT_LONG = "text_long"
    RATING = "rating"
    NPS = "nps"
    SCALE = "scale"
    DATE = "date"
    MATRIX = "matrix"
    RANKING = "ranking"
    FILE_UPLOAD = "file_upload"
    YES_NO = "yes_no"


class ResponseStatus(str, Enum):
    """Statuts de réponse"""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DistributionChannel(str, Enum):
    """Canaux de distribution"""
    EMAIL = "email"
    SMS = "sms"
    WEB_LINK = "web_link"
    EMBEDDED = "embedded"
    QR_CODE = "qr_code"
    IN_APP = "in_app"


# ============== Data Classes ==============

@dataclass
class QuestionOption:
    """Option de réponse"""
    id: str
    text: str
    value: Optional[str] = None
    score: int = 0
    order: int = 0
    is_other: bool = False


@dataclass
class QuestionLogic:
    """Logique conditionnelle"""
    condition_type: str  # show_if, skip_to, end_survey
    source_question_id: str
    operator: str  # equals, not_equals, contains, greater_than
    value: Any
    target_question_id: Optional[str] = None


@dataclass
class Question:
    """Question d'enquête"""
    id: str
    survey_id: str
    question_type: QuestionType
    text: str
    description: str = ""
    required: bool = False
    order: int = 0

    # Options pour choix
    options: List[QuestionOption] = field(default_factory=list)

    # Configuration rating/scale
    min_value: int = 1
    max_value: int = 5
    min_label: str = ""
    max_label: str = ""

    # Matrix
    rows: List[str] = field(default_factory=list)
    columns: List[str] = field(default_factory=list)

    # Validation
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    regex_pattern: Optional[str] = None
    validation_message: str = ""

    # Logique
    logic_rules: List[QuestionLogic] = field(default_factory=list)

    # Métadonnées
    tags: List[str] = field(default_factory=list)


@dataclass
class Survey:
    """Enquête"""
    id: str
    tenant_id: str
    title: str
    description: str = ""
    survey_type: SurveyType = SurveyType.FEEDBACK
    status: SurveyStatus = SurveyStatus.DRAFT

    # Questions
    questions: List[Question] = field(default_factory=list)

    # Configuration
    welcome_message: str = ""
    thank_you_message: str = ""
    redirect_url: str = ""
    allow_anonymous: bool = False
    allow_multiple_responses: bool = False
    show_progress_bar: bool = True
    randomize_questions: bool = False
    randomize_options: bool = False

    # Planification
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    max_responses: Optional[int] = None

    # Apparence
    theme_color: str = "#007bff"
    logo_url: str = ""
    background_image_url: str = ""

    # Statistiques
    total_responses: int = 0
    completed_responses: int = 0
    average_completion_time_seconds: int = 0

    # Métadonnées
    tags: List[str] = field(default_factory=list)
    category: str = ""
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Answer:
    """Réponse à une question"""
    question_id: str
    question_text: str
    question_type: QuestionType
    value: Any  # Texte, liste, nombre selon type
    score: Optional[int] = None
    answered_at: datetime = field(default_factory=datetime.now)


@dataclass
class SurveyResponse:
    """Réponse complète à enquête"""
    id: str
    tenant_id: str
    survey_id: str
    survey_title: str
    respondent_id: Optional[str] = None
    respondent_email: Optional[str] = None
    respondent_name: str = ""
    status: ResponseStatus = ResponseStatus.IN_PROGRESS

    # Réponses
    answers: List[Answer] = field(default_factory=list)

    # Scores
    total_score: Optional[int] = None
    nps_score: Optional[int] = None
    satisfaction_score: Optional[Decimal] = None

    # Métadonnées
    ip_address: str = ""
    user_agent: str = ""
    language: str = "fr"
    source: str = ""  # email, web, app
    referrer: str = ""

    # Temps
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_seconds: int = 0

    # Contexte
    context_type: str = ""  # order, ticket, visit
    context_id: str = ""
    custom_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Distribution:
    """Distribution d'enquête"""
    id: str
    tenant_id: str
    survey_id: str
    survey_title: str
    channel: DistributionChannel
    name: str
    description: str = ""

    # Configuration
    recipients: List[str] = field(default_factory=list)  # emails ou IDs
    message_subject: str = ""
    message_body: str = ""
    sender_name: str = ""
    sender_email: str = ""

    # Lien
    survey_url: str = ""
    short_url: str = ""
    qr_code_url: str = ""

    # Planification
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    # Statistiques
    total_sent: int = 0
    total_opened: int = 0
    total_started: int = 0
    total_completed: int = 0

    # Statut
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class SurveyTemplate:
    """Modèle d'enquête"""
    id: str
    tenant_id: str
    name: str
    description: str
    survey_type: SurveyType
    category: str = ""
    questions: List[Dict] = field(default_factory=list)
    is_system: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class QuestionStats:
    """Statistiques d'une question"""
    question_id: str
    question_text: str
    question_type: QuestionType
    total_responses: int = 0
    response_rate: Decimal = Decimal("0")
    average_score: Optional[Decimal] = None
    distribution: Dict[str, int] = field(default_factory=dict)
    text_responses: List[str] = field(default_factory=list)


@dataclass
class SurveyAnalytics:
    """Analytics d'enquête"""
    survey_id: str
    survey_title: str
    survey_type: SurveyType
    period_start: date
    period_end: date

    # Métriques globales
    total_responses: int = 0
    completed_responses: int = 0
    completion_rate: Decimal = Decimal("0")
    average_duration_seconds: int = 0

    # Scores
    nps_score: Optional[int] = None
    nps_promoters: int = 0
    nps_passives: int = 0
    nps_detractors: int = 0
    satisfaction_score: Optional[Decimal] = None

    # Par question
    question_stats: List[QuestionStats] = field(default_factory=list)

    # Tendances
    responses_by_day: Dict[str, int] = field(default_factory=dict)
    responses_by_source: Dict[str, int] = field(default_factory=dict)

    # Segments
    by_segment: Dict[str, Dict] = field(default_factory=dict)


# ============== Service ==============

class SurveyService:
    """
    Service de gestion des enquêtes et feedback.

    Fonctionnalités:
    - Création d'enquêtes multi-types
    - Questions variées avec logique
    - Distribution multicanal
    - Collecte et analyse
    - NPS et satisfaction
    """

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self._surveys: Dict[str, Survey] = {}
        self._responses: Dict[str, SurveyResponse] = {}
        self._distributions: Dict[str, Distribution] = {}
        self._templates: Dict[str, SurveyTemplate] = {}

    # ========== Enquêtes ==========

    def create_survey(
        self,
        title: str,
        survey_type: SurveyType,
        description: str = "",
        welcome_message: str = "",
        thank_you_message: str = "",
        allow_anonymous: bool = False,
        allow_multiple_responses: bool = False,
        category: str = "",
        created_by: str = ""
    ) -> Survey:
        """Créer une enquête"""
        survey = Survey(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            title=title,
            description=description,
            survey_type=survey_type,
            welcome_message=welcome_message,
            thank_you_message=thank_you_message or "Merci pour votre participation!",
            allow_anonymous=allow_anonymous,
            allow_multiple_responses=allow_multiple_responses,
            category=category,
            created_by=created_by
        )
        self._surveys[survey.id] = survey
        return survey

    def update_survey(
        self,
        survey_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        welcome_message: Optional[str] = None,
        thank_you_message: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        max_responses: Optional[int] = None
    ) -> Optional[Survey]:
        """Mettre à jour enquête"""
        survey = self._surveys.get(survey_id)
        if not survey:
            return None

        if title is not None:
            survey.title = title
        if description is not None:
            survey.description = description
        if welcome_message is not None:
            survey.welcome_message = welcome_message
        if thank_you_message is not None:
            survey.thank_you_message = thank_you_message
        if start_date is not None:
            survey.start_date = start_date
        if end_date is not None:
            survey.end_date = end_date
        if max_responses is not None:
            survey.max_responses = max_responses

        survey.updated_at = datetime.now()
        return survey

    def add_question(
        self,
        survey_id: str,
        question_type: QuestionType,
        text: str,
        description: str = "",
        required: bool = False,
        options: List[Dict] = None,
        min_value: int = 1,
        max_value: int = 5,
        min_label: str = "",
        max_label: str = ""
    ) -> Optional[Question]:
        """Ajouter une question"""
        survey = self._surveys.get(survey_id)
        if not survey or survey.status not in [SurveyStatus.DRAFT, SurveyStatus.PAUSED]:
            return None

        question_options = []
        if options:
            for i, opt in enumerate(options):
                question_options.append(QuestionOption(
                    id=str(uuid4()),
                    text=opt.get("text", ""),
                    value=opt.get("value"),
                    score=opt.get("score", 0),
                    order=i,
                    is_other=opt.get("is_other", False)
                ))

        question = Question(
            id=str(uuid4()),
            survey_id=survey_id,
            question_type=question_type,
            text=text,
            description=description,
            required=required,
            order=len(survey.questions),
            options=question_options,
            min_value=min_value,
            max_value=max_value,
            min_label=min_label,
            max_label=max_label
        )

        survey.questions.append(question)
        survey.updated_at = datetime.now()
        return question

    def add_nps_question(
        self,
        survey_id: str,
        text: str = "Sur une échelle de 0 à 10, quelle est la probabilité que vous recommandiez notre service?",
        required: bool = True
    ) -> Optional[Question]:
        """Ajouter question NPS standard"""
        return self.add_question(
            survey_id=survey_id,
            question_type=QuestionType.NPS,
            text=text,
            required=required,
            min_value=0,
            max_value=10,
            min_label="Pas du tout probable",
            max_label="Très probable"
        )

    def add_satisfaction_question(
        self,
        survey_id: str,
        text: str = "Globalement, êtes-vous satisfait de notre service?",
        required: bool = True
    ) -> Optional[Question]:
        """Ajouter question satisfaction"""
        return self.add_question(
            survey_id=survey_id,
            question_type=QuestionType.RATING,
            text=text,
            required=required,
            min_value=1,
            max_value=5,
            min_label="Très insatisfait",
            max_label="Très satisfait"
        )

    def add_question_logic(
        self,
        survey_id: str,
        question_id: str,
        condition_type: str,
        source_question_id: str,
        operator: str,
        value: Any,
        target_question_id: Optional[str] = None
    ) -> Optional[Question]:
        """Ajouter logique conditionnelle"""
        survey = self._surveys.get(survey_id)
        if not survey:
            return None

        for question in survey.questions:
            if question.id == question_id:
                logic = QuestionLogic(
                    condition_type=condition_type,
                    source_question_id=source_question_id,
                    operator=operator,
                    value=value,
                    target_question_id=target_question_id
                )
                question.logic_rules.append(logic)
                survey.updated_at = datetime.now()
                return question

        return None

    def reorder_questions(
        self,
        survey_id: str,
        question_ids: List[str]
    ) -> Optional[Survey]:
        """Réordonner les questions"""
        survey = self._surveys.get(survey_id)
        if not survey:
            return None

        question_map = {q.id: q for q in survey.questions}
        reordered = []
        for i, qid in enumerate(question_ids):
            if qid in question_map:
                question_map[qid].order = i
                reordered.append(question_map[qid])

        survey.questions = reordered
        survey.updated_at = datetime.now()
        return survey

    def delete_question(
        self,
        survey_id: str,
        question_id: str
    ) -> Optional[Survey]:
        """Supprimer une question"""
        survey = self._surveys.get(survey_id)
        if not survey or survey.status not in [SurveyStatus.DRAFT]:
            return None

        survey.questions = [q for q in survey.questions if q.id != question_id]

        # Renuméroter
        for i, q in enumerate(survey.questions):
            q.order = i

        survey.updated_at = datetime.now()
        return survey

    def activate_survey(self, survey_id: str) -> Optional[Survey]:
        """Activer enquête"""
        survey = self._surveys.get(survey_id)
        if not survey or not survey.questions:
            return None

        survey.status = SurveyStatus.ACTIVE
        survey.updated_at = datetime.now()
        return survey

    def pause_survey(self, survey_id: str) -> Optional[Survey]:
        """Mettre en pause"""
        survey = self._surveys.get(survey_id)
        if not survey or survey.status != SurveyStatus.ACTIVE:
            return None

        survey.status = SurveyStatus.PAUSED
        survey.updated_at = datetime.now()
        return survey

    def close_survey(self, survey_id: str) -> Optional[Survey]:
        """Fermer enquête"""
        survey = self._surveys.get(survey_id)
        if not survey:
            return None

        survey.status = SurveyStatus.CLOSED
        survey.updated_at = datetime.now()
        return survey

    def get_survey(self, survey_id: str) -> Optional[Survey]:
        """Obtenir enquête"""
        return self._surveys.get(survey_id)

    def list_surveys(
        self,
        status: Optional[SurveyStatus] = None,
        survey_type: Optional[SurveyType] = None,
        category: Optional[str] = None
    ) -> List[Survey]:
        """Lister les enquêtes"""
        surveys = list(self._surveys.values())

        if status:
            surveys = [s for s in surveys if s.status == status]
        if survey_type:
            surveys = [s for s in surveys if s.survey_type == survey_type]
        if category:
            surveys = [s for s in surveys if s.category == category]

        return sorted(surveys, key=lambda x: x.created_at, reverse=True)

    # ========== Réponses ==========

    def start_response(
        self,
        survey_id: str,
        respondent_id: Optional[str] = None,
        respondent_email: Optional[str] = None,
        respondent_name: str = "",
        source: str = "web",
        ip_address: str = "",
        user_agent: str = "",
        context_type: str = "",
        context_id: str = ""
    ) -> Optional[SurveyResponse]:
        """Démarrer une réponse"""
        survey = self._surveys.get(survey_id)
        if not survey or survey.status != SurveyStatus.ACTIVE:
            return None

        # Vérifier limites
        if survey.max_responses and survey.total_responses >= survey.max_responses:
            return None

        # Vérifier doublons
        if not survey.allow_multiple_responses and respondent_email:
            existing = [
                r for r in self._responses.values()
                if r.survey_id == survey_id
                and r.respondent_email == respondent_email
                and r.status == ResponseStatus.COMPLETED
            ]
            if existing:
                return None

        response = SurveyResponse(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            survey_id=survey_id,
            survey_title=survey.title,
            respondent_id=respondent_id,
            respondent_email=respondent_email,
            respondent_name=respondent_name,
            source=source,
            ip_address=ip_address,
            user_agent=user_agent,
            context_type=context_type,
            context_id=context_id
        )
        self._responses[response.id] = response
        survey.total_responses += 1

        return response

    def submit_answer(
        self,
        response_id: str,
        question_id: str,
        value: Any
    ) -> Optional[SurveyResponse]:
        """Soumettre une réponse"""
        response = self._responses.get(response_id)
        if not response or response.status == ResponseStatus.COMPLETED:
            return None

        survey = self._surveys.get(response.survey_id)
        if not survey:
            return None

        # Trouver la question
        question = None
        for q in survey.questions:
            if q.id == question_id:
                question = q
                break

        if not question:
            return None

        # Calculer score si applicable
        score = None
        if question.question_type in [QuestionType.NPS, QuestionType.RATING, QuestionType.SCALE]:
            score = int(value) if value is not None else None
        elif question.question_type == QuestionType.SINGLE_CHOICE:
            for opt in question.options:
                if opt.value == value or opt.text == value:
                    score = opt.score
                    break

        # Ajouter ou mettre à jour réponse
        existing_idx = None
        for i, ans in enumerate(response.answers):
            if ans.question_id == question_id:
                existing_idx = i
                break

        answer = Answer(
            question_id=question_id,
            question_text=question.text,
            question_type=question.question_type,
            value=value,
            score=score
        )

        if existing_idx is not None:
            response.answers[existing_idx] = answer
        else:
            response.answers.append(answer)

        return response

    def complete_response(
        self,
        response_id: str
    ) -> Optional[SurveyResponse]:
        """Compléter une réponse"""
        response = self._responses.get(response_id)
        if not response or response.status == ResponseStatus.COMPLETED:
            return None

        survey = self._surveys.get(response.survey_id)
        if not survey:
            return None

        # Vérifier questions obligatoires
        required_ids = {q.id for q in survey.questions if q.required}
        answered_ids = {a.question_id for a in response.answers}

        if not required_ids.issubset(answered_ids):
            return None

        response.status = ResponseStatus.COMPLETED
        response.completed_at = datetime.now()
        response.duration_seconds = int(
            (response.completed_at - response.started_at).total_seconds()
        )

        # Calculer scores
        scores = [a.score for a in response.answers if a.score is not None]
        if scores:
            response.total_score = sum(scores)

        # Score NPS
        for answer in response.answers:
            if answer.question_type == QuestionType.NPS:
                response.nps_score = answer.score
                break

        # Score satisfaction
        satisfaction_answers = [
            a for a in response.answers
            if a.question_type == QuestionType.RATING
        ]
        if satisfaction_answers:
            response.satisfaction_score = Decimal(
                sum(a.score or 0 for a in satisfaction_answers)
            ) / len(satisfaction_answers)

        # Mettre à jour enquête
        survey.completed_responses += 1
        total_duration = sum(
            r.duration_seconds for r in self._responses.values()
            if r.survey_id == survey.id and r.status == ResponseStatus.COMPLETED
        )
        survey.average_completion_time_seconds = total_duration // survey.completed_responses

        return response

    def abandon_response(self, response_id: str) -> Optional[SurveyResponse]:
        """Abandonner une réponse"""
        response = self._responses.get(response_id)
        if not response or response.status != ResponseStatus.IN_PROGRESS:
            return None

        response.status = ResponseStatus.ABANDONED
        return response

    def get_response(self, response_id: str) -> Optional[SurveyResponse]:
        """Obtenir une réponse"""
        return self._responses.get(response_id)

    def list_responses(
        self,
        survey_id: str,
        status: Optional[ResponseStatus] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None
    ) -> List[SurveyResponse]:
        """Lister les réponses"""
        responses = [
            r for r in self._responses.values()
            if r.survey_id == survey_id
        ]

        if status:
            responses = [r for r in responses if r.status == status]
        if date_from:
            responses = [r for r in responses if r.started_at.date() >= date_from]
        if date_to:
            responses = [r for r in responses if r.started_at.date() <= date_to]

        return sorted(responses, key=lambda x: x.started_at, reverse=True)

    # ========== Distribution ==========

    def create_distribution(
        self,
        survey_id: str,
        channel: DistributionChannel,
        name: str,
        recipients: List[str] = None,
        message_subject: str = "",
        message_body: str = "",
        sender_name: str = "",
        sender_email: str = "",
        scheduled_at: Optional[datetime] = None
    ) -> Optional[Distribution]:
        """Créer une distribution"""
        survey = self._surveys.get(survey_id)
        if not survey:
            return None

        # Générer URL
        survey_url = f"https://survey.example.com/s/{survey_id}"
        short_url = f"https://srv.ex/{str(uuid4())[:8]}"

        distribution = Distribution(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            survey_id=survey_id,
            survey_title=survey.title,
            channel=channel,
            name=name,
            recipients=recipients or [],
            message_subject=message_subject or f"Votre avis compte: {survey.title}",
            message_body=message_body,
            sender_name=sender_name,
            sender_email=sender_email,
            survey_url=survey_url,
            short_url=short_url,
            scheduled_at=scheduled_at
        )
        self._distributions[distribution.id] = distribution
        return distribution

    def send_distribution(
        self,
        distribution_id: str
    ) -> Optional[Distribution]:
        """Envoyer distribution (simulation)"""
        dist = self._distributions.get(distribution_id)
        if not dist or not dist.is_active:
            return None

        # Simulation envoi
        dist.sent_at = datetime.now()
        dist.total_sent = len(dist.recipients)

        return dist

    def track_email_open(
        self,
        distribution_id: str
    ) -> Optional[Distribution]:
        """Tracker ouverture email"""
        dist = self._distributions.get(distribution_id)
        if not dist:
            return None

        dist.total_opened += 1
        return dist

    def get_distribution(self, distribution_id: str) -> Optional[Distribution]:
        """Obtenir distribution"""
        return self._distributions.get(distribution_id)

    def list_distributions(
        self,
        survey_id: str
    ) -> List[Distribution]:
        """Lister distributions"""
        return [
            d for d in self._distributions.values()
            if d.survey_id == survey_id
        ]

    # ========== Templates ==========

    def create_template(
        self,
        name: str,
        description: str,
        survey_type: SurveyType,
        questions: List[Dict],
        category: str = ""
    ) -> SurveyTemplate:
        """Créer un modèle"""
        template = SurveyTemplate(
            id=str(uuid4()),
            tenant_id=self.tenant_id,
            name=name,
            description=description,
            survey_type=survey_type,
            category=category,
            questions=questions
        )
        self._templates[template.id] = template
        return template

    def create_survey_from_template(
        self,
        template_id: str,
        title: str,
        created_by: str = ""
    ) -> Optional[Survey]:
        """Créer enquête depuis modèle"""
        template = self._templates.get(template_id)
        if not template:
            return None

        survey = self.create_survey(
            title=title,
            survey_type=template.survey_type,
            description=template.description,
            category=template.category,
            created_by=created_by
        )

        # Ajouter questions du template
        for q_data in template.questions:
            self.add_question(
                survey_id=survey.id,
                question_type=QuestionType(q_data.get("type", "text_short")),
                text=q_data.get("text", ""),
                description=q_data.get("description", ""),
                required=q_data.get("required", False),
                options=q_data.get("options", []),
                min_value=q_data.get("min_value", 1),
                max_value=q_data.get("max_value", 5)
            )

        return survey

    def get_templates(
        self,
        survey_type: Optional[SurveyType] = None,
        category: Optional[str] = None
    ) -> List[SurveyTemplate]:
        """Lister templates"""
        templates = [t for t in self._templates.values() if t.is_active]

        if survey_type:
            templates = [t for t in templates if t.survey_type == survey_type]
        if category:
            templates = [t for t in templates if t.category == category]

        return sorted(templates, key=lambda x: x.name)

    # ========== Analytics ==========

    def calculate_nps(self, survey_id: str) -> Dict[str, Any]:
        """Calculer score NPS"""
        responses = [
            r for r in self._responses.values()
            if r.survey_id == survey_id
            and r.status == ResponseStatus.COMPLETED
            and r.nps_score is not None
        ]

        if not responses:
            return {"nps": None, "promoters": 0, "passives": 0, "detractors": 0}

        promoters = len([r for r in responses if r.nps_score >= 9])
        passives = len([r for r in responses if 7 <= r.nps_score <= 8])
        detractors = len([r for r in responses if r.nps_score <= 6])

        total = len(responses)
        nps = int((promoters - detractors) / total * 100)

        return {
            "nps": nps,
            "promoters": promoters,
            "passives": passives,
            "detractors": detractors,
            "promoter_pct": round(promoters / total * 100, 1),
            "passive_pct": round(passives / total * 100, 1),
            "detractor_pct": round(detractors / total * 100, 1)
        }

    def get_survey_analytics(
        self,
        survey_id: str,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None
    ) -> Optional[SurveyAnalytics]:
        """Obtenir analytics enquête"""
        survey = self._surveys.get(survey_id)
        if not survey:
            return None

        responses = [
            r for r in self._responses.values()
            if r.survey_id == survey_id
        ]

        if period_start:
            responses = [r for r in responses if r.started_at.date() >= period_start]
        if period_end:
            responses = [r for r in responses if r.started_at.date() <= period_end]

        completed = [r for r in responses if r.status == ResponseStatus.COMPLETED]

        analytics = SurveyAnalytics(
            survey_id=survey_id,
            survey_title=survey.title,
            survey_type=survey.survey_type,
            period_start=period_start or date.today(),
            period_end=period_end or date.today(),
            total_responses=len(responses),
            completed_responses=len(completed)
        )

        if responses:
            analytics.completion_rate = Decimal(len(completed)) / len(responses) * 100

        if completed:
            analytics.average_duration_seconds = sum(
                r.duration_seconds for r in completed
            ) // len(completed)

            # NPS
            nps_data = self.calculate_nps(survey_id)
            analytics.nps_score = nps_data.get("nps")
            analytics.nps_promoters = nps_data.get("promoters", 0)
            analytics.nps_passives = nps_data.get("passives", 0)
            analytics.nps_detractors = nps_data.get("detractors", 0)

            # Satisfaction
            sat_scores = [r.satisfaction_score for r in completed if r.satisfaction_score]
            if sat_scores:
                analytics.satisfaction_score = sum(sat_scores) / len(sat_scores)

        # Stats par question
        for question in survey.questions:
            q_answers = []
            for resp in completed:
                for ans in resp.answers:
                    if ans.question_id == question.id:
                        q_answers.append(ans)
                        break

            q_stats = QuestionStats(
                question_id=question.id,
                question_text=question.text,
                question_type=question.question_type,
                total_responses=len(q_answers)
            )

            if responses:
                q_stats.response_rate = Decimal(len(q_answers)) / len(responses) * 100

            # Distribution pour choix
            if question.question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
                for opt in question.options:
                    count = sum(
                        1 for a in q_answers
                        if (isinstance(a.value, list) and opt.text in a.value)
                        or a.value == opt.text
                    )
                    q_stats.distribution[opt.text] = count

            # Moyenne pour rating/scale
            if question.question_type in [QuestionType.RATING, QuestionType.NPS, QuestionType.SCALE]:
                scores = [a.score for a in q_answers if a.score is not None]
                if scores:
                    q_stats.average_score = Decimal(sum(scores)) / len(scores)

            # Réponses texte
            if question.question_type in [QuestionType.TEXT_SHORT, QuestionType.TEXT_LONG]:
                q_stats.text_responses = [
                    str(a.value) for a in q_answers if a.value
                ][:50]  # Limiter à 50

            analytics.question_stats.append(q_stats)

        # Réponses par jour
        for resp in responses:
            day_key = resp.started_at.strftime("%Y-%m-%d")
            analytics.responses_by_day[day_key] = analytics.responses_by_day.get(day_key, 0) + 1

        # Par source
        for resp in responses:
            analytics.responses_by_source[resp.source] = \
                analytics.responses_by_source.get(resp.source, 0) + 1

        return analytics

    def export_responses(
        self,
        survey_id: str,
        format: str = "csv"
    ) -> List[Dict]:
        """Exporter réponses"""
        survey = self._surveys.get(survey_id)
        if not survey:
            return []

        responses = [
            r for r in self._responses.values()
            if r.survey_id == survey_id and r.status == ResponseStatus.COMPLETED
        ]

        export_data = []
        for resp in responses:
            row = {
                "response_id": resp.id,
                "respondent_email": resp.respondent_email or "",
                "respondent_name": resp.respondent_name,
                "started_at": resp.started_at.isoformat(),
                "completed_at": resp.completed_at.isoformat() if resp.completed_at else "",
                "duration_seconds": resp.duration_seconds,
                "nps_score": resp.nps_score,
                "satisfaction_score": float(resp.satisfaction_score) if resp.satisfaction_score else None
            }

            # Ajouter réponses
            for question in survey.questions:
                for ans in resp.answers:
                    if ans.question_id == question.id:
                        row[f"q_{question.id}"] = ans.value
                        break
                else:
                    row[f"q_{question.id}"] = None

            export_data.append(row)

        return export_data


def create_survey_service(tenant_id: str) -> SurveyService:
    """Factory function pour créer le service survey"""
    return SurveyService(tenant_id)
