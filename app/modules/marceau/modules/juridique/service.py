"""
AZALS MODULE - Marceau Juridique Service
=========================================

Service d'assistance juridique automatisee.
Utilise l'intelligence LLM pour l'analyse de contrats et la conformite.

IMPORTANT: Ce module fournit une assistance et des suggestions.
Il ne remplace pas les conseils d'un professionnel du droit.

Actions:
    - analyze_contract: Analyse d'un contrat (clauses, risques)
    - check_compliance: Verification conformite RGPD/reglementaire
    - assess_risk: Evaluation des risques juridiques
    - generate_clause: Generation de clauses types
"""

import json
import logging
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.modules.marceau.llm_client import get_llm_client_for_tenant, extract_json_from_response
from app.modules.marceau.models import MarceauAction, ActionStatus

logger = logging.getLogger(__name__)


class JuridiqueService:
    """
    Service d'assistance juridique.
    Utilise le LLM pour analyser contrats et verifier conformite.
    """

    # Types de contrats reconnus
    CONTRACT_TYPES = [
        "cdi", "cdd", "freelance", "prestation",
        "vente", "location", "partenariat", "nda",
        "cgu", "cgv", "politique_confidentialite",
    ]

    # Risques juridiques courants
    RISK_CATEGORIES = [
        "clause_abusive",
        "manque_consentement",
        "donnees_personnelles",
        "propriete_intellectuelle",
        "responsabilite",
        "resiliation",
        "penalites",
        "juridiction",
    ]

    # Clauses types disponibles
    CLAUSE_TEMPLATES = {
        "confidentialite": "Clause de confidentialite NDA",
        "propriete_intellectuelle": "Clause de cession PI",
        "donnees_personnelles": "Clause RGPD",
        "limitation_responsabilite": "Clause de limitation de responsabilite",
        "resiliation": "Clause de resiliation anticipee",
        "force_majeure": "Clause de force majeure",
        "non_sollicitation": "Clause de non-sollicitation",
        "non_concurrence": "Clause de non-concurrence",
        "penalites": "Clause de penalites de retard",
        "juridiction": "Clause attributive de juridiction",
    }

    def __init__(self, tenant_id: str, db: Session):
        self.tenant_id = tenant_id
        self.db = db

    async def execute_action(
        self,
        action: str,
        data: dict,
        context: list[str],
    ) -> dict:
        """Execute une action juridique."""
        action_handlers = {
            "analyze_contract": self._analyze_contract,
            "check_compliance": self._check_compliance,
            "assess_risk": self._assess_risk,
            "generate_clause": self._generate_clause,
        }

        handler = action_handlers.get(action, self._unknown_action)
        return await handler(data, context)

    # ========================================================================
    # ANALYZE CONTRACT
    # ========================================================================

    async def _analyze_contract(self, data: dict, context: list[str]) -> dict:
        """
        Analyse un contrat et identifie les points cles.

        Args:
            data: {
                "contract_text": "Texte du contrat...",
                "contract_type": "prestation",  # optionnel
                "focus_areas": ["responsabilite", "resiliation"],  # optionnel
            }
        """
        logger.info("[Juridique] Analyse contrat")

        contract_text = data.get("contract_text", "")
        if not contract_text or len(contract_text) < 100:
            return {
                "success": False,
                "error": "Texte du contrat trop court ou manquant (min 100 caracteres)",
                "action": "analyze_contract",
            }

        contract_type = data.get("contract_type", "inconnu")
        focus_areas = data.get("focus_areas", [])

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            # Limiter le texte pour le prompt
            text_excerpt = contract_text[:8000]
            truncated = len(contract_text) > 8000

            focus_instruction = ""
            if focus_areas:
                focus_instruction = f"Concentre-toi particulierement sur: {', '.join(focus_areas)}"

            prompt = f"""Analyse ce contrat ({contract_type}) et fournis:

1. **Resume**: Resume en 2-3 phrases
2. **Parties**: Identification des parties
3. **Objet**: Objet principal du contrat
4. **Clauses cles**: Les 5-7 clauses les plus importantes
5. **Points d'attention**: Elements a surveiller ou negocier
6. **Risques identifies**: Risques potentiels pour chaque partie
7. **Recommandations**: Suggestions d'amelioration

{focus_instruction}

CONTRAT:
{text_excerpt}

{"[TEXTE TRONQUE - analyse basee sur les premiers 8000 caracteres]" if truncated else ""}

Reponds en JSON structure:
{{
    "summary": "resume...",
    "parties": {{"partie_a": "...", "partie_b": "..."}},
    "object": "objet du contrat",
    "key_clauses": [
        {{"name": "nom clause", "content": "resume", "assessment": "favorable/neutre/defavorable"}}
    ],
    "attention_points": ["point 1", "point 2"],
    "risks": [
        {{"risk": "description", "severity": "low/medium/high", "party_affected": "partie_a/partie_b/both"}}
    ],
    "recommendations": ["recommandation 1", "recommandation 2"]
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.1,
                max_tokens=2000,
                system_prompt="Tu es un juriste expert en droit des contrats francais. Analyse avec rigueur et objectivite.",
            )

            analysis = await extract_json_from_response(response)

            if not analysis:
                analysis = {
                    "summary": "Analyse non structuree disponible",
                    "raw_analysis": response[:1500],
                    "error": "Format JSON non obtenu",
                }

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="juridique",
                action_type="analyze_contract",
                status=ActionStatus.COMPLETED,
                input_data={
                    "contract_type": contract_type,
                    "text_length": len(contract_text),
                    "focus_areas": focus_areas,
                },
                output_data={
                    "has_analysis": True,
                    "risks_count": len(analysis.get("risks", [])),
                },
                reasoning="Analyse de contrat effectuee",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "analyze_contract",
                "action_id": str(action_record.id),
                "contract_type": contract_type,
                "analysis": analysis,
                "truncated": truncated,
                "disclaimer": "Cette analyse est fournie a titre indicatif et ne constitue pas un avis juridique professionnel.",
            }

        except Exception as e:
            logger.error(f"[Juridique] Erreur analyse contrat: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "analyze_contract",
            }

    # ========================================================================
    # CHECK COMPLIANCE
    # ========================================================================

    async def _check_compliance(self, data: dict, context: list[str]) -> dict:
        """
        Verifie la conformite RGPD et reglementaire.

        Args:
            data: {
                "document_text": "Texte du document (CGU, politique confidentialite...)",
                "document_type": "politique_confidentialite" | "cgu" | "cgv",
                "regulations": ["rgpd", "ecommerce"],  # Reglementations a verifier
            }
        """
        logger.info("[Juridique] Verification conformite")

        document_text = data.get("document_text", "")
        if not document_text:
            return {
                "success": False,
                "error": "Texte du document requis",
                "action": "check_compliance",
            }

        document_type = data.get("document_type", "inconnu")
        regulations = data.get("regulations", ["rgpd"])

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            # Construire les criteres de verification selon la reglementation
            criteria = self._get_compliance_criteria(document_type, regulations)

            prompt = f"""Verifie la conformite de ce document ({document_type}) aux reglementations: {', '.join(regulations)}

CRITERES A VERIFIER:
{json.dumps(criteria, indent=2, ensure_ascii=False)}

DOCUMENT:
{document_text[:6000]}

Pour chaque critere, indique:
- present: true/false
- conforme: true/false/partial
- commentaire: explication

Reponds en JSON:
{{
    "overall_compliance": "conforme/non_conforme/partiel",
    "compliance_score": 85,
    "criteria_results": [
        {{"criterion": "nom", "present": true, "compliant": true, "comment": "..."}}
    ],
    "missing_elements": ["element manquant 1"],
    "non_compliant_elements": ["element non conforme"],
    "recommendations": ["action corrective 1"]
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.1,
                max_tokens=1500,
                system_prompt="Tu es un expert en conformite RGPD et reglementation e-commerce europeenne.",
            )

            compliance_result = await extract_json_from_response(response)

            if not compliance_result:
                compliance_result = {
                    "overall_compliance": "inconnu",
                    "raw_analysis": response[:1000],
                    "error": "Analyse structuree non disponible",
                }

            # Determiner le statut de l'action
            status = ActionStatus.COMPLETED
            if compliance_result.get("overall_compliance") == "non_conforme":
                status = ActionStatus.NEEDS_VALIDATION

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="juridique",
                action_type="check_compliance",
                status=status,
                input_data={
                    "document_type": document_type,
                    "regulations": regulations,
                    "text_length": len(document_text),
                },
                output_data={
                    "overall_compliance": compliance_result.get("overall_compliance"),
                    "score": compliance_result.get("compliance_score"),
                },
                reasoning=f"Verification conformite: {compliance_result.get('overall_compliance')}",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "check_compliance",
                "action_id": str(action_record.id),
                "document_type": document_type,
                "regulations_checked": regulations,
                "compliance": compliance_result,
                "requires_attention": compliance_result.get("overall_compliance") != "conforme",
            }

        except Exception as e:
            logger.error(f"[Juridique] Erreur verification conformite: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "check_compliance",
            }

    def _get_compliance_criteria(self, doc_type: str, regulations: list[str]) -> list[dict]:
        """Retourne les criteres de conformite selon le type de document et reglementations."""
        criteria = []

        if "rgpd" in regulations:
            criteria.extend([
                {"name": "identite_responsable", "description": "Identite du responsable de traitement"},
                {"name": "finalites_traitement", "description": "Finalites du traitement clairement indiquees"},
                {"name": "base_legale", "description": "Base legale du traitement (consentement, contrat, interet legitime...)"},
                {"name": "duree_conservation", "description": "Duree de conservation des donnees"},
                {"name": "droits_personnes", "description": "Information sur les droits (acces, rectification, suppression, portabilite)"},
                {"name": "contact_dpo", "description": "Contact du DPO ou responsable donnees"},
                {"name": "transferts_hors_ue", "description": "Information sur les transferts hors UE"},
                {"name": "securite_donnees", "description": "Mesures de securite mentionnees"},
                {"name": "cookies", "description": "Information sur les cookies (si applicable)"},
            ])

        if "ecommerce" in regulations and doc_type in ["cgv", "cgu"]:
            criteria.extend([
                {"name": "identite_vendeur", "description": "Identite complete du vendeur (SIRET, adresse...)"},
                {"name": "prix_ttc", "description": "Prix TTC clairement indiques"},
                {"name": "frais_livraison", "description": "Frais de livraison indiques"},
                {"name": "droit_retractation", "description": "Droit de retractation 14 jours"},
                {"name": "garanties", "description": "Garanties legales (conformite, vices caches)"},
                {"name": "mediation", "description": "Information sur la mediation consommateur"},
                {"name": "conditions_paiement", "description": "Conditions de paiement"},
            ])

        return criteria

    # ========================================================================
    # ASSESS RISK
    # ========================================================================

    async def _assess_risk(self, data: dict, context: list[str]) -> dict:
        """
        Evalue les risques juridiques d'une situation.

        Args:
            data: {
                "situation": "Description de la situation...",
                "domain": "commercial" | "travail" | "pi" | "donnees" | "general",
                "documents": ["contrat X", "email Y"],  # Documents lies (optionnel)
            }
        """
        logger.info("[Juridique] Evaluation risques")

        situation = data.get("situation", "")
        if not situation:
            return {
                "success": False,
                "error": "Description de la situation requise",
                "action": "assess_risk",
            }

        domain = data.get("domain", "general")
        documents = data.get("documents", [])

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            prompt = f"""Evalue les risques juridiques de cette situation (domaine: {domain}):

SITUATION:
{situation}

{"DOCUMENTS ASSOCIES: " + ", ".join(documents) if documents else ""}

Analyse les risques selon:
1. Nature du risque
2. Probabilite de realisation
3. Impact potentiel
4. Parties concernees
5. Mesures de mitigation

Reponds en JSON:
{{
    "risk_level": "low/medium/high/critical",
    "summary": "resume de l'evaluation",
    "risks": [
        {{
            "name": "nom du risque",
            "description": "description",
            "probability": "low/medium/high",
            "impact": "low/medium/high",
            "affected_parties": ["partie 1"],
            "mitigation": "mesures de mitigation"
        }}
    ],
    "immediate_actions": ["action urgente si necessaire"],
    "recommended_consultation": true/false,
    "consultation_type": "avocat/expert-comptable/dpo/autre"
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.2,
                max_tokens=1500,
                system_prompt="Tu es un conseiller juridique experimente. Evalue les risques avec prudence et recommande une consultation professionnelle en cas de doute.",
            )

            risk_assessment = await extract_json_from_response(response)

            if not risk_assessment:
                risk_assessment = {
                    "risk_level": "unknown",
                    "summary": response[:500],
                    "error": "Evaluation structuree non disponible",
                    "recommended_consultation": True,
                }

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="juridique",
                action_type="assess_risk",
                status=ActionStatus.COMPLETED,
                input_data={
                    "domain": domain,
                    "situation_length": len(situation),
                    "documents_count": len(documents),
                },
                output_data={
                    "risk_level": risk_assessment.get("risk_level"),
                    "risks_count": len(risk_assessment.get("risks", [])),
                },
                reasoning=f"Evaluation risques: niveau {risk_assessment.get('risk_level')}",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "assess_risk",
                "action_id": str(action_record.id),
                "domain": domain,
                "assessment": risk_assessment,
                "disclaimer": "Cette evaluation ne remplace pas l'avis d'un professionnel du droit. En cas de risque eleve, consultez un avocat.",
            }

        except Exception as e:
            logger.error(f"[Juridique] Erreur evaluation risques: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "assess_risk",
            }

    # ========================================================================
    # GENERATE CLAUSE
    # ========================================================================

    async def _generate_clause(self, data: dict, context: list[str]) -> dict:
        """
        Genere une clause type adaptee.

        Args:
            data: {
                "clause_type": "confidentialite" | "resiliation" | "rgpd" | ...,
                "context": {
                    "partie_a": "Nom societe A",
                    "partie_b": "Nom societe B",
                    "duree": "12 mois",
                    "specificites": ["clause stricte", "penalites elevees"],
                },
                "style": "standard" | "strict" | "souple",
            }
        """
        logger.info("[Juridique] Generation clause")

        clause_type = data.get("clause_type", "")
        if clause_type not in self.CLAUSE_TEMPLATES:
            return {
                "success": False,
                "error": f"Type de clause inconnu: {clause_type}",
                "available_types": list(self.CLAUSE_TEMPLATES.keys()),
                "action": "generate_clause",
            }

        clause_context = data.get("context", {})
        style = data.get("style", "standard")

        try:
            llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

            clause_name = self.CLAUSE_TEMPLATES[clause_type]

            style_instruction = {
                "standard": "Redige une clause equilibree, conforme aux standards du marche.",
                "strict": "Redige une clause protectrice avec des obligations renforcees et des penalites.",
                "souple": "Redige une clause flexible permettant des adaptations.",
            }.get(style, "")

            prompt = f"""Redige une clause de type "{clause_name}" pour un contrat.

CONTEXTE:
{json.dumps(clause_context, indent=2, ensure_ascii=False) if clause_context else "Contexte standard"}

STYLE DEMANDE: {style}
{style_instruction}

Redige la clause en francais juridique professionnel, prete a etre inseree dans un contrat.
Inclus les elements habituels de ce type de clause.

Reponds en JSON:
{{
    "clause_title": "Titre de la clause",
    "clause_text": "Texte complet de la clause...",
    "key_points": ["point cle 1", "point cle 2"],
    "customization_notes": "Notes pour personnalisation si necessaire",
    "legal_references": ["reference legale si applicable"]
}}"""

            response = await llm.generate(
                prompt,
                temperature=0.3,
                max_tokens=1500,
                system_prompt="Tu es un juriste redacteur de contrats. Redige des clauses precises, claires et juridiquement solides.",
            )

            clause_result = await extract_json_from_response(response)

            if not clause_result:
                # Extraire le texte brut si pas de JSON
                clause_result = {
                    "clause_title": clause_name,
                    "clause_text": response,
                    "key_points": [],
                    "note": "Clause generee sans formatage structure",
                }

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="juridique",
                action_type="generate_clause",
                status=ActionStatus.COMPLETED,
                input_data={
                    "clause_type": clause_type,
                    "style": style,
                    "has_context": bool(clause_context),
                },
                output_data={
                    "clause_title": clause_result.get("clause_title"),
                    "text_length": len(clause_result.get("clause_text", "")),
                },
                reasoning=f"Clause {clause_type} ({style}) generee",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "generate_clause",
                "action_id": str(action_record.id),
                "clause_type": clause_type,
                "style": style,
                "clause": clause_result,
                "disclaimer": "Cette clause est un modele a adapter. Faites-la valider par un juriste avant utilisation.",
            }

        except Exception as e:
            logger.error(f"[Juridique] Erreur generation clause: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "generate_clause",
            }

    # ========================================================================
    # UNKNOWN ACTION
    # ========================================================================

    async def _unknown_action(self, data: dict, context: list[str]) -> dict:
        """Gere les actions non reconnues."""
        return {
            "success": False,
            "error": "Action juridique non reconnue",
            "available_actions": [
                "analyze_contract",
                "check_compliance",
                "assess_risk",
                "generate_clause",
            ],
            "available_clause_types": list(self.CLAUSE_TEMPLATES.keys()),
        }
