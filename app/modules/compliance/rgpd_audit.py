"""
AZALS MODULE - Service d'Audit RGPD
====================================

Service d'audit automatisé pour vérifier la conformité RGPD.
Intègre le module compliance et le Pack France RGPD.

Checklist RGPD complète:
- Article 5: Principes relatifs au traitement
- Article 6: Licéité du traitement
- Article 7: Conditions applicables au consentement
- Article 12-22: Droits des personnes concernées
- Article 24-25: Responsabilité et protection dès la conception
- Article 28-29: Sous-traitance
- Article 30: Registre des traitements
- Article 32-34: Sécurité et notification des violations
- Article 35-36: Analyse d'impact (DPIA)
- Article 37-39: DPO
"""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from .models import (
    ComplianceAssessment, ComplianceGap, ComplianceAction,
    Regulation, Requirement, ComplianceStatus, RegulationType,
    RequirementPriority, RiskLevel, AssessmentStatus, ActionStatus
)


class RGPDArticle(str, Enum):
    """Articles RGPD vérifiés."""
    ART_5_PRINCIPLES = "Article 5 - Principes"
    ART_6_LAWFULNESS = "Article 6 - Licéité"
    ART_7_CONSENT = "Article 7 - Consentement"
    ART_12_TRANSPARENCY = "Article 12 - Transparence"
    ART_13_14_INFORMATION = "Article 13-14 - Information"
    ART_15_ACCESS = "Article 15 - Droit d'accès"
    ART_16_RECTIFICATION = "Article 16 - Rectification"
    ART_17_ERASURE = "Article 17 - Effacement"
    ART_18_RESTRICTION = "Article 18 - Limitation"
    ART_19_NOTIFICATION = "Article 19 - Notification"
    ART_20_PORTABILITY = "Article 20 - Portabilité"
    ART_21_OBJECTION = "Article 21 - Opposition"
    ART_22_PROFILING = "Article 22 - Profilage"
    ART_24_ACCOUNTABILITY = "Article 24 - Responsabilité"
    ART_25_BY_DESIGN = "Article 25 - Privacy by Design"
    ART_28_PROCESSORS = "Article 28 - Sous-traitants"
    ART_30_RECORDS = "Article 30 - Registre"
    ART_32_SECURITY = "Article 32 - Sécurité"
    ART_33_BREACH_NOTIFICATION = "Article 33 - Notification CNIL"
    ART_34_COMMUNICATION = "Article 34 - Communication"
    ART_35_DPIA = "Article 35 - AIPD"
    ART_37_DPO = "Article 37 - DPO"


@dataclass
class RGPDAuditCheck:
    """Résultat d'un contrôle RGPD."""
    article: RGPDArticle
    title: str
    description: str
    status: ComplianceStatus
    score: int  # 0-100
    findings: list[str]
    recommendations: list[str]
    evidence: list[str]
    risk_level: RiskLevel


@dataclass
class RGPDAuditResult:
    """Résultat complet de l'audit RGPD."""
    audit_date: datetime
    overall_score: int
    overall_status: ComplianceStatus
    checks: list[RGPDAuditCheck]
    total_checks: int
    compliant_checks: int
    partial_checks: int
    non_compliant_checks: int
    critical_gaps: list[str]
    recommendations: list[str]
    next_steps: list[str]


class RGPDAuditService:
    """Service d'audit RGPD automatisé."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def run_full_audit(self) -> RGPDAuditResult:
        """
        Exécuter un audit RGPD complet.

        Vérifie tous les articles applicables et génère un rapport.
        """
        checks = []

        # Article 5 - Principes
        checks.append(self._check_article_5_principles())

        # Article 6 - Licéité
        checks.append(self._check_article_6_lawfulness())

        # Article 7 - Consentement
        checks.append(self._check_article_7_consent())

        # Articles 12-14 - Transparence et Information
        checks.append(self._check_articles_12_14_transparency())

        # Article 15 - Droit d'accès
        checks.append(self._check_article_15_access())

        # Article 17 - Droit à l'effacement
        checks.append(self._check_article_17_erasure())

        # Article 20 - Portabilité
        checks.append(self._check_article_20_portability())

        # Article 25 - Privacy by Design
        checks.append(self._check_article_25_by_design())

        # Article 30 - Registre des traitements
        checks.append(self._check_article_30_records())

        # Article 32 - Sécurité
        checks.append(self._check_article_32_security())

        # Article 33 - Notification des violations
        checks.append(self._check_article_33_breach_notification())

        # Article 35 - AIPD
        checks.append(self._check_article_35_dpia())

        # Article 37 - DPO
        checks.append(self._check_article_37_dpo())

        # Calcul des résultats
        compliant = sum(1 for c in checks if c.status == ComplianceStatus.COMPLIANT)
        partial = sum(1 for c in checks if c.status == ComplianceStatus.PARTIAL)
        non_compliant = sum(1 for c in checks if c.status == ComplianceStatus.NON_COMPLIANT)

        total_score = sum(c.score for c in checks)
        overall_score = total_score // len(checks) if checks else 0

        if overall_score >= 90:
            overall_status = ComplianceStatus.COMPLIANT
        elif overall_score >= 70:
            overall_status = ComplianceStatus.PARTIAL
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT

        # Identifier les écarts critiques
        critical_gaps = []
        for check in checks:
            if check.risk_level == RiskLevel.CRITICAL:
                critical_gaps.extend(check.findings)

        # Recommandations prioritaires
        recommendations = []
        for check in sorted(checks, key=lambda c: c.score):
            if check.score < 80:
                recommendations.extend(check.recommendations[:2])

        # Prochaines étapes
        next_steps = self._generate_next_steps(checks, overall_score)

        return RGPDAuditResult(
            audit_date=datetime.utcnow(),
            overall_score=overall_score,
            overall_status=overall_status,
            checks=checks,
            total_checks=len(checks),
            compliant_checks=compliant,
            partial_checks=partial,
            non_compliant_checks=non_compliant,
            critical_gaps=critical_gaps,
            recommendations=recommendations[:10],
            next_steps=next_steps
        )

    def _check_article_5_principles(self) -> RGPDAuditCheck:
        """Article 5 - Principes relatifs au traitement."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        # Vérifier la présence du registre des traitements
        from app.modules.country_packs.france.models import RGPDDataProcessing
        processings = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id
        ).count()

        if processings == 0:
            findings.append("Aucun traitement documenté dans le registre")
            recommendations.append("Documenter tous les traitements de données personnelles")
            score -= 30
        else:
            evidence.append(f"{processings} traitements documentés")

        # Vérifier les finalités
        processings_without_purpose = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id,
            RGPDDataProcessing.purposes == None
        ).count()

        if processings_without_purpose > 0:
            findings.append(f"{processings_without_purpose} traitements sans finalité documentée")
            recommendations.append("Documenter les finalités de chaque traitement")
            score -= 20

        # Vérifier les durées de conservation
        processings_without_retention = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id,
            RGPDDataProcessing.retention_period == None
        ).count()

        if processings_without_retention > 0:
            findings.append(f"{processings_without_retention} traitements sans durée de conservation")
            recommendations.append("Définir les durées de conservation pour chaque traitement")
            score -= 15

        status = self._score_to_status(score)
        risk_level = RiskLevel.CRITICAL if score < 50 else (RiskLevel.HIGH if score < 70 else RiskLevel.MEDIUM)

        return RGPDAuditCheck(
            article=RGPDArticle.ART_5_PRINCIPLES,
            title="Principes relatifs au traitement",
            description="Licéité, loyauté, transparence, limitation des finalités, minimisation, exactitude, conservation limitée, intégrité et confidentialité",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_6_lawfulness(self) -> RGPDAuditCheck:
        """Article 6 - Licéité du traitement."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        from app.modules.country_packs.france.models import RGPDDataProcessing

        # Vérifier que chaque traitement a une base légale
        processings = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id
        ).all()

        without_legal_basis = 0
        for p in processings:
            if not p.legal_basis:
                without_legal_basis += 1

        if without_legal_basis > 0:
            findings.append(f"{without_legal_basis} traitements sans base légale documentée")
            recommendations.append("Définir la base légale (consentement, contrat, obligation légale, intérêts vitaux, mission publique, intérêts légitimes)")
            score -= 30

        if processings:
            evidence.append(f"{len(processings) - without_legal_basis}/{len(processings)} traitements avec base légale")

        status = self._score_to_status(score)
        risk_level = RiskLevel.CRITICAL if score < 50 else RiskLevel.HIGH if score < 70 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_6_LAWFULNESS,
            title="Licéité du traitement",
            description="Chaque traitement doit reposer sur une base légale valide",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_7_consent(self) -> RGPDAuditCheck:
        """Article 7 - Conditions applicables au consentement."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        from app.modules.country_packs.france.models import RGPDConsent, RGPDConsentStatus

        # Vérifier les consentements actifs
        active_consents = self.db.query(RGPDConsent).filter(
            RGPDConsent.tenant_id == self.tenant_id,
            RGPDConsent.status == RGPDConsentStatus.GRANTED
        ).count()

        total_consents = self.db.query(RGPDConsent).filter(
            RGPDConsent.tenant_id == self.tenant_id
        ).count()

        if total_consents > 0:
            evidence.append(f"{active_consents} consentements actifs sur {total_consents} total")

        # Vérifier les preuves de consentement
        without_proof = self.db.query(RGPDConsent).filter(
            RGPDConsent.tenant_id == self.tenant_id,
            RGPDConsent.consent_proof == None
        ).count()

        if without_proof > 0:
            findings.append(f"{without_proof} consentements sans preuve documentée")
            recommendations.append("Conserver une preuve du consentement (date, méthode, version)")
            score -= 20

        # Vérifier les consentements expirés non renouvelés
        expired = self.db.query(RGPDConsent).filter(
            RGPDConsent.tenant_id == self.tenant_id,
            RGPDConsent.valid_until < date.today(),
            RGPDConsent.status == RGPDConsentStatus.GRANTED
        ).count()

        if expired > 0:
            findings.append(f"{expired} consentements expirés non révoqués")
            recommendations.append("Mettre en place un processus de renouvellement des consentements")
            score -= 15

        status = self._score_to_status(score)
        risk_level = RiskLevel.HIGH if score < 70 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_7_CONSENT,
            title="Conditions applicables au consentement",
            description="Le consentement doit être libre, spécifique, éclairé et univoque",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_articles_12_14_transparency(self) -> RGPDAuditCheck:
        """Articles 12-14 - Transparence et Information."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        # Vérifier l'existence de politiques de confidentialité
        from .models import Policy, DocumentType
        privacy_policies = self.db.query(Policy).filter(
            Policy.tenant_id == self.tenant_id,
            Policy.type == DocumentType.POLICY,
            Policy.category == "privacy",
            Policy.is_active == True
        ).count()

        if privacy_policies == 0:
            findings.append("Aucune politique de confidentialité active")
            recommendations.append("Rédiger et publier une politique de confidentialité conforme")
            score -= 40
        else:
            evidence.append(f"{privacy_policies} politique(s) de confidentialité")

        status = self._score_to_status(score)
        risk_level = RiskLevel.HIGH if score < 70 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_12_TRANSPARENCY,
            title="Transparence et Information",
            description="Informations claires sur le traitement des données",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_15_access(self) -> RGPDAuditCheck:
        """Article 15 - Droit d'accès."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        from app.modules.country_packs.france.models import RGPDRequest, RGPDRequestType

        # Vérifier les demandes d'accès traitées
        access_requests = self.db.query(RGPDRequest).filter(
            RGPDRequest.tenant_id == self.tenant_id,
            RGPDRequest.request_type == RGPDRequestType.ACCESS
        ).all()

        total = len(access_requests)
        completed = sum(1 for r in access_requests if r.status == "completed")
        overdue = sum(1 for r in access_requests if r.due_date < date.today() and r.status not in ["completed", "rejected"])

        if total > 0:
            evidence.append(f"{completed}/{total} demandes d'accès traitées")

        if overdue > 0:
            findings.append(f"{overdue} demandes d'accès en retard")
            recommendations.append("Traiter les demandes d'accès dans le délai légal (1 mois)")
            score -= 25

        status = self._score_to_status(score)
        risk_level = RiskLevel.HIGH if overdue > 0 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_15_ACCESS,
            title="Droit d'accès",
            description="Répondre aux demandes d'accès dans le délai légal",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_17_erasure(self) -> RGPDAuditCheck:
        """Article 17 - Droit à l'effacement."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        from app.modules.country_packs.france.models import RGPDRequest, RGPDRequestType

        erasure_requests = self.db.query(RGPDRequest).filter(
            RGPDRequest.tenant_id == self.tenant_id,
            RGPDRequest.request_type == RGPDRequestType.ERASURE
        ).all()

        total = len(erasure_requests)
        completed = sum(1 for r in erasure_requests if r.status == "completed")
        overdue = sum(1 for r in erasure_requests if r.due_date < date.today() and r.status not in ["completed", "rejected"])

        if total > 0:
            evidence.append(f"{completed}/{total} demandes d'effacement traitées")

        if overdue > 0:
            findings.append(f"{overdue} demandes d'effacement en retard")
            recommendations.append("Mettre en place un processus d'effacement efficace")
            score -= 30

        status = self._score_to_status(score)
        risk_level = RiskLevel.HIGH if overdue > 0 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_17_ERASURE,
            title="Droit à l'effacement",
            description="Répondre aux demandes d'effacement dans le délai légal",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_20_portability(self) -> RGPDAuditCheck:
        """Article 20 - Droit à la portabilité."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        from app.modules.country_packs.france.models import RGPDRequest, RGPDRequestType

        portability_requests = self.db.query(RGPDRequest).filter(
            RGPDRequest.tenant_id == self.tenant_id,
            RGPDRequest.request_type == RGPDRequestType.PORTABILITY
        ).all()

        total = len(portability_requests)
        completed = sum(1 for r in portability_requests if r.status == "completed" and r.data_exported)

        if total > 0:
            evidence.append(f"{completed}/{total} demandes de portabilité avec export")

        # Vérifier si un format d'export standard existe
        # (vérification basique - à améliorer selon l'implémentation)
        if total > 0 and completed < total:
            findings.append("Certaines demandes de portabilité sans export de données")
            recommendations.append("Implémenter un export au format structuré (JSON, CSV)")
            score -= 20

        status = self._score_to_status(score)
        risk_level = RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_20_PORTABILITY,
            title="Droit à la portabilité",
            description="Fournir les données dans un format structuré et lisible",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_25_by_design(self) -> RGPDAuditCheck:
        """Article 25 - Privacy by Design et by Default."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        # Vérification de base - à adapter selon l'implémentation
        # Vérifier les paramètres de configuration de protection des données
        from app.modules.country_packs.france.models import RGPDDataProcessing

        processings_with_security = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id,
            RGPDDataProcessing.security_measures != None
        ).count()

        total_processings = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id
        ).count()

        if total_processings > 0:
            if processings_with_security < total_processings:
                findings.append(f"{total_processings - processings_with_security} traitements sans mesures de sécurité documentées")
                recommendations.append("Documenter les mesures de protection par défaut pour chaque traitement")
                score -= 25
            else:
                evidence.append("Mesures de sécurité documentées pour tous les traitements")

        status = self._score_to_status(score)
        risk_level = RiskLevel.HIGH if score < 70 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_25_BY_DESIGN,
            title="Protection dès la conception et par défaut",
            description="Mesures techniques et organisationnelles appropriées",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_30_records(self) -> RGPDAuditCheck:
        """Article 30 - Registre des activités de traitement."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        from app.modules.country_packs.france.models import RGPDDataProcessing

        processings = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id
        ).all()

        if len(processings) == 0:
            findings.append("Registre des traitements vide ou inexistant")
            recommendations.append("Créer et maintenir un registre des activités de traitement")
            score -= 50
        else:
            evidence.append(f"{len(processings)} traitements dans le registre")

            # Vérifier les champs obligatoires
            incomplete = 0
            for p in processings:
                if not all([p.processing_name, p.purposes, p.data_categories, p.recipients]):
                    incomplete += 1

            if incomplete > 0:
                findings.append(f"{incomplete} traitements avec informations incomplètes")
                recommendations.append("Compléter les informations obligatoires (finalités, catégories, destinataires)")
                score -= 20

        status = self._score_to_status(score)
        risk_level = RiskLevel.CRITICAL if len(processings) == 0 else RiskLevel.HIGH if score < 70 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_30_RECORDS,
            title="Registre des activités de traitement",
            description="Tenue d'un registre conforme Article 30",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_32_security(self) -> RGPDAuditCheck:
        """Article 32 - Sécurité du traitement."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        # Vérifier les mesures de sécurité documentées
        from app.modules.country_packs.france.models import RGPDDataProcessing

        processings = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id
        ).all()

        without_security = sum(1 for p in processings if not p.security_measures)

        if without_security > 0:
            findings.append(f"{without_security} traitements sans mesures de sécurité documentées")
            recommendations.append("Documenter les mesures de sécurité: chiffrement, pseudonymisation, contrôle d'accès")
            score -= 30

        # Vérifier les violations de données
        from app.modules.country_packs.france.models import RGPDDataBreach

        open_breaches = self.db.query(RGPDDataBreach).filter(
            RGPDDataBreach.tenant_id == self.tenant_id,
            RGPDDataBreach.status.in_(["detected", "investigating"])
        ).count()

        if open_breaches > 0:
            findings.append(f"{open_breaches} violations de données non résolues")
            recommendations.append("Résoudre les violations de données en cours")
            score -= 20

        status = self._score_to_status(score)
        risk_level = RiskLevel.CRITICAL if open_breaches > 0 else RiskLevel.HIGH if score < 70 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_32_SECURITY,
            title="Sécurité du traitement",
            description="Mesures techniques et organisationnelles appropriées",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_33_breach_notification(self) -> RGPDAuditCheck:
        """Article 33 - Notification des violations à l'autorité de contrôle."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        from app.modules.country_packs.france.models import RGPDDataBreach

        breaches = self.db.query(RGPDDataBreach).filter(
            RGPDDataBreach.tenant_id == self.tenant_id
        ).all()

        # Vérifier les violations nécessitant notification CNIL
        requiring_notification = [b for b in breaches if b.cnil_notification_required]
        notified = [b for b in requiring_notification if b.cnil_notified_at]

        if requiring_notification:
            evidence.append(f"{len(notified)}/{len(requiring_notification)} violations notifiées à la CNIL")

            not_notified = len(requiring_notification) - len(notified)
            if not_notified > 0:
                findings.append(f"{not_notified} violations non notifiées à la CNIL")
                recommendations.append("Notifier la CNIL dans les 72h suivant la détection")
                score -= 40

            # Vérifier le délai de 72h
            for b in requiring_notification:
                if b.cnil_notified_at and b.detected_at:
                    delay = (b.cnil_notified_at - b.detected_at).total_seconds() / 3600
                    if delay > 72:
                        findings.append(f"Violation {b.breach_code} notifiée après {int(delay)}h (>72h)")
                        score -= 10

        status = self._score_to_status(score)
        risk_level = RiskLevel.CRITICAL if score < 60 else RiskLevel.HIGH if score < 80 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_33_BREACH_NOTIFICATION,
            title="Notification des violations à la CNIL",
            description="Notification dans les 72h en cas de risque",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_35_dpia(self) -> RGPDAuditCheck:
        """Article 35 - Analyse d'impact relative à la protection des données."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        # Vérifier les traitements à risque
        from app.modules.country_packs.france.models import RGPDDataProcessing

        # Traitements potentiellement à risque (données sensibles, profilage, grande échelle)
        high_risk = self.db.query(RGPDDataProcessing).filter(
            RGPDDataProcessing.tenant_id == self.tenant_id,
            RGPDDataProcessing.special_categories != None
        ).count()

        if high_risk > 0:
            findings.append(f"{high_risk} traitements avec données sensibles - AIPD potentiellement requise")
            recommendations.append("Réaliser une Analyse d'Impact (AIPD) pour les traitements à risque")
            score -= 25

        status = self._score_to_status(score)
        risk_level = RiskLevel.HIGH if high_risk > 0 else RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_35_DPIA,
            title="Analyse d'impact (AIPD)",
            description="AIPD requise pour les traitements à risque élevé",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _check_article_37_dpo(self) -> RGPDAuditCheck:
        """Article 37 - Désignation du DPO."""
        findings = []
        recommendations = []
        evidence = []
        score = 100

        # Vérifier la désignation du DPO
        # (vérification basique - à adapter selon l'implémentation)
        from .models import ComplianceDocument, DocumentType

        dpo_docs = self.db.query(ComplianceDocument).filter(
            ComplianceDocument.tenant_id == self.tenant_id,
            ComplianceDocument.type == DocumentType.CERTIFICATE,
            ComplianceDocument.category == "dpo",
            ComplianceDocument.is_active == True
        ).count()

        if dpo_docs == 0:
            findings.append("Aucune désignation de DPO documentée")
            recommendations.append("Désigner un DPO si obligatoire (organisme public, traitement à grande échelle, données sensibles)")
            score -= 20

        status = self._score_to_status(score)
        risk_level = RiskLevel.MEDIUM

        return RGPDAuditCheck(
            article=RGPDArticle.ART_37_DPO,
            title="Délégué à la protection des données",
            description="Désignation d'un DPO si requis",
            status=status,
            score=max(0, score),
            findings=findings,
            recommendations=recommendations,
            evidence=evidence,
            risk_level=risk_level
        )

    def _score_to_status(self, score: int) -> ComplianceStatus:
        """Convertir un score en statut de conformité."""
        if score >= 90:
            return ComplianceStatus.COMPLIANT
        elif score >= 70:
            return ComplianceStatus.PARTIAL
        else:
            return ComplianceStatus.NON_COMPLIANT

    def _generate_next_steps(self, checks: list[RGPDAuditCheck], overall_score: int) -> list[str]:
        """Générer les prochaines étapes recommandées."""
        next_steps = []

        # Étapes critiques
        critical_checks = [c for c in checks if c.risk_level == RiskLevel.CRITICAL]
        if critical_checks:
            next_steps.append("URGENT: Traiter les écarts critiques identifiés")

        # Score global
        if overall_score < 70:
            next_steps.append("Mettre en place un plan d'action de mise en conformité")
            next_steps.append("Désigner un responsable conformité RGPD")

        if overall_score < 90:
            next_steps.append("Planifier un audit de suivi dans 3 mois")

        # Vérifier le registre
        art30 = next((c for c in checks if c.article == RGPDArticle.ART_30_RECORDS), None)
        if art30 and art30.status != ComplianceStatus.COMPLIANT:
            next_steps.append("Mettre à jour le registre des traitements")

        # Vérifier les violations
        art33 = next((c for c in checks if c.article == RGPDArticle.ART_33_BREACH_NOTIFICATION), None)
        if art33 and art33.status != ComplianceStatus.COMPLIANT:
            next_steps.append("Revoir la procédure de gestion des violations de données")

        return next_steps[:5]

    def save_audit_result(self, result: RGPDAuditResult) -> ComplianceAssessment:
        """Sauvegarder le résultat de l'audit dans la base."""
        import uuid

        # Créer ou récupérer la réglementation RGPD
        rgpd_regulation = self.db.query(Regulation).filter(
            Regulation.tenant_id == self.tenant_id,
            Regulation.type == RegulationType.GDPR
        ).first()

        if not rgpd_regulation:
            rgpd_regulation = Regulation(
                tenant_id=self.tenant_id,
                code="RGPD",
                name="Règlement Général sur la Protection des Données",
                type=RegulationType.GDPR,
                authority="Commission Européenne / CNIL",
                is_mandatory=True
            )
            self.db.add(rgpd_regulation)
            self.db.flush()

        # Créer l'assessment
        assessment_number = f"RGPD-AUDIT-{datetime.utcnow().strftime('%Y%m%d-%H%M')}"
        assessment = ComplianceAssessment(
            tenant_id=self.tenant_id,
            number=assessment_number,
            name=f"Audit RGPD - {result.audit_date.strftime('%d/%m/%Y')}",
            regulation_id=rgpd_regulation.id,
            assessment_type="Full",
            status=AssessmentStatus.COMPLETED,
            overall_score=Decimal(str(result.overall_score)),
            overall_status=result.overall_status,
            total_requirements=result.total_checks,
            compliant_count=result.compliant_checks,
            non_compliant_count=result.non_compliant_checks,
            partial_count=result.partial_checks,
            findings_summary="\n".join(result.critical_gaps),
            recommendations="\n".join(result.recommendations),
            end_date=date.today()
        )
        self.db.add(assessment)
        self.db.flush()

        # Créer les gaps pour les écarts
        for check in result.checks:
            if check.status != ComplianceStatus.COMPLIANT:
                # Créer ou récupérer l'exigence
                requirement = self.db.query(Requirement).filter(
                    Requirement.tenant_id == self.tenant_id,
                    Requirement.code == check.article.value
                ).first()

                if not requirement:
                    requirement = Requirement(
                        tenant_id=self.tenant_id,
                        regulation_id=rgpd_regulation.id,
                        code=check.article.value,
                        name=check.title,
                        description=check.description,
                        compliance_status=check.status,
                        current_score=Decimal(str(check.score))
                    )
                    self.db.add(requirement)
                    self.db.flush()

                # Créer le gap
                gap = ComplianceGap(
                    tenant_id=self.tenant_id,
                    assessment_id=assessment.id,
                    requirement_id=requirement.id,
                    gap_description="\n".join(check.findings),
                    severity=check.risk_level,
                    current_status=check.status
                )
                self.db.add(gap)

        self.db.commit()
        self.db.refresh(assessment)
        return assessment
