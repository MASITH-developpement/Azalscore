"""
AZALS MODULE - Marceau Comptabilite Service
============================================

Service de comptabilite automatisee pour le module Marceau.
Integre le module accounting AZALSCORE avec intelligence LLM.

Actions:
    - process_invoice: Traitement facture fournisseur avec imputation automatique
    - reconcile_bank: Rapprochement bancaire automatique
    - post_entry: Creation ecriture comptable
    - generate_report: Generation rapports comptables
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.marceau.llm_client import get_llm_client_for_tenant, extract_json_from_response
from app.modules.marceau.models import MarceauAction, ActionStatus

logger = logging.getLogger(__name__)


class ComptabiliteService:
    """
    Service de comptabilite automatisee.
    Utilise l'intelligence LLM pour l'imputation et la categorisation.
    """

    # Mapping des classes PCG pour l'analyse LLM
    PCG_CLASSES = {
        "1": "Capitaux",
        "2": "Immobilisations",
        "3": "Stocks",
        "4": "Tiers (clients, fournisseurs)",
        "5": "Tresorerie",
        "6": "Charges",
        "7": "Produits",
        "8": "Comptes speciaux",
    }

    # Comptes fournisseurs courants
    DEFAULT_ACCOUNTS = {
        "fournisseur": "401000",
        "tva_deductible": "445660",
        "achats_marchandises": "607000",
        "achats_services": "604000",
        "banque": "512000",
        "caisse": "530000",
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
        """
        Execute une action comptabilite.

        Args:
            action: Nom de l'action
            data: Donnees de l'action
            context: Historique conversation

        Returns:
            Resultat de l'action
        """
        action_handlers = {
            "process_invoice": self._process_invoice,
            "reconcile_bank": self._reconcile_bank,
            "post_entry": self._post_entry,
            "generate_report": self._generate_report,
        }

        handler = action_handlers.get(action, self._unknown_action)
        return await handler(data, context)

    # ========================================================================
    # PROCESS INVOICE - Traitement facture fournisseur
    # ========================================================================

    async def _process_invoice(self, data: dict, context: list[str]) -> dict:
        """
        Traite une facture fournisseur avec suggestion d'imputation.

        Etapes:
        1. Analyse du contenu facture via LLM
        2. Suggestion comptes d'imputation
        3. Creation ecriture comptable (DRAFT)
        4. Demande validation humaine

        Args:
            data: {
                "supplier_name": "Nom fournisseur",
                "invoice_number": "FA-2024-001",
                "invoice_date": "2024-01-15",
                "amount_ht": 1000.00,
                "amount_tva": 200.00,
                "amount_ttc": 1200.00,
                "description": "Achat materiel informatique",
                "document_path": "/path/to/invoice.pdf"  # optionnel
            }
        """
        logger.info(f"[Comptabilite] Traitement facture: {data.get('invoice_number')}")

        # Validation donnees obligatoires
        required = ["supplier_name", "invoice_number", "amount_ttc"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return {
                "success": False,
                "error": f"Champs manquants: {', '.join(missing)}",
                "action": "process_invoice",
            }

        try:
            # Extraire les montants
            amount_ht = Decimal(str(data.get("amount_ht", 0)))
            amount_tva = Decimal(str(data.get("amount_tva", 0)))
            amount_ttc = Decimal(str(data.get("amount_ttc", 0)))

            # Si HT/TVA manquants, calculer a partir de TTC (TVA 20%)
            if not amount_ht and amount_ttc:
                amount_ht = amount_ttc / Decimal("1.20")
                amount_tva = amount_ttc - amount_ht

            # Suggerer l'imputation via LLM
            imputation = await self._suggest_imputation(data)

            # Recuperer l'exercice actif
            from app.modules.accounting.service import AccountingService
            accounting = AccountingService(self.db, self.tenant_id)
            fiscal_year = accounting.get_active_fiscal_year()

            if not fiscal_year:
                return {
                    "success": False,
                    "error": "Aucun exercice comptable actif",
                    "action": "process_invoice",
                }

            # Preparer les lignes d'ecriture
            lines = [
                {
                    "account_number": imputation.get("charge_account", self.DEFAULT_ACCOUNTS["achats_services"]),
                    "account_label": imputation.get("charge_label", "Achats"),
                    "debit": float(amount_ht),
                    "credit": 0,
                    "label": data.get("description", ""),
                },
                {
                    "account_number": self.DEFAULT_ACCOUNTS["tva_deductible"],
                    "account_label": "TVA deductible",
                    "debit": float(amount_tva),
                    "credit": 0,
                    "label": "TVA deductible",
                },
                {
                    "account_number": self.DEFAULT_ACCOUNTS["fournisseur"],
                    "account_label": f"Fournisseur {data.get('supplier_name')}",
                    "debit": 0,
                    "credit": float(amount_ttc),
                    "label": f"Facture {data.get('invoice_number')}",
                    "auxiliary_code": data.get("supplier_code"),
                },
            ]

            # Creer l'action Marceau pour validation
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="comptabilite",
                action_type="process_invoice",
                status=ActionStatus.NEEDS_VALIDATION,
                input_data={
                    "invoice": data,
                    "imputation": imputation,
                },
                output_data={
                    "fiscal_year_id": str(fiscal_year.id),
                    "entry_lines": lines,
                    "amount_ht": float(amount_ht),
                    "amount_tva": float(amount_tva),
                    "amount_ttc": float(amount_ttc),
                },
                reasoning=imputation.get("reasoning", ""),
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "process_invoice",
                "action_id": str(action_record.id),
                "status": "needs_validation",
                "message": f"Facture {data.get('invoice_number')} analysee. Imputation suggeree: {imputation.get('charge_account')} - {imputation.get('charge_label')}",
                "imputation": imputation,
                "entry_preview": {
                    "journal": "AC",
                    "date": data.get("invoice_date", datetime.now().strftime("%Y-%m-%d")),
                    "label": f"Facture {data.get('supplier_name')} - {data.get('invoice_number')}",
                    "lines": lines,
                },
                "requires_validation": True,
            }

        except Exception as e:
            logger.error(f"[Comptabilite] Erreur traitement facture: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "process_invoice",
            }

    async def _suggest_imputation(self, invoice_data: dict) -> dict:
        """
        Utilise le LLM pour suggerer l'imputation comptable.
        """
        llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

        prompt = f"""Analyse cette facture fournisseur et suggere l'imputation comptable PCG:

Fournisseur: {invoice_data.get('supplier_name')}
Description: {invoice_data.get('description', 'Non specifiee')}
Montant TTC: {invoice_data.get('amount_ttc')} EUR

Classes PCG disponibles:
- Classe 6: Charges (achats, services, personnel, impots, charges financieres, charges exceptionnelles)
- Sous-classes courantes:
  - 601000-602000: Achats stockes (matieres premieres, fournitures)
  - 604000-605000: Achats etudes et prestations
  - 606000-607000: Achats non stockes (fournitures, marchandises)
  - 611000-618000: Sous-traitance et services exterieurs
  - 621000-628000: Autres services exterieurs

Reponds en JSON avec:
{{
    "charge_account": "60XXXX",
    "charge_label": "Libelle du compte",
    "confidence": 0.8,
    "reasoning": "Explication courte du choix"
}}"""

        try:
            response = await llm.generate(
                prompt,
                temperature=0.1,
                max_tokens=500,
                system_prompt="Tu es un expert-comptable. Reponds uniquement en JSON valide.",
            )

            result = await extract_json_from_response(response)
            if result:
                return result

            # Fallback si parsing echoue
            return {
                "charge_account": self.DEFAULT_ACCOUNTS["achats_services"],
                "charge_label": "Autres achats et charges externes",
                "confidence": 0.5,
                "reasoning": "Imputation par defaut (analyse LLM non disponible)",
            }

        except Exception as e:
            logger.warning(f"[Comptabilite] Erreur suggestion LLM: {e}")
            return {
                "charge_account": self.DEFAULT_ACCOUNTS["achats_services"],
                "charge_label": "Autres achats et charges externes",
                "confidence": 0.5,
                "reasoning": f"Imputation par defaut (erreur: {str(e)[:50]})",
            }

    # ========================================================================
    # RECONCILE BANK - Rapprochement bancaire
    # ========================================================================

    async def _reconcile_bank(self, data: dict, context: list[str]) -> dict:
        """
        Effectue le rapprochement bancaire automatique.

        Etapes:
        1. Recupere les mouvements bancaires non rapproches
        2. Recupere les ecritures comptables du compte banque
        3. Propose les correspondances via algorithme de matching
        4. Demande validation humaine

        Args:
            data: {
                "bank_account": "512000",  # Compte banque
                "period_start": "2024-01-01",
                "period_end": "2024-01-31",
                "bank_movements": [  # Mouvements du releve bancaire
                    {"date": "2024-01-05", "label": "VIR Client X", "amount": 1200.00},
                    {"date": "2024-01-10", "label": "PRLV Loyer", "amount": -800.00},
                ]
            }
        """
        logger.info(f"[Comptabilite] Rapprochement bancaire: {data.get('bank_account')}")

        bank_account = data.get("bank_account", self.DEFAULT_ACCOUNTS["banque"])
        bank_movements = data.get("bank_movements", [])

        if not bank_movements:
            return {
                "success": False,
                "error": "Aucun mouvement bancaire fourni",
                "action": "reconcile_bank",
            }

        try:
            from app.modules.accounting.service import AccountingService
            from app.modules.accounting.models import (
                AccountingJournalEntry,
                AccountingJournalEntryLine,
                EntryStatus,
            )

            accounting = AccountingService(self.db, self.tenant_id)

            # Recuperer les ecritures du compte banque
            period_start = data.get("period_start")
            period_end = data.get("period_end")

            query = self.db.query(AccountingJournalEntryLine).join(
                AccountingJournalEntry,
                AccountingJournalEntryLine.entry_id == AccountingJournalEntry.id,
            ).filter(
                AccountingJournalEntryLine.tenant_id == self.tenant_id,
                AccountingJournalEntryLine.account_number == bank_account,
                AccountingJournalEntry.status.in_([EntryStatus.POSTED, EntryStatus.VALIDATED]),
            )

            if period_start:
                query = query.filter(AccountingJournalEntry.entry_date >= period_start)
            if period_end:
                query = query.filter(AccountingJournalEntry.entry_date <= period_end)

            entry_lines = query.all()

            # Construire liste des ecritures non rapprochees
            unreconciled_entries = []
            for line in entry_lines:
                amount = float(line.debit) - float(line.credit)
                unreconciled_entries.append({
                    "line_id": str(line.id),
                    "entry_id": str(line.entry_id),
                    "date": line.entry.entry_date.strftime("%Y-%m-%d") if line.entry else "",
                    "label": line.label or line.entry.label if line.entry else "",
                    "amount": amount,
                })

            # Proposer les correspondances
            matches = await self._match_bank_movements(bank_movements, unreconciled_entries)

            # Calculer les statistiques
            matched_count = len([m for m in matches if m.get("match_found")])
            total_movements = len(bank_movements)

            # Creer l'action pour validation
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="comptabilite",
                action_type="reconcile_bank",
                status=ActionStatus.NEEDS_VALIDATION,
                input_data={
                    "bank_account": bank_account,
                    "period_start": period_start,
                    "period_end": period_end,
                    "movements_count": total_movements,
                },
                output_data={
                    "matches": matches,
                    "matched_count": matched_count,
                    "unmatched_count": total_movements - matched_count,
                },
                reasoning=f"Rapprochement: {matched_count}/{total_movements} mouvements matches",
            )
            self.db.add(action_record)
            self.db.commit()
            self.db.refresh(action_record)

            return {
                "success": True,
                "action": "reconcile_bank",
                "action_id": str(action_record.id),
                "status": "needs_validation",
                "message": f"Rapprochement propose: {matched_count}/{total_movements} correspondances trouvees",
                "statistics": {
                    "total_movements": total_movements,
                    "matched": matched_count,
                    "unmatched": total_movements - matched_count,
                    "match_rate": round(matched_count / total_movements * 100, 1) if total_movements > 0 else 0,
                },
                "matches": matches,
                "requires_validation": True,
            }

        except Exception as e:
            logger.error(f"[Comptabilite] Erreur rapprochement: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "reconcile_bank",
            }

    async def _match_bank_movements(
        self,
        bank_movements: list[dict],
        entries: list[dict],
    ) -> list[dict]:
        """
        Algorithme de matching mouvement bancaire <-> ecriture comptable.
        Criteres: montant exact + proximite de date + similarite libelle
        """
        matches = []

        for movement in bank_movements:
            mvt_amount = float(movement.get("amount", 0))
            mvt_date = movement.get("date", "")
            mvt_label = movement.get("label", "").lower()

            best_match = None
            best_score = 0

            for entry in entries:
                # Verifier montant exact
                if abs(float(entry.get("amount", 0)) - mvt_amount) > 0.01:
                    continue

                score = 50  # Base score pour montant exact

                # Bonus proximite de date
                try:
                    mvt_dt = datetime.strptime(mvt_date, "%Y-%m-%d")
                    entry_dt = datetime.strptime(entry.get("date", ""), "%Y-%m-%d")
                    days_diff = abs((mvt_dt - entry_dt).days)
                    if days_diff == 0:
                        score += 30
                    elif days_diff <= 3:
                        score += 20
                    elif days_diff <= 7:
                        score += 10
                except (ValueError, TypeError):
                    pass

                # Bonus similarite libelle
                entry_label = entry.get("label", "").lower()
                common_words = set(mvt_label.split()) & set(entry_label.split())
                if common_words:
                    score += min(len(common_words) * 5, 20)

                if score > best_score:
                    best_score = score
                    best_match = entry

            matches.append({
                "movement": movement,
                "match_found": best_match is not None,
                "matched_entry": best_match,
                "confidence_score": best_score,
            })

        return matches

    # ========================================================================
    # POST ENTRY - Comptabilisation
    # ========================================================================

    async def _post_entry(self, data: dict, context: list[str]) -> dict:
        """
        Cree et comptabilise une ecriture.

        Args:
            data: {
                "journal_code": "VT",  # VT=Ventes, AC=Achats, BQ=Banque, OD=Operations diverses
                "entry_date": "2024-01-15",
                "label": "Vente client X",
                "lines": [
                    {"account": "411000", "label": "Client X", "debit": 1200, "credit": 0},
                    {"account": "701000", "label": "Ventes produits", "debit": 0, "credit": 1000},
                    {"account": "445710", "label": "TVA collectee", "debit": 0, "credit": 200},
                ],
                "auto_post": false  # Si true, comptabilise directement
            }
        """
        logger.info(f"[Comptabilite] Creation ecriture: {data.get('journal_code')}")

        required = ["journal_code", "entry_date", "label", "lines"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return {
                "success": False,
                "error": f"Champs manquants: {', '.join(missing)}",
                "action": "post_entry",
            }

        lines = data.get("lines", [])
        if len(lines) < 2:
            return {
                "success": False,
                "error": "Une ecriture doit avoir au moins 2 lignes",
                "action": "post_entry",
            }

        # Verifier l'equilibre
        total_debit = sum(float(l.get("debit", 0)) for l in lines)
        total_credit = sum(float(l.get("credit", 0)) for l in lines)

        if abs(total_debit - total_credit) > 0.01:
            return {
                "success": False,
                "error": f"Ecriture desequilibree: debit={total_debit}, credit={total_credit}",
                "action": "post_entry",
            }

        try:
            from app.modules.accounting.service import AccountingService
            from app.modules.accounting.schemas import JournalEntryCreate, JournalEntryLineCreate

            accounting = AccountingService(self.db, self.tenant_id)
            fiscal_year = accounting.get_active_fiscal_year()

            if not fiscal_year:
                return {
                    "success": False,
                    "error": "Aucun exercice comptable actif",
                    "action": "post_entry",
                }

            # Construire les lignes
            entry_lines = []
            for line in lines:
                entry_lines.append(JournalEntryLineCreate(
                    account_number=line.get("account"),
                    account_label=line.get("label", ""),
                    label=line.get("line_label"),
                    debit=Decimal(str(line.get("debit", 0))),
                    credit=Decimal(str(line.get("credit", 0))),
                    analytics_code=line.get("analytics_code"),
                    auxiliary_code=line.get("auxiliary_code"),
                ))

            # Creer l'ecriture
            entry_date = datetime.strptime(data.get("entry_date"), "%Y-%m-%d")
            entry_data = JournalEntryCreate(
                fiscal_year_id=fiscal_year.id,
                piece_number=data.get("piece_number", f"MRC-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                journal_code=data.get("journal_code"),
                journal_label=self._get_journal_label(data.get("journal_code")),
                entry_date=entry_date,
                label=data.get("label"),
                document_type=data.get("document_type"),
                document_id=UUID(data.get("document_id")) if data.get("document_id") else None,
                lines=entry_lines,
            )

            # Creer l'ecriture (DRAFT par defaut)
            entry = accounting.create_journal_entry(entry_data, user_id=None)

            # Comptabiliser si demande
            if data.get("auto_post"):
                entry = accounting.post_journal_entry(entry.id, user_id=None)

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="comptabilite",
                action_type="post_entry",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={
                    "entry_id": str(entry.id),
                    "entry_number": entry.entry_number,
                    "status": entry.status.value,
                    "total_debit": float(entry.total_debit),
                    "total_credit": float(entry.total_credit),
                },
                reasoning=f"Ecriture {entry.entry_number} creee",
            )
            self.db.add(action_record)
            self.db.commit()

            return {
                "success": True,
                "action": "post_entry",
                "action_id": str(action_record.id),
                "entry_id": str(entry.id),
                "entry_number": entry.entry_number,
                "status": entry.status.value,
                "message": f"Ecriture {entry.entry_number} creee ({entry.status.value})",
                "totals": {
                    "debit": float(entry.total_debit),
                    "credit": float(entry.total_credit),
                },
            }

        except Exception as e:
            logger.error(f"[Comptabilite] Erreur creation ecriture: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "post_entry",
            }

    def _get_journal_label(self, code: str) -> str:
        """Retourne le libelle du journal."""
        labels = {
            "VT": "Journal des ventes",
            "AC": "Journal des achats",
            "BQ": "Journal de banque",
            "CA": "Journal de caisse",
            "OD": "Operations diverses",
            "AN": "A nouveaux",
        }
        return labels.get(code, f"Journal {code}")

    # ========================================================================
    # GENERATE REPORT - Generation rapports
    # ========================================================================

    async def _generate_report(self, data: dict, context: list[str]) -> dict:
        """
        Genere un rapport comptable.

        Args:
            data: {
                "report_type": "balance" | "ledger" | "income_statement" | "balance_sheet",
                "fiscal_year_id": "uuid",  # optionnel, utilise l'actif par defaut
                "period": "2024-01",  # optionnel
                "format": "json" | "pdf" | "excel",  # json par defaut
            }
        """
        report_type = data.get("report_type", "balance")
        logger.info(f"[Comptabilite] Generation rapport: {report_type}")

        valid_types = ["balance", "ledger", "income_statement", "balance_sheet", "summary"]
        if report_type not in valid_types:
            return {
                "success": False,
                "error": f"Type de rapport invalide. Types valides: {', '.join(valid_types)}",
                "action": "generate_report",
            }

        try:
            from app.modules.accounting.service import AccountingService

            accounting = AccountingService(self.db, self.tenant_id)

            # Recuperer l'exercice
            fiscal_year_id = data.get("fiscal_year_id")
            if fiscal_year_id:
                fiscal_year_id = UUID(fiscal_year_id)
            else:
                fiscal_year = accounting.get_active_fiscal_year()
                fiscal_year_id = fiscal_year.id if fiscal_year else None

            period = data.get("period")
            report_data = {}

            if report_type == "balance":
                # Balance generale
                entries, total = accounting.get_balance(
                    fiscal_year_id=fiscal_year_id,
                    period=period,
                    per_page=1000,
                )
                report_data = {
                    "type": "balance",
                    "entries": [
                        {
                            "account_number": e.account_number,
                            "account_label": e.account_label,
                            "opening_debit": float(e.opening_debit),
                            "opening_credit": float(e.opening_credit),
                            "period_debit": float(e.period_debit),
                            "period_credit": float(e.period_credit),
                            "closing_debit": float(e.closing_debit),
                            "closing_credit": float(e.closing_credit),
                        }
                        for e in entries
                    ],
                    "total_entries": total,
                }

            elif report_type == "ledger":
                # Grand livre
                accounts, total = accounting.get_ledger(
                    fiscal_year_id=fiscal_year_id,
                    per_page=1000,
                )
                report_data = {
                    "type": "ledger",
                    "accounts": [
                        {
                            "account_number": a.account_number,
                            "account_label": a.account_label,
                            "debit_total": float(a.debit_total),
                            "credit_total": float(a.credit_total),
                            "balance": float(a.balance),
                        }
                        for a in accounts
                    ],
                    "total_accounts": total,
                }

            elif report_type in ["income_statement", "balance_sheet", "summary"]:
                # Resume comptable
                summary = accounting.get_summary(fiscal_year_id=fiscal_year_id)
                report_data = {
                    "type": report_type,
                    "total_assets": float(summary.total_assets),
                    "total_liabilities": float(summary.total_liabilities),
                    "total_equity": float(summary.total_equity),
                    "revenue": float(summary.revenue),
                    "expenses": float(summary.expenses),
                    "net_income": float(summary.net_income),
                    "currency": summary.currency,
                }

            # Ajouter analyse LLM si demande
            if data.get("with_analysis"):
                analysis = await self._analyze_report(report_type, report_data)
                report_data["ai_analysis"] = analysis

            # Enregistrer l'action
            action_record = MarceauAction(
                tenant_id=self.tenant_id,
                module="comptabilite",
                action_type="generate_report",
                status=ActionStatus.COMPLETED,
                input_data=data,
                output_data={"report_type": report_type, "generated_at": datetime.now().isoformat()},
                reasoning=f"Rapport {report_type} genere",
            )
            self.db.add(action_record)
            self.db.commit()

            return {
                "success": True,
                "action": "generate_report",
                "action_id": str(action_record.id),
                "report": report_data,
                "generated_at": datetime.now().isoformat(),
                "format": data.get("format", "json"),
            }

        except Exception as e:
            logger.error(f"[Comptabilite] Erreur generation rapport: {e}")
            return {
                "success": False,
                "error": str(e),
                "action": "generate_report",
            }

    async def _analyze_report(self, report_type: str, report_data: dict) -> dict:
        """
        Analyse un rapport via LLM.
        """
        llm = await get_llm_client_for_tenant(self.tenant_id, self.db)

        prompt = f"""Analyse ce rapport comptable ({report_type}) et fournis:
1. Points cles (3-5 observations principales)
2. Alertes eventuelles (anomalies, risques)
3. Recommandations (1-3 actions suggerees)

Donnees du rapport:
{json.dumps(report_data, indent=2, default=str)[:2000]}

Reponds en JSON:
{{
    "key_points": ["point 1", "point 2"],
    "alerts": ["alerte si applicable"],
    "recommendations": ["recommandation 1"]
}}"""

        try:
            response = await llm.generate(
                prompt,
                temperature=0.2,
                max_tokens=800,
                system_prompt="Tu es un expert-comptable analysant les comptes d'une entreprise.",
            )

            result = await extract_json_from_response(response)
            return result or {"error": "Analyse non disponible"}

        except Exception as e:
            logger.warning(f"[Comptabilite] Erreur analyse LLM: {e}")
            return {"error": str(e)}

    # ========================================================================
    # ACTION INCONNUE
    # ========================================================================

    async def _unknown_action(self, data: dict, context: list[str]) -> dict:
        """Gere les actions non reconnues."""
        return {
            "success": False,
            "error": "Action comptabilite non reconnue",
            "available_actions": [
                "process_invoice",
                "reconcile_bank",
                "post_entry",
                "generate_report",
            ],
        }
