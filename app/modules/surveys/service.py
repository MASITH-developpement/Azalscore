"""
Service Surveys / Sondages - GAP-065

Gestion des enquêtes et sondages:
- Création de questionnaires
- Types de questions variés
- Logique conditionnelle
- Distribution multi-canal
- Collecte de réponses
- Analyses et rapports
- NPS et satisfaction
- Anonymat configurable
"""
from __future__ import annotations


from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Set
from uuid import uuid4
import statistics


# ============================================================================
# ÉNUMÉRATIONS
# ============================================================================

class SurveyType(str, Enum):
    """Type de sondage."""
    SATISFACTION = "satisfaction"
    NPS = "nps"
    FEEDBACK = "feedback"
    POLL = "poll"
    QUIZ = "quiz"
    ASSESSMENT = "assessment"
    RESEARCH = "research"
    EMPLOYEE = "employee"


class SurveyStatus(str, Enum):
    """Statut d'un sondage."""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    CLOSED = "closed"
    ARCHIVED = "archived"


class QuestionType(str, Enum):
    """Type de question."""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT_SHORT = "text_short"
    TEXT_LONG = "text_long"
    RATING = "rating"
    SCALE = "scale"
    NPS = "nps"
    DATE = "date"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    FILE_UPLOAD = "file_upload"
    MATRIX = "matrix"
    RANKING = "ranking"
    YES_NO = "yes_no"


class ResponseStatus(str, Enum):
    """Statut d'une réponse."""
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class DistributionChannel(str, Enum):
    """Canal de distribution."""
    EMAIL = "email"
    SMS = "sms"
    LINK = "link"
    EMBEDDED = "embedded"
    QR_CODE = "qr_code"
    POPUP = "popup"


class TriggerType(str, Enum):
    """Type de déclencheur."""
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    EVENT_BASED = "event_based"
    POST_PURCHASE = "post_purchase"
    POST_SUPPORT = "post_support"
    RECURRING = "recurring"


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class QuestionOption:
    """Option de réponse."""
    id: str
    text: str
    value: Optional[str] = None
    order: int = 0
    is_other: bool = False
    image_url: Optional[str] = None


@dataclass
class QuestionLogic:
    """Logique conditionnelle."""
    id: str
    condition_question_id: str
    condition_operator: str  # equals, not_equals, contains, greater_than, etc.
    condition_value: Any
    action: str  # show, hide, skip_to, end
    target_question_id: Optional[str] = None


@dataclass
class Question:
    """Une question."""
    id: str
    survey_id: str
    question_type: QuestionType
    text: str
    description: Optional[str] = None
    order: int = 0
    is_required: bool = True
    options: List[QuestionOption] = field(default_factory=list)
    min_value: Optional[int] = None
    max_value: Optional[int] = None
    min_label: Optional[str] = None
    max_label: Optional[str] = None
    placeholder: Optional[str] = None
    validation_regex: Optional[str] = None
    validation_message: Optional[str] = None
    max_length: Optional[int] = None
    allow_multiple: bool = False
    randomize_options: bool = False
    image_url: Optional[str] = None
    logic_rules: List[QuestionLogic] = field(default_factory=list)
    matrix_rows: List[str] = field(default_factory=list)
    matrix_columns: List[str] = field(default_factory=list)
    settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SurveyPage:
    """Page d'un sondage."""
    id: str
    survey_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    order: int = 0
    question_ids: List[str] = field(default_factory=list)


@dataclass
class Survey:
    """Un sondage."""
    id: str
    tenant_id: str
    title: str
    description: Optional[str] = None
    survey_type: SurveyType = SurveyType.FEEDBACK
    status: SurveyStatus = SurveyStatus.DRAFT
    is_anonymous: bool = False
    allow_multiple_responses: bool = False
    show_progress_bar: bool = True
    randomize_questions: bool = False
    one_question_per_page: bool = False
    welcome_message: Optional[str] = None
    thank_you_message: Optional[str] = None
    redirect_url: Optional[str] = None
    logo_url: Optional[str] = None
    theme_color: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    max_responses: Optional[int] = None
    estimated_time_minutes: Optional[int] = None
    pages: List[SurveyPage] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    target_audience: Optional[str] = None
    response_count: int = 0
    completion_rate: Decimal = Decimal("0")
    avg_completion_time_seconds: int = 0
    created_by: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None


@dataclass
class SurveyDistribution:
    """Distribution d'un sondage."""
    id: str
    survey_id: str
    channel: DistributionChannel
    name: Optional[str] = None
    trigger_type: TriggerType = TriggerType.MANUAL
    trigger_config: Dict[str, Any] = field(default_factory=dict)
    recipients: List[str] = field(default_factory=list)
    recipient_count: int = 0
    sent_count: int = 0
    opened_count: int = 0
    started_count: int = 0
    completed_count: int = 0
    unique_link: Optional[str] = None
    embed_code: Optional[str] = None
    qr_code_url: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    reminder_enabled: bool = False
    reminder_days: int = 3
    reminder_sent: bool = False
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Response:
    """Une réponse au sondage."""
    id: str
    survey_id: str
    distribution_id: Optional[str] = None
    respondent_id: Optional[str] = None
    respondent_email: Optional[str] = None
    status: ResponseStatus = ResponseStatus.IN_PROGRESS
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    completion_time_seconds: int = 0
    answers: Dict[str, Any] = field(default_factory=dict)
    current_page: int = 0
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Answer:
    """Une réponse à une question."""
    id: str
    response_id: str
    question_id: str
    question_type: QuestionType
    value: Any = None
    text_value: Optional[str] = None
    numeric_value: Optional[Decimal] = None
    selected_options: List[str] = field(default_factory=list)
    file_ids: List[str] = field(default_factory=list)
    answered_at: datetime = field(default_factory=datetime.now)


@dataclass
class QuestionAnalytics:
    """Analyse d'une question."""
    question_id: str
    question_text: str
    question_type: QuestionType
    total_responses: int = 0
    skipped_count: int = 0
    response_rate: Decimal = Decimal("0")
    option_counts: Dict[str, int] = field(default_factory=dict)
    option_percentages: Dict[str, Decimal] = field(default_factory=dict)
    numeric_stats: Optional[Dict[str, Decimal]] = None  # min, max, avg, median, std_dev
    text_responses: List[str] = field(default_factory=list)
    word_frequency: Dict[str, int] = field(default_factory=dict)
    nps_score: Optional[Decimal] = None
    nps_breakdown: Optional[Dict[str, int]] = None  # promoters, passives, detractors


@dataclass
class SurveyAnalytics:
    """Analyse globale d'un sondage."""
    survey_id: str
    survey_title: str
    total_responses: int = 0
    completed_responses: int = 0
    abandoned_responses: int = 0
    completion_rate: Decimal = Decimal("0")
    avg_completion_time_seconds: int = 0
    response_by_day: Dict[str, int] = field(default_factory=dict)
    response_by_channel: Dict[str, int] = field(default_factory=dict)
    response_by_device: Dict[str, int] = field(default_factory=dict)
    question_analytics: List[QuestionAnalytics] = field(default_factory=list)
    nps_overall: Optional[Decimal] = None
    satisfaction_score: Optional[Decimal] = None
    generated_at: datetime = field(default_factory=datetime.now)


@dataclass
class SurveyTemplate:
    """Template de sondage."""
    id: str
    name: str
    tenant_id: Optional[str] = None  # None = template système
    description: Optional[str] = None
    survey_type: SurveyType = SurveyType.FEEDBACK
    category: Optional[str] = None
    questions: List[Dict[str, Any]] = field(default_factory=list)
    is_public: bool = False
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# SERVICE PRINCIPAL
# ============================================================================

class SurveyService:
    """Service de gestion des sondages."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

        # Stockage en mémoire (simulation)
        self._surveys: Dict[str, Survey] = {}
        self._questions: Dict[str, Question] = {}
        self._distributions: Dict[str, SurveyDistribution] = {}
        self._responses: Dict[str, Response] = {}
        self._answers: Dict[str, Answer] = {}
        self._templates: Dict[str, SurveyTemplate] = {}

    # -------------------------------------------------------------------------
    # Sondages
    # -------------------------------------------------------------------------

    def create_survey(
        self,
        title: str,
        survey_type: SurveyType = SurveyType.FEEDBACK,
        description: Optional[str] = None,
        **kwargs
    ) -> Survey:
        """Crée un sondage."""
        survey_id = str(uuid4())

        survey = Survey(
            id=survey_id,
            tenant_id=self.tenant_id,
            title=title,
            survey_type=survey_type,
            description=description,
            **kwargs
        )

        # Créer une page par défaut
        page = SurveyPage(
            id=str(uuid4()),
            survey_id=survey_id,
            order=0
        )
        survey.pages.append(page)

        self._surveys[survey_id] = survey
        return survey

    def get_survey(self, survey_id: str) -> Optional[Survey]:
        """Récupère un sondage."""
        survey = self._surveys.get(survey_id)
        if survey and survey.tenant_id == self.tenant_id:
            return survey
        return None

    def update_survey(self, survey_id: str, **updates) -> Optional[Survey]:
        """Met à jour un sondage."""
        survey = self.get_survey(survey_id)
        if not survey:
            return None

        for key, value in updates.items():
            if hasattr(survey, key):
                setattr(survey, key, value)

        survey.updated_at = datetime.now()
        return survey

    def publish_survey(self, survey_id: str) -> Optional[Survey]:
        """Publie un sondage."""
        survey = self.get_survey(survey_id)
        if not survey:
            return None

        if survey.status != SurveyStatus.DRAFT:
            return None

        # Vérifier qu'il y a des questions
        questions = self.list_questions(survey_id)
        if not questions:
            return None

        survey.status = SurveyStatus.ACTIVE
        survey.published_at = datetime.now()

        # Si dates définies, ajuster le statut
        now = datetime.now()
        if survey.start_date and survey.start_date > now:
            survey.status = SurveyStatus.SCHEDULED

        survey.updated_at = datetime.now()
        return survey

    def close_survey(self, survey_id: str) -> Optional[Survey]:
        """Ferme un sondage."""
        survey = self.get_survey(survey_id)
        if not survey:
            return None

        survey.status = SurveyStatus.CLOSED
        survey.updated_at = datetime.now()
        return survey

    def list_surveys(
        self,
        *,
        status: Optional[SurveyStatus] = None,
        survey_type: Optional[SurveyType] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Survey], int]:
        """Liste les sondages."""
        results = []

        for survey in self._surveys.values():
            if survey.tenant_id != self.tenant_id:
                continue
            if status and survey.status != status:
                continue
            if survey_type and survey.survey_type != survey_type:
                continue
            if search and search.lower() not in survey.title.lower():
                continue
            results.append(survey)

        results.sort(key=lambda x: x.created_at, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    def duplicate_survey(self, survey_id: str, new_title: str) -> Optional[Survey]:
        """Duplique un sondage."""
        original = self.get_survey(survey_id)
        if not original:
            return None

        # Créer la copie
        new_survey = self.create_survey(
            title=new_title,
            survey_type=original.survey_type,
            description=original.description,
            is_anonymous=original.is_anonymous,
            welcome_message=original.welcome_message,
            thank_you_message=original.thank_you_message,
            show_progress_bar=original.show_progress_bar
        )

        # Copier les questions
        questions = self.list_questions(survey_id)
        for q in questions:
            self.add_question(
                new_survey.id,
                question_type=q.question_type,
                text=q.text,
                description=q.description,
                is_required=q.is_required,
                options=[
                    {"text": opt.text, "value": opt.value}
                    for opt in q.options
                ],
                min_value=q.min_value,
                max_value=q.max_value,
                min_label=q.min_label,
                max_label=q.max_label
            )

        return new_survey

    # -------------------------------------------------------------------------
    # Questions
    # -------------------------------------------------------------------------

    def add_question(
        self,
        survey_id: str,
        question_type: QuestionType,
        text: str,
        *,
        description: Optional[str] = None,
        is_required: bool = True,
        options: Optional[List[Dict[str, Any]]] = None,
        page_id: Optional[str] = None,
        **kwargs
    ) -> Optional[Question]:
        """Ajoute une question."""
        survey = self.get_survey(survey_id)
        if not survey:
            return None

        # Déterminer l'ordre
        existing = [q for q in self._questions.values() if q.survey_id == survey_id]
        order = len(existing)

        question_id = str(uuid4())

        # Créer les options
        question_options = []
        if options:
            for i, opt in enumerate(options):
                question_options.append(QuestionOption(
                    id=str(uuid4()),
                    text=opt.get("text", ""),
                    value=opt.get("value"),
                    order=i,
                    is_other=opt.get("is_other", False)
                ))

        question = Question(
            id=question_id,
            survey_id=survey_id,
            question_type=question_type,
            text=text,
            description=description,
            order=order,
            is_required=is_required,
            options=question_options,
            **kwargs
        )

        self._questions[question_id] = question

        # Ajouter à la page
        target_page = survey.pages[0]
        if page_id:
            for p in survey.pages:
                if p.id == page_id:
                    target_page = p
                    break
        target_page.question_ids.append(question_id)

        return question

    def update_question(
        self,
        question_id: str,
        **updates
    ) -> Optional[Question]:
        """Met à jour une question."""
        question = self._questions.get(question_id)
        if not question:
            return None

        survey = self.get_survey(question.survey_id)
        if not survey:
            return None

        for key, value in updates.items():
            if hasattr(question, key):
                setattr(question, key, value)

        return question

    def delete_question(self, question_id: str) -> bool:
        """Supprime une question."""
        question = self._questions.get(question_id)
        if not question:
            return False

        survey = self.get_survey(question.survey_id)
        if not survey:
            return False

        # Retirer de la page
        for page in survey.pages:
            if question_id in page.question_ids:
                page.question_ids.remove(question_id)

        del self._questions[question_id]
        return True

    def reorder_questions(
        self,
        survey_id: str,
        question_order: List[str]
    ) -> bool:
        """Réordonne les questions."""
        survey = self.get_survey(survey_id)
        if not survey:
            return False

        for i, qid in enumerate(question_order):
            if qid in self._questions:
                self._questions[qid].order = i

        return True

    def list_questions(self, survey_id: str) -> List[Question]:
        """Liste les questions d'un sondage."""
        questions = [
            q for q in self._questions.values()
            if q.survey_id == survey_id
        ]
        questions.sort(key=lambda x: x.order)
        return questions

    def add_logic_rule(
        self,
        question_id: str,
        condition_question_id: str,
        condition_operator: str,
        condition_value: Any,
        action: str,
        target_question_id: Optional[str] = None
    ) -> Optional[QuestionLogic]:
        """Ajoute une règle de logique conditionnelle."""
        question = self._questions.get(question_id)
        if not question:
            return None

        logic = QuestionLogic(
            id=str(uuid4()),
            condition_question_id=condition_question_id,
            condition_operator=condition_operator,
            condition_value=condition_value,
            action=action,
            target_question_id=target_question_id
        )

        question.logic_rules.append(logic)
        return logic

    # -------------------------------------------------------------------------
    # Distribution
    # -------------------------------------------------------------------------

    def create_distribution(
        self,
        survey_id: str,
        channel: DistributionChannel,
        *,
        name: Optional[str] = None,
        recipients: Optional[List[str]] = None,
        trigger_type: TriggerType = TriggerType.MANUAL,
        **kwargs
    ) -> Optional[SurveyDistribution]:
        """Crée une distribution."""
        survey = self.get_survey(survey_id)
        if not survey:
            return None

        dist_id = str(uuid4())

        # Générer lien unique
        unique_link = f"https://survey.azalscore.com/s/{survey_id}/{dist_id}"

        distribution = SurveyDistribution(
            id=dist_id,
            survey_id=survey_id,
            channel=channel,
            name=name or f"{channel.value} distribution",
            trigger_type=trigger_type,
            recipients=recipients or [],
            recipient_count=len(recipients) if recipients else 0,
            unique_link=unique_link,
            **kwargs
        )

        # Générer code d'intégration
        if channel == DistributionChannel.EMBEDDED:
            distribution.embed_code = f'<iframe src="{unique_link}" width="100%" height="600"></iframe>'

        self._distributions[dist_id] = distribution
        return distribution

    def send_distribution(
        self,
        distribution_id: str
    ) -> Optional[SurveyDistribution]:
        """Envoie une distribution."""
        dist = self._distributions.get(distribution_id)
        if not dist:
            return None

        survey = self.get_survey(dist.survey_id)
        if not survey or survey.status != SurveyStatus.ACTIVE:
            return None

        # Simulation envoi
        if dist.channel == DistributionChannel.EMAIL:
            # En production: envoyer les emails
            dist.sent_count = dist.recipient_count

        elif dist.channel == DistributionChannel.SMS:
            # En production: envoyer les SMS
            dist.sent_count = dist.recipient_count

        dist.sent_at = datetime.now()
        return dist

    def get_distribution(self, distribution_id: str) -> Optional[SurveyDistribution]:
        """Récupère une distribution."""
        return self._distributions.get(distribution_id)

    def list_distributions(self, survey_id: str) -> List[SurveyDistribution]:
        """Liste les distributions d'un sondage."""
        return [
            d for d in self._distributions.values()
            if d.survey_id == survey_id
        ]

    # -------------------------------------------------------------------------
    # Réponses
    # -------------------------------------------------------------------------

    def start_response(
        self,
        survey_id: str,
        distribution_id: Optional[str] = None,
        respondent_id: Optional[str] = None,
        respondent_email: Optional[str] = None,
        **kwargs
    ) -> Optional[Response]:
        """Démarre une réponse."""
        survey = self.get_survey(survey_id)
        if not survey:
            return None

        if survey.status != SurveyStatus.ACTIVE:
            return None

        # Vérifier limite de réponses
        if survey.max_responses:
            if survey.response_count >= survey.max_responses:
                return None

        # Vérifier réponse multiple
        if not survey.allow_multiple_responses and respondent_id:
            existing = [
                r for r in self._responses.values()
                if r.survey_id == survey_id and
                   r.respondent_id == respondent_id and
                   r.status == ResponseStatus.COMPLETED
            ]
            if existing:
                return None

        response_id = str(uuid4())

        response = Response(
            id=response_id,
            survey_id=survey_id,
            distribution_id=distribution_id,
            respondent_id=respondent_id,
            respondent_email=respondent_email,
            **kwargs
        )

        self._responses[response_id] = response

        # Mettre à jour distribution
        if distribution_id:
            dist = self._distributions.get(distribution_id)
            if dist:
                dist.started_count += 1

        return response

    def save_answer(
        self,
        response_id: str,
        question_id: str,
        value: Any
    ) -> Optional[Answer]:
        """Enregistre une réponse."""
        response = self._responses.get(response_id)
        if not response:
            return None

        question = self._questions.get(question_id)
        if not question:
            return None

        answer_id = str(uuid4())

        # Parser la valeur selon le type
        text_value = None
        numeric_value = None
        selected_options = []

        if question.question_type in [QuestionType.TEXT_SHORT, QuestionType.TEXT_LONG]:
            text_value = str(value) if value else None

        elif question.question_type in [QuestionType.RATING, QuestionType.SCALE, QuestionType.NPS, QuestionType.NUMBER]:
            numeric_value = Decimal(str(value)) if value is not None else None

        elif question.question_type in [QuestionType.SINGLE_CHOICE, QuestionType.YES_NO]:
            selected_options = [str(value)] if value else []

        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            selected_options = value if isinstance(value, list) else [value]

        answer = Answer(
            id=answer_id,
            response_id=response_id,
            question_id=question_id,
            question_type=question.question_type,
            value=value,
            text_value=text_value,
            numeric_value=numeric_value,
            selected_options=selected_options
        )

        self._answers[answer_id] = answer
        response.answers[question_id] = value

        return answer

    def complete_response(self, response_id: str) -> Optional[Response]:
        """Termine une réponse."""
        response = self._responses.get(response_id)
        if not response:
            return None

        response.status = ResponseStatus.COMPLETED
        response.completed_at = datetime.now()
        response.completion_time_seconds = int(
            (response.completed_at - response.started_at).total_seconds()
        )

        # Mettre à jour le sondage
        survey = self.get_survey(response.survey_id)
        if survey:
            survey.response_count += 1
            self._update_survey_stats(survey)

        # Mettre à jour distribution
        if response.distribution_id:
            dist = self._distributions.get(response.distribution_id)
            if dist:
                dist.completed_count += 1

        return response

    def _update_survey_stats(self, survey: Survey):
        """Met à jour les statistiques du sondage."""
        responses = [
            r for r in self._responses.values()
            if r.survey_id == survey.id
        ]

        completed = [r for r in responses if r.status == ResponseStatus.COMPLETED]

        if responses:
            survey.completion_rate = Decimal(len(completed)) / Decimal(len(responses)) * 100

        if completed:
            total_time = sum(r.completion_time_seconds for r in completed)
            survey.avg_completion_time_seconds = total_time // len(completed)

    def get_response(self, response_id: str) -> Optional[Response]:
        """Récupère une réponse."""
        return self._responses.get(response_id)

    def list_responses(
        self,
        survey_id: str,
        *,
        status: Optional[ResponseStatus] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[Response], int]:
        """Liste les réponses."""
        results = []

        for response in self._responses.values():
            if response.survey_id != survey_id:
                continue
            if status and response.status != status:
                continue
            if from_date and response.started_at < from_date:
                continue
            if to_date and response.started_at > to_date:
                continue
            results.append(response)

        results.sort(key=lambda x: x.started_at, reverse=True)

        total = len(results)
        start = (page - 1) * page_size
        end = start + page_size

        return results[start:end], total

    def get_response_answers(self, response_id: str) -> List[Answer]:
        """Récupère les réponses d'une soumission."""
        return [
            a for a in self._answers.values()
            if a.response_id == response_id
        ]

    # -------------------------------------------------------------------------
    # Analytics
    # -------------------------------------------------------------------------

    def get_survey_analytics(self, survey_id: str) -> Optional[SurveyAnalytics]:
        """Génère l'analyse d'un sondage."""
        survey = self.get_survey(survey_id)
        if not survey:
            return None

        analytics = SurveyAnalytics(
            survey_id=survey_id,
            survey_title=survey.title
        )

        responses = [
            r for r in self._responses.values()
            if r.survey_id == survey_id
        ]

        analytics.total_responses = len(responses)
        analytics.completed_responses = len([
            r for r in responses if r.status == ResponseStatus.COMPLETED
        ])
        analytics.abandoned_responses = len([
            r for r in responses if r.status == ResponseStatus.ABANDONED
        ])

        if analytics.total_responses > 0:
            analytics.completion_rate = (
                Decimal(analytics.completed_responses) /
                Decimal(analytics.total_responses) * 100
            )

        completion_times = [
            r.completion_time_seconds for r in responses
            if r.status == ResponseStatus.COMPLETED and r.completion_time_seconds > 0
        ]
        if completion_times:
            analytics.avg_completion_time_seconds = sum(completion_times) // len(completion_times)

        # Par jour
        for response in responses:
            day = response.started_at.strftime("%Y-%m-%d")
            analytics.response_by_day[day] = analytics.response_by_day.get(day, 0) + 1

        # Par canal
        for response in responses:
            if response.distribution_id:
                dist = self._distributions.get(response.distribution_id)
                if dist:
                    channel = dist.channel.value
                    analytics.response_by_channel[channel] = (
                        analytics.response_by_channel.get(channel, 0) + 1
                    )

        # Par device
        for response in responses:
            device = response.device_type or "unknown"
            analytics.response_by_device[device] = (
                analytics.response_by_device.get(device, 0) + 1
            )

        # Analyse par question
        questions = self.list_questions(survey_id)
        for question in questions:
            q_analytics = self._analyze_question(question, responses)
            analytics.question_analytics.append(q_analytics)

            # NPS global
            if question.question_type == QuestionType.NPS and q_analytics.nps_score is not None:
                analytics.nps_overall = q_analytics.nps_score

        return analytics

    def _analyze_question(
        self,
        question: Question,
        responses: List[Response]
    ) -> QuestionAnalytics:
        """Analyse une question."""
        analytics = QuestionAnalytics(
            question_id=question.id,
            question_text=question.text,
            question_type=question.question_type
        )

        # Récupérer les réponses
        answers = [
            a for a in self._answers.values()
            if a.question_id == question.id
        ]

        analytics.total_responses = len(answers)
        analytics.skipped_count = len(responses) - len(answers)

        if len(responses) > 0:
            analytics.response_rate = Decimal(len(answers)) / Decimal(len(responses)) * 100

        if not answers:
            return analytics

        # Analyse selon le type
        if question.question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE, QuestionType.YES_NO]:
            # Compter les options
            for answer in answers:
                for opt_id in answer.selected_options:
                    analytics.option_counts[opt_id] = analytics.option_counts.get(opt_id, 0) + 1

            # Pourcentages
            total = sum(analytics.option_counts.values()) or 1
            for opt_id, count in analytics.option_counts.items():
                analytics.option_percentages[opt_id] = Decimal(count) / Decimal(total) * 100

        elif question.question_type in [QuestionType.RATING, QuestionType.SCALE, QuestionType.NUMBER]:
            # Statistiques numériques
            values = [float(a.numeric_value) for a in answers if a.numeric_value is not None]
            if values:
                analytics.numeric_stats = {
                    "min": Decimal(str(min(values))),
                    "max": Decimal(str(max(values))),
                    "avg": Decimal(str(statistics.mean(values))),
                    "median": Decimal(str(statistics.median(values)))
                }
                if len(values) > 1:
                    analytics.numeric_stats["std_dev"] = Decimal(str(statistics.stdev(values)))

        elif question.question_type == QuestionType.NPS:
            # Calcul NPS
            scores = [int(a.numeric_value) for a in answers if a.numeric_value is not None]
            if scores:
                promoters = len([s for s in scores if s >= 9])
                passives = len([s for s in scores if 7 <= s <= 8])
                detractors = len([s for s in scores if s <= 6])

                analytics.nps_breakdown = {
                    "promoters": promoters,
                    "passives": passives,
                    "detractors": detractors
                }

                total = len(scores)
                nps = ((promoters / total) - (detractors / total)) * 100
                analytics.nps_score = Decimal(str(round(nps, 1)))

        elif question.question_type in [QuestionType.TEXT_SHORT, QuestionType.TEXT_LONG]:
            # Collecter les textes
            analytics.text_responses = [
                a.text_value for a in answers
                if a.text_value
            ]

            # Fréquence des mots
            word_counts: Dict[str, int] = {}
            for text in analytics.text_responses:
                words = text.lower().split()
                for word in words:
                    if len(word) > 3:  # Ignorer petits mots
                        word_counts[word] = word_counts.get(word, 0) + 1

            # Top 20 mots
            analytics.word_frequency = dict(
                sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            )

        return analytics

    def export_responses(
        self,
        survey_id: str,
        format: str = "json"
    ) -> List[Dict[str, Any]]:
        """Exporte les réponses."""
        survey = self.get_survey(survey_id)
        if not survey:
            return []

        questions = self.list_questions(survey_id)
        question_map = {q.id: q for q in questions}

        results = []
        responses, _ = self.list_responses(survey_id, status=ResponseStatus.COMPLETED)

        for response in responses:
            row = {
                "response_id": response.id,
                "respondent_id": response.respondent_id,
                "respondent_email": response.respondent_email,
                "started_at": response.started_at.isoformat(),
                "completed_at": response.completed_at.isoformat() if response.completed_at else None,
                "completion_time_seconds": response.completion_time_seconds
            }

            # Ajouter les réponses
            for qid, value in response.answers.items():
                question = question_map.get(qid)
                if question:
                    key = f"Q{question.order + 1}: {question.text[:50]}"
                    row[key] = value

            results.append(row)

        return results

    # -------------------------------------------------------------------------
    # Templates
    # -------------------------------------------------------------------------

    def create_template_from_survey(
        self,
        survey_id: str,
        name: str,
        description: Optional[str] = None,
        is_public: bool = False
    ) -> Optional[SurveyTemplate]:
        """Crée un template depuis un sondage."""
        survey = self.get_survey(survey_id)
        if not survey:
            return None

        questions = self.list_questions(survey_id)

        template_id = str(uuid4())

        template = SurveyTemplate(
            id=template_id,
            tenant_id=self.tenant_id if not is_public else None,
            name=name,
            description=description,
            survey_type=survey.survey_type,
            questions=[
                {
                    "type": q.question_type.value,
                    "text": q.text,
                    "description": q.description,
                    "is_required": q.is_required,
                    "options": [{"text": o.text, "value": o.value} for o in q.options],
                    "min_value": q.min_value,
                    "max_value": q.max_value
                }
                for q in questions
            ],
            is_public=is_public
        )

        self._templates[template_id] = template
        return template

    def create_survey_from_template(
        self,
        template_id: str,
        title: str
    ) -> Optional[Survey]:
        """Crée un sondage depuis un template."""
        template = self._templates.get(template_id)
        if not template:
            return None

        # Vérifier accès
        if template.tenant_id and template.tenant_id != self.tenant_id:
            return None

        # Créer le sondage
        survey = self.create_survey(
            title=title,
            survey_type=template.survey_type,
            description=template.description
        )

        # Ajouter les questions
        for q_data in template.questions:
            self.add_question(
                survey.id,
                question_type=QuestionType(q_data["type"]),
                text=q_data["text"],
                description=q_data.get("description"),
                is_required=q_data.get("is_required", True),
                options=q_data.get("options"),
                min_value=q_data.get("min_value"),
                max_value=q_data.get("max_value")
            )

        template.usage_count += 1

        return survey

    def list_templates(
        self,
        include_public: bool = True
    ) -> List[SurveyTemplate]:
        """Liste les templates."""
        results = []

        for template in self._templates.values():
            if template.tenant_id == self.tenant_id:
                results.append(template)
            elif include_public and template.is_public:
                results.append(template)

        results.sort(key=lambda x: x.usage_count, reverse=True)
        return results


# ============================================================================
# FACTORY
# ============================================================================

def create_survey_service(tenant_id: str) -> SurveyService:
    """Factory pour créer un service de sondages."""
    return SurveyService(tenant_id)
