"""
AZALS MODULE - Marceau Recrutement Service
===========================================

Service de recrutement automatise.
Utilise l'intelligence LLM pour le scoring de CV et l'assistance recrutement.

Actions:
    - source_candidates: Recherche de candidats (parsing offres)
    - score_candidate: Scoring CV via LLM
    - schedule_interview: Planification entretien
    - send_offer: Envoi proposition d'embauche
"""
from __future__ import annotations


import json
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy.orm import Session

from app.modules.marceau.llm_client import get_llm_client_for_tenant, extract_json_from_response
from app.modules.marceau.models import MarceauAction, ActionStatus

logger = logging.getLogger(__name__)


class RecrutementService:
    """
    Service de recrutement automatise.
    Utilise le LLM pour analyser les CV et assister le processus de recrutement.
    """

    # Statuts de candidature
    CANDIDATE_STATUSES = [
        "nouveau",
        "preselectionnne",
        "entretien_planifie",
        "entretien_passe",
        "evaluation",
        "offre_envoyee",
        "accepte",
        "refuse",
        "desiste",
    ]

    # Types d'entretien
    INTERVIEW_TYPES = [
        "telephonique",
        "video",
        "technique",
        "rh",
        "manager",
        "direction",
        "collectif",
    ]

    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db

    async def execute_action(
        self,
        action: str,
        data: dict,
        context: list[str],
    ) -> dict:
        """Execute une action recrutement."""
        action_handlers = {
            "source_candidates": self._source_candidates,
            "score_candidate": self._score_candidate,
            "schedule_interview": self._schedule_interview,
            "send_offer": self._send_offer,
            "create_job_posting": self._create_job_posting,
            "screen_applications": self._screen_applications,
        }

        handler = action_handlers.get(action, self._unknown_action)
        return await handler(data, context)

    # ========================================================================
    # SOURCE CANDIDATES
    # ========================================================================

    async def _source_candidates(self, data: dict, context: list[str]) -> dict:
        """
        Analyse une offre d'emploi et suggere des criteres de recherche.

        Note: L'integration LinkedIn API necessite des credentials specifiques.
        Cette fonction prepare les criteres pour la recherche manuelle ou API.

        Args:
            data: {
                "job_title": "Developpeur Python Senior",
                "job_description": "Description du poste...",
                "requirements": ["Python", "FastAPI", "PostgreSQL"],
                "experience_years": 5,
                "location": "Paris",
                "remote_policy": "hybrid",  # onsite, hybrid, full_remote
            }
        """
        logger.info(f"[Recrutement] Sourcing candidats: {data.get('job_title')}")

        job_title = data.get("job_title", "")
        if not job_title:
            return {
                "success": False,
                "error": "Titre du poste requis",
                "action": "source_candidates",
            }

        job_description = data.get("job_description", "")
        requirements = data.get("requirements", [])
        experience_years = data.get("experience_years", 0)
        location = data.get("location", "")

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""Analyse cette offre d'emploi et genere des criteres de recherche de candidats:

POSTE: {job_title}
DESCRIPTION: {job_description[:2000] if job_description else "Non fournie"}
COMPETENCES REQUISES: {', '.join(requirements) if requirements else "Non specifiees"}
EXPERIENCE: {experience_years} ans
LOCALISATION: {location or "Non specifiee"}

Genere:
1. Mots-cles LinkedIn optimises pour la recherche
2. Competences cles a rechercher
3. Titres de postes alternatifs/similaires
4. Entreprises cibles potentielles (secteur/type)
5. Questions de presqualification suggerees

Reponds en JSON:
{{
    "linkedin_keywords": ["mot-cle 1", "mot-cle 2"],
    "boolean_search": "chaine de recherche booleenne",
    "key_skills": ["competence 1", "competence 2"],
    "alternative_titles": ["titre 1", "titre 2"],
    "target_companies": ["type entreprise 1"],
    "screening_questions": [
        {{"question": "question", "expected_answer": "reponse attendue"}}
    ],
    "salary_range_suggestion": {{"min": 45000, "max": 60000, "currency": "EUR"}}
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.3,
                max_tokens=1200,
                system_prompt="Tu es un expert en recrutement tech. Optimise la recherche de talents.",
            )

            search_criteria = await extract_json_from_response(response)

            if not search_criteria:
                search_criteria = {
                    "linkedin_keywords": [job_title] + requirements[:3],
                    "key_skills": requirements,
                    "error": "Analyse structuree non disponible",
                }

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="recrutement",
                action_type="source_candidates",
                status=ActionStatus.COMPLETED,
                input_data={
                    "job_title": job_title,
                    "requirements_count": len(requirements),
                    "location": location,
                },
                output_data={
                    "keywords_count": len(search_criteria.get("linkedin_keywords", [])),
                    "has_boolean_search": bool(search_criteria.get("boolean_search")),
                },
                reasoning=f"Criteres de recherche generes pour {job_title}",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "source_candidates",
                "action_id": str(action_record.id),
                "job_title": job_title,
                "search_criteria": search_criteria,
                "platforms": ["LinkedIn", "Indeed", "Welcome to the Jungle", "APEC"],
                "note": "Utilisez ces criteres pour rechercher des candidats sur les plateformes.",
            }

        except Exception as e:
            logger.error(f"[Recrutement] Erreur sourcing: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "source_candidates",
            }

    # ========================================================================
    # SCORE CANDIDATE
    # ========================================================================

    async def _score_candidate(self, data: dict, context: list[str]) -> dict:
        """
        Evalue et score un CV par rapport a une offre.

        Args:
            data: {
                "cv_text": "Contenu du CV...",
                "job_title": "Developpeur Python Senior",
                "requirements": ["Python", "FastAPI", "PostgreSQL"],
                "nice_to_have": ["Docker", "AWS"],
                "experience_min": 5,
            }
        """
        logger.info("[Recrutement] Scoring candidat")

        cv_text = data.get("cv_text", "")
        if not cv_text or len(cv_text) < 50:
            return {
                "success": False,
                "error": "Contenu du CV trop court ou manquant",
                "action": "score_candidate",
            }

        job_title = data.get("job_title", "")
        requirements = data.get("requirements", [])
        nice_to_have = data.get("nice_to_have", [])
        experience_min = data.get("experience_min", 0)

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""Analyse ce CV par rapport au poste et fournis une evaluation detaillee:

POSTE RECHERCHE: {job_title}
COMPETENCES REQUISES: {', '.join(requirements) if requirements else "Non specifiees"}
COMPETENCES APPRECIEES: {', '.join(nice_to_have) if nice_to_have else "Non specifiees"}
EXPERIENCE MINIMUM: {experience_min} ans

CV DU CANDIDAT:
{cv_text[:5000]}

Evalue selon ces criteres (score 0-100):
1. Adequation competences techniques
2. Experience pertinente
3. Formation/certifications
4. Qualite du parcours (progression, stabilite)
5. Adequation culturelle (si elements disponibles)

Reponds en JSON:
{{
    "overall_score": 75,
    "recommendation": "shortlist/maybe/reject",
    "scores": {{
        "technical_skills": 80,
        "experience": 70,
        "education": 75,
        "career_trajectory": 72,
        "cultural_fit": 65
    }},
    "matched_requirements": ["Python", "FastAPI"],
    "missing_requirements": ["AWS"],
    "matched_nice_to_have": ["Docker"],
    "strengths": ["point fort 1", "point fort 2"],
    "concerns": ["point attention 1"],
    "experience_years_estimated": 6,
    "current_position": "titre actuel",
    "interview_focus_areas": ["sujet a approfondir en entretien"],
    "summary": "Resume en 2-3 phrases"
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.2,
                max_tokens=1500,
                system_prompt="Tu es un expert en recrutement tech. Evalue objectivement les candidatures.",
            )

            evaluation = await extract_json_from_response(response)

            if not evaluation:
                evaluation = {
                    "overall_score": 0,
                    "recommendation": "manual_review",
                    "raw_analysis": response[:800],
                    "error": "Evaluation structuree non disponible",
                }

            # Determiner le statut selon le score
            overall_score = evaluation.get("overall_score", 0)
            if overall_score >= 70:
                status = ActionStatus.COMPLETED
            else:
                status = ActionStatus.NEEDS_VALIDATION

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="recrutement",
                action_type="score_candidate",
                status=status,
                input_data={
                    "job_title": job_title,
                    "cv_length": len(cv_text),
                    "requirements_count": len(requirements),
                },
                output_data={
                    "overall_score": overall_score,
                    "recommendation": evaluation.get("recommendation"),
                    "matched_requirements": len(evaluation.get("matched_requirements", [])),
                },
                reasoning=f"Score {overall_score}/100 - {evaluation.get('recommendation')}",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "score_candidate",
                "action_id": str(action_record.id),
                "job_title": job_title,
                "evaluation": evaluation,
                "next_steps": self._get_next_steps(evaluation.get("recommendation")),
            }

        except Exception as e:
            logger.error(f"[Recrutement] Erreur scoring: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "score_candidate",
            }

    def _get_next_steps(self, recommendation: str) -> list[str]:
        """Retourne les prochaines etapes selon la recommandation."""
        steps = {
            "shortlist": [
                "Planifier un entretien telephonique",
                "Verifier les references",
                "Preparer les questions techniques",
            ],
            "maybe": [
                "Faire evaluer par un autre recruteur",
                "Demander des precisions au candidat",
                "Comparer avec autres candidatures",
            ],
            "reject": [
                "Envoyer email de reponse negative personnalise",
                "Conserver le profil pour postes futurs si pertinent",
            ],
        }
        return steps.get(recommendation, ["Revue manuelle necessaire"])

    # ========================================================================
    # SCHEDULE INTERVIEW
    # ========================================================================

    async def _schedule_interview(self, data: dict, context: list[str]) -> dict:
        """
        Planifie un entretien avec un candidat.

        Args:
            data: {
                "candidate_name": "Jean Dupont",
                "candidate_email": "jean.dupont@email.com",
                "interview_type": "technique",
                "interviewer_ids": ["uuid1", "uuid2"],
                "proposed_slots": [
                    {"date": "2024-02-15", "time": "10:00"},
                    {"date": "2024-02-15", "time": "14:00"},
                ],
                "duration_minutes": 60,
                "location": "video",  # video, onsite, phone
                "job_title": "Developpeur Python",
            }
        """
        logger.info(f"[Recrutement] Planification entretien: {data.get('candidate_name')}")

        required = ["candidate_name", "candidate_email", "interview_type"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return {
                "success": False,
                "error": f"Champs manquants: {', '.join(missing)}",
                "action": "schedule_interview",
            }

        candidate_name = data.get("candidate_name")
        candidate_email = data.get("candidate_email")
        interview_type = data.get("interview_type")
        proposed_slots = data.get("proposed_slots", [])
        duration = data.get("duration_minutes", 60)
        location = data.get("location", "video")
        job_title = data.get("job_title", "")

        try:
            # Generer l'email d'invitation
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""Redige un email professionnel d'invitation a un entretien:

CANDIDAT: {candidate_name}
POSTE: {job_title}
TYPE ENTRETIEN: {interview_type}
DUREE: {duration} minutes
FORMAT: {location}
CRENEAUX PROPOSES: {json.dumps(proposed_slots, ensure_ascii=False) if proposed_slots else "A convenir"}

L'email doit:
- Etre professionnel mais chaleureux
- Presenter le type d'entretien
- Proposer les creneaux ou demander les disponibilites
- Preciser les modalites (lien visio, adresse...)
- Mentionner ce que le candidat doit preparer

Reponds en JSON:
{{
    "subject": "Objet de l'email",
    "body": "Corps de l'email",
    "calendar_title": "Titre pour invitation calendrier"
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.4,
                max_tokens=800,
                system_prompt="Tu es un recruteur professionnel. Redige des communications engageantes.",
            )

            email_content = await extract_json_from_response(response)

            if not email_content:
                email_content = {
                    "subject": f"Invitation entretien - {job_title}",
                    "body": response,
                    "calendar_title": f"Entretien {interview_type} - {candidate_name}",
                }

            # Preparer les donnees d'invitation
            interview_data = {
                "candidate": {
                    "name": candidate_name,
                    "email": candidate_email,
                },
                "interview_type": interview_type,
                "duration_minutes": duration,
                "location": location,
                "proposed_slots": proposed_slots,
                "job_title": job_title,
                "email": email_content,
            }

            # Enregistrer l'action (en attente de validation pour envoi)
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="recrutement",
                action_type="schedule_interview",
                status=ActionStatus.NEEDS_VALIDATION,
                input_data={
                    "candidate_name": candidate_name,
                    "interview_type": interview_type,
                    "slots_count": len(proposed_slots),
                },
                output_data=interview_data,
                reasoning=f"Entretien {interview_type} a planifier avec {candidate_name}",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "schedule_interview",
                "action_id": str(action_record.id),
                "status": "pending_validation",
                "interview": interview_data,
                "message": f"Invitation prete pour {candidate_name}. Validez pour envoyer.",
                "requires_validation": True,
            }

        except Exception as e:
            logger.error(f"[Recrutement] Erreur planification: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "schedule_interview",
            }

    # ========================================================================
    # SEND OFFER
    # ========================================================================

    async def _send_offer(self, data: dict, context: list[str]) -> dict:
        """
        Prepare une proposition d'embauche.

        Args:
            data: {
                "candidate_name": "Jean Dupont",
                "candidate_email": "jean.dupont@email.com",
                "job_title": "Developpeur Python Senior",
                "department": "Engineering",
                "contract_type": "CDI",
                "start_date": "2024-03-01",
                "salary": {
                    "gross_annual": 55000,
                    "currency": "EUR",
                    "variable": 5000,
                },
                "benefits": ["mutuelle", "tickets restaurant", "teletravail 2j/semaine"],
                "probation_months": 3,
                "response_deadline": "2024-02-20",
            }
        """
        logger.info(f"[Recrutement] Preparation offre: {data.get('candidate_name')}")

        required = ["candidate_name", "candidate_email", "job_title", "contract_type", "salary"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return {
                "success": False,
                "error": f"Champs manquants: {', '.join(missing)}",
                "action": "send_offer",
            }

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            salary = data.get("salary", {})
            benefits = data.get("benefits", [])

            prompt = f"""Redige une lettre de proposition d'embauche professionnelle:

CANDIDAT: {data.get('candidate_name')}
POSTE: {data.get('job_title')}
DEPARTEMENT: {data.get('department', 'Non specifie')}
TYPE CONTRAT: {data.get('contract_type')}
DATE DEBUT SOUHAITEE: {data.get('start_date', 'A convenir')}

REMUNERATION:
- Salaire brut annuel: {salary.get('gross_annual')} {salary.get('currency', 'EUR')}
- Part variable: {salary.get('variable', 0)} {salary.get('currency', 'EUR')}

AVANTAGES: {', '.join(benefits) if benefits else 'Standard entreprise'}
PERIODE ESSAI: {data.get('probation_months', 3)} mois
DATE LIMITE REPONSE: {data.get('response_deadline', '7 jours')}

La lettre doit:
- Exprimer l'enthousiasme de l'entreprise
- Detailler clairement l'offre
- Presenter les prochaines etapes
- Rester professionnelle et engageante

Reponds en JSON:
{{
    "subject": "Objet de l'email",
    "greeting": "Formule d'introduction",
    "body": "Corps de la lettre (plusieurs paragraphes)",
    "closing": "Formule de cloture",
    "key_points_summary": ["point cle 1", "point cle 2"]
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.3,
                max_tokens=1500,
                system_prompt="Tu es un DRH. Redige des propositions d'embauche attractives et professionnelles.",
            )

            offer_letter = await extract_json_from_response(response)

            if not offer_letter:
                offer_letter = {
                    "subject": f"Proposition d'embauche - {data.get('job_title')}",
                    "body": response,
                }

            # Construire l'offre complete
            offer_data = {
                "candidate": {
                    "name": data.get("candidate_name"),
                    "email": data.get("candidate_email"),
                },
                "position": {
                    "title": data.get("job_title"),
                    "department": data.get("department"),
                    "contract_type": data.get("contract_type"),
                    "start_date": data.get("start_date"),
                },
                "compensation": {
                    "gross_annual": salary.get("gross_annual"),
                    "variable": salary.get("variable", 0),
                    "currency": salary.get("currency", "EUR"),
                    "benefits": benefits,
                },
                "terms": {
                    "probation_months": data.get("probation_months", 3),
                    "response_deadline": data.get("response_deadline"),
                },
                "letter": offer_letter,
            }

            # Enregistrer l'action (en attente de validation)
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="recrutement",
                action_type="send_offer",
                status=ActionStatus.NEEDS_VALIDATION,
                input_data={
                    "candidate_name": data.get("candidate_name"),
                    "job_title": data.get("job_title"),
                    "salary": salary.get("gross_annual"),
                },
                output_data={
                    "offer_prepared": True,
                    "contract_type": data.get("contract_type"),
                },
                reasoning=f"Offre {data.get('job_title')} preparee pour {data.get('candidate_name')}",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "send_offer",
                "action_id": str(action_record.id),
                "status": "pending_validation",
                "offer": offer_data,
                "message": f"Offre prete pour {data.get('candidate_name')}. Validez avant envoi.",
                "requires_validation": True,
                "next_steps": [
                    "Valider l'offre",
                    "Preparer le contrat de travail",
                    "Organiser l'onboarding",
                ],
            }

        except Exception as e:
            logger.error(f"[Recrutement] Erreur offre: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "send_offer",
            }

    # ========================================================================
    # CREATE JOB POSTING
    # ========================================================================

    async def _create_job_posting(self, data: dict, context: list[str]) -> dict:
        """
        Genere une annonce d'emploi optimisee.

        Args:
            data: {
                "job_title": "Developpeur Python Senior",
                "department": "Engineering",
                "responsibilities": ["Developper...", "Maintenir..."],
                "requirements": ["Python 5+ ans", "FastAPI", "PostgreSQL"],
                "nice_to_have": ["Docker", "AWS", "CI/CD"],
                "salary_range": {"min": 45000, "max": 60000},
                "location": "Paris",
                "remote_policy": "hybrid",
                "company_culture": "description culture...",
            }
        """
        logger.info(f"[Recrutement] Creation annonce: {data.get('job_title')}")

        job_title = data.get("job_title", "")
        if not job_title:
            return {
                "success": False,
                "error": "Titre du poste requis",
                "action": "create_job_posting",
            }

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""Redige une annonce d'emploi attractive et complete:

POSTE: {job_title}
DEPARTEMENT: {data.get('department', 'Non specifie')}
RESPONSABILITES: {json.dumps(data.get('responsibilities', []), ensure_ascii=False)}
COMPETENCES REQUISES: {json.dumps(data.get('requirements', []), ensure_ascii=False)}
COMPETENCES APPRECIEES: {json.dumps(data.get('nice_to_have', []), ensure_ascii=False)}
SALAIRE: {json.dumps(data.get('salary_range', {}), ensure_ascii=False)}
LOCALISATION: {data.get('location', 'Non specifie')}
TELETRAVAIL: {data.get('remote_policy', 'Non specifie')}
CULTURE: {data.get('company_culture', '')[:500]}

L'annonce doit:
- Avoir un titre accrocheur
- Presenter l'entreprise brievement
- Detailler le poste de maniere engageante
- Lister les competences de maniere claire
- Mettre en avant les avantages
- Inciter a postuler

Reponds en JSON:
{{
    "title": "Titre optimise pour SEO",
    "teaser": "Phrase d'accroche courte",
    "company_intro": "Introduction entreprise (2-3 phrases)",
    "role_description": "Description du role (paragraphe)",
    "responsibilities": ["responsabilite 1 formulee"],
    "required_skills": ["competence 1 formulee"],
    "nice_to_have": ["bonus 1"],
    "benefits": ["avantage 1"],
    "application_process": "Description du processus",
    "call_to_action": "Appel a l'action final",
    "seo_keywords": ["mot-cle 1", "mot-cle 2"]
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.4,
                max_tokens=1500,
                system_prompt="Tu es un expert en recrutement. Redige des annonces qui attirent les meilleurs talents.",
            )

            job_posting = await extract_json_from_response(response)

            if not job_posting:
                job_posting = {
                    "title": job_title,
                    "raw_content": response,
                }

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="recrutement",
                action_type="create_job_posting",
                status=ActionStatus.COMPLETED,
                input_data={"job_title": job_title},
                output_data={"posting_generated": True},
                reasoning=f"Annonce generee pour {job_title}",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "create_job_posting",
                "action_id": str(action_record.id),
                "job_posting": job_posting,
                "platforms_suggested": [
                    "LinkedIn Jobs",
                    "Welcome to the Jungle",
                    "Indeed",
                    "Site carriere entreprise",
                ],
            }

        except Exception as e:
            logger.error(f"[Recrutement] Erreur annonce: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "create_job_posting",
            }

    # ========================================================================
    # SCREEN APPLICATIONS
    # ========================================================================

    async def _screen_applications(self, data: dict, context: list[str]) -> dict:
        """
        Pre-filtre un lot de candidatures.

        Args:
            data: {
                "job_title": "Developpeur Python",
                "requirements": ["Python", "FastAPI"],
                "candidates": [
                    {"name": "Jean", "cv_summary": "5 ans Python..."},
                    {"name": "Marie", "cv_summary": "3 ans Java..."},
                ]
            }
        """
        logger.info("[Recrutement] Screening candidatures")

        candidates = data.get("candidates", [])
        if not candidates:
            return {
                "success": False,
                "error": "Liste de candidats requise",
                "action": "screen_applications",
            }

        job_title = data.get("job_title", "")
        requirements = data.get("requirements", [])

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            # Limiter a 10 candidats par lot
            batch = candidates[:10]

            prompt = f"""Pre-filtre ces candidatures pour le poste de {job_title}:

COMPETENCES REQUISES: {', '.join(requirements)}

CANDIDATS:
{json.dumps(batch, indent=2, ensure_ascii=False)}

Pour chaque candidat, donne:
- Score rapide (0-100)
- Decision: shortlist/maybe/reject
- Justification courte (1 phrase)

Reponds en JSON:
{{
    "results": [
        {{"name": "nom", "score": 75, "decision": "shortlist", "reason": "..."}}
    ],
    "summary": {{
        "total": 10,
        "shortlisted": 3,
        "maybe": 4,
        "rejected": 3
    }}
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.2,
                max_tokens=1200,
                system_prompt="Tu es un recruteur efficace. Filtre rapidement mais equitablement.",
            )

            screening = await extract_json_from_response(response)

            if not screening:
                screening = {
                    "results": [],
                    "error": "Screening non disponible",
                }

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="recrutement",
                action_type="screen_applications",
                status=ActionStatus.COMPLETED,
                input_data={
                    "job_title": job_title,
                    "candidates_count": len(candidates),
                },
                output_data=screening.get("summary", {}),
                reasoning=f"Screening {len(batch)} candidatures",
            )
            self.db.add(action_record)
            self.db.commit()

            return {
                "success": True,
                "action": "screen_applications",
                "action_id": str(action_record.id),
                "job_title": job_title,
                "screening": screening,
                "processed": len(batch),
                "remaining": max(0, len(candidates) - 10),
            }

        except Exception as e:
            logger.error(f"[Recrutement] Erreur screening: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "screen_applications",
            }

    # ========================================================================
    # UNKNOWN ACTION
    # ========================================================================

    async def _unknown_action(self, data: dict, context: list[str]) -> dict:
        """Gere les actions non reconnues."""
        return {
            "success": False,
            "error": "Action recrutement non reconnue",
            "available_actions": [
                "source_candidates",
                "score_candidate",
                "schedule_interview",
                "send_offer",
                "create_job_posting",
                "screen_applications",
            ],
        }
