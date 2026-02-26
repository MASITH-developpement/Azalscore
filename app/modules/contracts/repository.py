"""
AZALS MODULE CONTRACTS - Repository
=====================================

Couche d'acces aux donnees avec isolation multi-tenant stricte.
Toutes les requetes sont filtrees par tenant_id.
"""
from __future__ import annotations


from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, or_, func, desc, asc, extract
from sqlalchemy.orm import Session, joinedload, selectinload

from .models import (
    Contract, ContractParty, ContractLine, ContractClause,
    ContractObligation, ContractMilestone, ContractAmendment,
    ContractRenewal, ContractDocument, ContractAlert,
    ContractApproval, ContractHistory, ContractCategory,
    ContractTemplate, ClauseTemplate, ContractMetrics,
    ContractStatus, ObligationStatus, AlertPriority
)
from .schemas import ContractFilters


class ContractRepository:
    """Repository Contract avec isolation tenant stricte."""

    def __init__(self, db: Session, tenant_id: UUID, include_deleted: bool = False):
        self.db = db
        self.tenant_id = str(tenant_id)
        self.include_deleted = include_deleted

    def _base_query(self):
        """Query de base filtree par tenant_id."""
        query = self.db.query(Contract).filter(Contract.tenant_id == self.tenant_id)
        if not self.include_deleted:
            query = query.filter(Contract.is_deleted == False)
        return query

    def get_by_id(self, id: UUID, with_relations: bool = False) -> Optional[Contract]:
        """Recuperer un contrat par ID."""
        query = self._base_query()
        if with_relations:
            query = query.options(
                selectinload(Contract.parties),
                selectinload(Contract.lines),
                selectinload(Contract.clauses),
                selectinload(Contract.obligations),
                selectinload(Contract.milestones),
                selectinload(Contract.amendments),
                selectinload(Contract.documents),
                selectinload(Contract.alerts),
            )
        return query.filter(Contract.id == id).first()

    def get_by_number(self, contract_number: str) -> Optional[Contract]:
        """Recuperer un contrat par numero."""
        return self._base_query().filter(
            Contract.contract_number == contract_number.upper()
        ).first()

    def exists(self, id: UUID) -> bool:
        """Verifier si un contrat existe."""
        return self._base_query().filter(Contract.id == id).count() > 0

    def number_exists(self, contract_number: str, exclude_id: UUID = None) -> bool:
        """Verifier si un numero de contrat existe."""
        query = self._base_query().filter(
            Contract.contract_number == contract_number.upper()
        )
        if exclude_id:
            query = query.filter(Contract.id != exclude_id)
        return query.count() > 0

    def get_next_number(self, prefix: str = "CTR") -> str:
        """Generer le prochain numero de contrat."""
        year = datetime.utcnow().year
        full_prefix = f"{prefix}-{year}-"

        last = self.db.query(Contract).filter(
            Contract.tenant_id == self.tenant_id,
            Contract.contract_number.like(f"{full_prefix}%")
        ).order_by(desc(Contract.contract_number)).first()

        if last:
            try:
                last_num = int(last.contract_number.split("-")[-1])
                return f"{full_prefix}{last_num + 1:05d}"
            except (ValueError, IndexError):
                pass

        return f"{full_prefix}00001"

    def list(
        self,
        filters: ContractFilters = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc"
    ) -> Tuple[List[Contract], int]:
        """Lister les contrats avec filtres et pagination."""
        query = self._base_query()

        if filters:
            if filters.search:
                term = f"%{filters.search}%"
                query = query.filter(or_(
                    Contract.title.ilike(term),
                    Contract.contract_number.ilike(term),
                    Contract.reference.ilike(term),
                    Contract.description.ilike(term)
                ))

            if filters.status:
                query = query.filter(
                    Contract.status.in_([s.value for s in filters.status])
                )

            if filters.contract_type:
                query = query.filter(
                    Contract.contract_type.in_([t.value for t in filters.contract_type])
                )

            if filters.category_id:
                query = query.filter(Contract.category_id == filters.category_id)

            if filters.owner_id:
                query = query.filter(Contract.owner_id == filters.owner_id)

            if filters.party_id:
                query = query.join(ContractParty).filter(
                    ContractParty.entity_id == filters.party_id
                )

            if filters.party_name:
                query = query.join(ContractParty).filter(
                    ContractParty.name.ilike(f"%{filters.party_name}%")
                )

            if filters.date_from:
                query = query.filter(Contract.start_date >= filters.date_from)

            if filters.date_to:
                query = query.filter(Contract.end_date <= filters.date_to)

            if filters.expiring_within_days:
                future_date = date.today() + timedelta(days=filters.expiring_within_days)
                query = query.filter(
                    Contract.end_date <= future_date,
                    Contract.end_date >= date.today(),
                    Contract.status == ContractStatus.ACTIVE.value
                )

            if filters.renewal_due_within_days:
                future_date = date.today() + timedelta(days=filters.renewal_due_within_days)
                query = query.filter(
                    Contract.next_renewal_date <= future_date,
                    Contract.next_renewal_date >= date.today(),
                    Contract.status == ContractStatus.ACTIVE.value
                )

            if filters.min_value is not None:
                query = query.filter(Contract.total_value >= filters.min_value)

            if filters.max_value is not None:
                query = query.filter(Contract.total_value <= filters.max_value)

            if filters.currency:
                query = query.filter(Contract.currency == filters.currency)

            if filters.tags:
                for tag in filters.tags:
                    query = query.filter(Contract.tags.contains([tag]))

            if filters.is_recurring is not None:
                if filters.is_recurring:
                    query = query.join(ContractLine).filter(
                        ContractLine.is_recurring == True
                    ).distinct()

        total = query.count()

        # Tri
        sort_col = getattr(Contract, sort_by, Contract.created_at)
        query = query.order_by(desc(sort_col) if sort_dir == "desc" else asc(sort_col))

        # Pagination
        offset = (page - 1) * page_size
        items = query.offset(offset).limit(page_size).all()

        return items, total

    def get_by_status(self, status: str) -> List[Contract]:
        """Recuperer les contrats par statut."""
        return self._base_query().filter(Contract.status == status).all()

    def get_active_contracts(self) -> List[Contract]:
        """Recuperer tous les contrats actifs."""
        return self._base_query().filter(
            Contract.status == ContractStatus.ACTIVE.value
        ).order_by(Contract.end_date).all()

    def get_expiring_contracts(self, days: int = 30) -> List[Contract]:
        """Recuperer les contrats qui expirent bientot."""
        future_date = date.today() + timedelta(days=days)
        return self._base_query().filter(
            Contract.status == ContractStatus.ACTIVE.value,
            Contract.end_date <= future_date,
            Contract.end_date >= date.today()
        ).order_by(Contract.end_date).all()

    def get_pending_renewal_notice(self) -> List[Contract]:
        """Recuperer les contrats necessitant un avis de renouvellement."""
        today = date.today()
        return self._base_query().filter(
            Contract.status == ContractStatus.ACTIVE.value,
            Contract.renewal_type.in_(['automatic', 'evergreen']),
            Contract.next_renewal_date != None
        ).all()

    def get_pending_approvals(self, approver_id: UUID = None) -> List[Contract]:
        """Recuperer les contrats en attente d'approbation."""
        query = self._base_query().filter(
            Contract.status == ContractStatus.PENDING_APPROVAL.value
        )
        if approver_id:
            query = query.filter(Contract.current_approver_id == approver_id)
        return query.order_by(Contract.created_at).all()

    def get_pending_signatures(self) -> List[Contract]:
        """Recuperer les contrats en attente de signature."""
        return self._base_query().filter(
            Contract.status.in_([
                ContractStatus.PENDING_SIGNATURE.value,
                ContractStatus.PARTIALLY_SIGNED.value
            ])
        ).order_by(Contract.created_at).all()

    def search_contracts(self, query: str, limit: int = 10) -> List[Contract]:
        """Recherche rapide de contrats."""
        if len(query) < 2:
            return []
        term = f"%{query}%"
        return self._base_query().filter(or_(
            Contract.title.ilike(term),
            Contract.contract_number.ilike(term),
            Contract.reference.ilike(term)
        )).order_by(Contract.created_at.desc()).limit(limit).all()

    def autocomplete(self, prefix: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Autocompletion pour recherche."""
        if len(prefix) < 2:
            return []
        results = self.search_contracts(prefix, limit)
        return [
            {
                "id": str(c.id),
                "number": c.contract_number,
                "title": c.title,
                "label": f"[{c.contract_number}] {c.title}"
            }
            for c in results
        ]

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> Contract:
        """Creer un nouveau contrat."""
        parties_data = data.pop("parties", [])
        lines_data = data.pop("lines", [])
        clauses_data = data.pop("clauses", [])

        # Generer le numero si non fourni
        if "contract_number" not in data or not data["contract_number"]:
            data["contract_number"] = self.get_next_number()

        contract = Contract(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(contract)
        self.db.flush()

        # Ajouter les parties
        for i, party_data in enumerate(parties_data):
            party = ContractParty(
                tenant_id=self.tenant_id,
                contract_id=contract.id,
                sort_order=i,
                created_by=created_by,
                **party_data
            )
            self.db.add(party)

        # Ajouter les lignes
        for i, line_data in enumerate(lines_data):
            line_data["line_number"] = line_data.get("line_number", i + 1)
            self._add_line(contract, line_data, created_by)

        # Ajouter les clauses
        for i, clause_data in enumerate(clauses_data):
            clause_data["sort_order"] = clause_data.get("sort_order", i)
            clause = ContractClause(
                tenant_id=self.tenant_id,
                contract_id=contract.id,
                created_by=created_by,
                **clause_data
            )
            self.db.add(clause)

        # Recalculer la valeur totale
        self._recalculate_total(contract)

        # Enregistrer dans l'historique
        self._add_history(contract, "created", created_by)

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def update(
        self,
        contract: Contract,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> Contract:
        """Mettre a jour un contrat."""
        changes = {}
        for key, value in data.items():
            if hasattr(contract, key) and key not in ["parties", "lines", "clauses"]:
                old_value = getattr(contract, key)
                if old_value != value:
                    changes[key] = {"old": old_value, "new": value}
                    setattr(contract, key, value)

        contract.updated_by = updated_by
        contract.version += 1

        if changes:
            self._add_history(
                contract, "updated", updated_by,
                changes=changes
            )

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def update_status(
        self,
        contract: Contract,
        new_status: str,
        updated_by: UUID = None,
        reason: str = None
    ) -> Contract:
        """Mettre a jour le statut d'un contrat."""
        old_status = contract.status
        contract.status = new_status
        contract.status_reason = reason
        contract.status_changed_at = datetime.utcnow()
        contract.status_changed_by = updated_by
        contract.updated_by = updated_by
        contract.version += 1

        self._add_history(
            contract, "status_changed", updated_by,
            previous_status=old_status,
            new_status=new_status,
            reason=reason
        )

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def soft_delete(self, contract: Contract, deleted_by: UUID = None) -> bool:
        """Suppression logique d'un contrat."""
        contract.is_deleted = True
        contract.deleted_at = datetime.utcnow()
        contract.deleted_by = deleted_by

        self._add_history(contract, "deleted", deleted_by)

        self.db.commit()
        return True

    def restore(self, contract: Contract, restored_by: UUID = None) -> Contract:
        """Restaurer un contrat supprime."""
        contract.is_deleted = False
        contract.deleted_at = None
        contract.deleted_by = None
        contract.updated_by = restored_by

        self._add_history(contract, "restored", restored_by)

        self.db.commit()
        self.db.refresh(contract)
        return contract

    def _add_line(
        self,
        contract: Contract,
        line_data: Dict[str, Any],
        created_by: UUID = None
    ) -> ContractLine:
        """Ajouter une ligne au contrat."""
        # Calculer les totaux
        quantity = Decimal(str(line_data.get("quantity", 1)))
        unit_price = Decimal(str(line_data.get("unit_price", 0)))
        discount_percent = Decimal(str(line_data.get("discount_percent", 0)))
        discount_amount = Decimal(str(line_data.get("discount_amount", 0)))
        tax_rate = Decimal(str(line_data.get("tax_rate", 20)))

        subtotal = quantity * unit_price
        if discount_percent > 0:
            discount_amount = (subtotal * discount_percent / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        subtotal -= discount_amount
        tax_amount = (subtotal * tax_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total = subtotal + tax_amount

        line_data["subtotal"] = subtotal
        line_data["tax_amount"] = tax_amount
        line_data["total"] = total
        line_data["discount_amount"] = discount_amount

        line = ContractLine(
            tenant_id=self.tenant_id,
            contract_id=contract.id,
            created_by=created_by,
            **line_data
        )
        self.db.add(line)
        return line

    def _recalculate_total(self, contract: Contract):
        """Recalculer la valeur totale du contrat."""
        lines = self.db.query(ContractLine).filter(
            ContractLine.contract_id == contract.id,
            ContractLine.is_active == True,
            ContractLine.is_deleted == False
        ).all()

        total = sum(line.total or Decimal("0") for line in lines)
        contract.total_value = total

    def _add_history(
        self,
        contract: Contract,
        action: str,
        user_id: UUID,
        changes: Dict = None,
        previous_status: str = None,
        new_status: str = None,
        reason: str = None
    ):
        """Ajouter une entree dans l'historique."""
        history = ContractHistory(
            tenant_id=self.tenant_id,
            contract_id=contract.id,
            version_number=contract.version,
            action=action,
            changes=changes,
            previous_status=previous_status,
            new_status=new_status,
            user_id=user_id,
            reason=reason
        )
        self.db.add(history)


class ContractPartyRepository:
    """Repository ContractParty avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractParty).filter(
            ContractParty.tenant_id == self.tenant_id,
            ContractParty.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractParty]:
        return self._base_query().filter(ContractParty.id == id).first()

    def get_by_contract(self, contract_id: UUID) -> List[ContractParty]:
        return self._base_query().filter(
            ContractParty.contract_id == contract_id
        ).order_by(ContractParty.sort_order).all()

    def get_primary_party(self, contract_id: UUID, role: str) -> Optional[ContractParty]:
        return self._base_query().filter(
            ContractParty.contract_id == contract_id,
            ContractParty.role == role,
            ContractParty.is_primary == True
        ).first()

    def get_unsigned_parties(self, contract_id: UUID) -> List[ContractParty]:
        return self._base_query().filter(
            ContractParty.contract_id == contract_id,
            ContractParty.is_signatory == True,
            ContractParty.has_signed == False
        ).all()

    def create(
        self,
        contract_id: UUID,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> ContractParty:
        party = ContractParty(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            created_by=created_by,
            **data
        )
        self.db.add(party)
        self.db.commit()
        self.db.refresh(party)
        return party

    def update(
        self,
        party: ContractParty,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ContractParty:
        for key, value in data.items():
            if hasattr(party, key):
                setattr(party, key, value)
        party.updated_by = updated_by
        self.db.commit()
        self.db.refresh(party)
        return party

    def record_signature(
        self,
        party: ContractParty,
        signature_id: str,
        signature_ip: str = None
    ) -> ContractParty:
        party.has_signed = True
        party.signed_at = datetime.utcnow()
        party.signature_id = signature_id
        party.signature_ip = signature_ip
        self.db.commit()
        self.db.refresh(party)
        return party

    def soft_delete(self, party: ContractParty, deleted_by: UUID = None) -> bool:
        party.is_deleted = True
        party.deleted_at = datetime.utcnow()
        party.deleted_by = deleted_by
        self.db.commit()
        return True


class ContractLineRepository:
    """Repository ContractLine avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractLine).filter(
            ContractLine.tenant_id == self.tenant_id,
            ContractLine.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractLine]:
        return self._base_query().filter(ContractLine.id == id).first()

    def get_by_contract(self, contract_id: UUID) -> List[ContractLine]:
        return self._base_query().filter(
            ContractLine.contract_id == contract_id
        ).order_by(ContractLine.line_number).all()

    def get_recurring_lines(self, contract_id: UUID = None) -> List[ContractLine]:
        query = self._base_query().filter(
            ContractLine.is_recurring == True,
            ContractLine.is_active == True
        )
        if contract_id:
            query = query.filter(ContractLine.contract_id == contract_id)
        return query.all()

    def get_lines_due_for_billing(self, before_date: date = None) -> List[ContractLine]:
        if not before_date:
            before_date = date.today()
        return self._base_query().filter(
            ContractLine.is_recurring == True,
            ContractLine.is_active == True,
            ContractLine.next_billing_date <= before_date
        ).all()

    def create(
        self,
        contract_id: UUID,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> ContractLine:
        # Calculer les totaux
        quantity = Decimal(str(data.get("quantity", 1)))
        unit_price = Decimal(str(data.get("unit_price", 0)))
        discount_percent = Decimal(str(data.get("discount_percent", 0)))
        discount_amount = Decimal(str(data.get("discount_amount", 0)))
        tax_rate = Decimal(str(data.get("tax_rate", 20)))

        subtotal = quantity * unit_price
        if discount_percent > 0:
            discount_amount = (subtotal * discount_percent / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        subtotal -= discount_amount
        tax_amount = (subtotal * tax_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total = subtotal + tax_amount

        data["subtotal"] = subtotal
        data["tax_amount"] = tax_amount
        data["total"] = total
        data["discount_amount"] = discount_amount

        line = ContractLine(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            created_by=created_by,
            **data
        )
        self.db.add(line)
        self.db.commit()
        self.db.refresh(line)
        return line

    def update(
        self,
        line: ContractLine,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ContractLine:
        for key, value in data.items():
            if hasattr(line, key):
                setattr(line, key, value)

        # Recalculer les totaux
        quantity = line.quantity or Decimal("1")
        unit_price = line.unit_price or Decimal("0")
        discount_percent = line.discount_percent or Decimal("0")
        discount_amount = line.discount_amount or Decimal("0")
        tax_rate = line.tax_rate or Decimal("20")

        subtotal = quantity * unit_price
        if discount_percent > 0:
            discount_amount = (subtotal * discount_percent / 100).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        subtotal -= discount_amount
        tax_amount = (subtotal * tax_rate / 100).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        line.subtotal = subtotal
        line.tax_amount = tax_amount
        line.total = subtotal + tax_amount
        line.discount_amount = discount_amount

        line.updated_by = updated_by
        line.version += 1
        self.db.commit()
        self.db.refresh(line)
        return line

    def soft_delete(self, line: ContractLine, deleted_by: UUID = None) -> bool:
        line.is_deleted = True
        line.deleted_at = datetime.utcnow()
        line.deleted_by = deleted_by
        self.db.commit()
        return True


class ContractObligationRepository:
    """Repository ContractObligation avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractObligation).filter(
            ContractObligation.tenant_id == self.tenant_id,
            ContractObligation.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractObligation]:
        return self._base_query().filter(ContractObligation.id == id).first()

    def get_by_contract(self, contract_id: UUID) -> List[ContractObligation]:
        return self._base_query().filter(
            ContractObligation.contract_id == contract_id
        ).order_by(ContractObligation.due_date).all()

    def get_pending_obligations(
        self,
        contract_id: UUID = None,
        due_before: date = None
    ) -> List[ContractObligation]:
        query = self._base_query().filter(
            ContractObligation.status == ObligationStatus.PENDING.value
        )
        if contract_id:
            query = query.filter(ContractObligation.contract_id == contract_id)
        if due_before:
            query = query.filter(ContractObligation.due_date <= due_before)
        return query.order_by(ContractObligation.due_date).all()

    def get_overdue_obligations(self) -> List[ContractObligation]:
        return self._base_query().filter(
            ContractObligation.status == ObligationStatus.PENDING.value,
            ContractObligation.due_date < date.today()
        ).order_by(ContractObligation.due_date).all()

    def get_upcoming_obligations(self, days: int = 30) -> List[ContractObligation]:
        future_date = date.today() + timedelta(days=days)
        return self._base_query().filter(
            ContractObligation.status == ObligationStatus.PENDING.value,
            ContractObligation.due_date <= future_date,
            ContractObligation.due_date >= date.today()
        ).order_by(ContractObligation.due_date).all()

    def create(
        self,
        contract_id: UUID,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> ContractObligation:
        obligation = ContractObligation(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            created_by=created_by,
            **data
        )
        if obligation.is_recurring and obligation.due_date:
            obligation.next_due_date = obligation.due_date
        self.db.add(obligation)
        self.db.commit()
        self.db.refresh(obligation)
        return obligation

    def update(
        self,
        obligation: ContractObligation,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ContractObligation:
        for key, value in data.items():
            if hasattr(obligation, key):
                setattr(obligation, key, value)
        obligation.updated_by = updated_by
        obligation.version += 1
        self.db.commit()
        self.db.refresh(obligation)
        return obligation

    def mark_completed(
        self,
        obligation: ContractObligation,
        completed_by: UUID,
        notes: str = None
    ) -> ContractObligation:
        obligation.status = ObligationStatus.COMPLETED.value
        obligation.completed_at = datetime.utcnow()
        obligation.completed_by = completed_by
        obligation.completion_notes = notes
        obligation.last_completed_date = date.today()
        obligation.occurrences_completed += 1

        # Si recurrent, calculer la prochaine echeance
        if obligation.is_recurring and obligation.recurrence_end_date:
            if obligation.next_due_date and obligation.next_due_date < obligation.recurrence_end_date:
                obligation.next_due_date = self._calculate_next_due_date(
                    obligation.next_due_date,
                    obligation.recurrence_pattern,
                    obligation.recurrence_interval
                )
                obligation.status = ObligationStatus.PENDING.value
                obligation.alert_sent = False

        self.db.commit()
        self.db.refresh(obligation)
        return obligation

    def _calculate_next_due_date(
        self,
        current_date: date,
        pattern: str,
        interval: int
    ) -> date:
        """Calculer la prochaine date d'echeance."""
        if pattern == "daily":
            return current_date + timedelta(days=interval)
        elif pattern == "weekly":
            return current_date + timedelta(weeks=interval)
        elif pattern == "monthly":
            month = current_date.month + interval
            year = current_date.year + (month - 1) // 12
            month = ((month - 1) % 12) + 1
            day = min(current_date.day, 28)  # Eviter les problemes de fin de mois
            return date(year, month, day)
        elif pattern == "quarterly":
            return self._calculate_next_due_date(current_date, "monthly", interval * 3)
        elif pattern == "yearly":
            return date(current_date.year + interval, current_date.month, current_date.day)
        return current_date

    def soft_delete(
        self,
        obligation: ContractObligation,
        deleted_by: UUID = None
    ) -> bool:
        obligation.is_deleted = True
        obligation.deleted_at = datetime.utcnow()
        obligation.deleted_by = deleted_by
        self.db.commit()
        return True


class ContractMilestoneRepository:
    """Repository ContractMilestone avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractMilestone).filter(
            ContractMilestone.tenant_id == self.tenant_id,
            ContractMilestone.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractMilestone]:
        return self._base_query().filter(ContractMilestone.id == id).first()

    def get_by_contract(self, contract_id: UUID) -> List[ContractMilestone]:
        return self._base_query().filter(
            ContractMilestone.contract_id == contract_id
        ).order_by(ContractMilestone.sort_order, ContractMilestone.target_date).all()

    def get_upcoming_milestones(self, days: int = 30) -> List[ContractMilestone]:
        future_date = date.today() + timedelta(days=days)
        return self._base_query().filter(
            ContractMilestone.status.in_(["pending", "in_progress"]),
            ContractMilestone.target_date <= future_date,
            ContractMilestone.target_date >= date.today()
        ).order_by(ContractMilestone.target_date).all()

    def create(
        self,
        contract_id: UUID,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> ContractMilestone:
        milestone = ContractMilestone(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            created_by=created_by,
            **data
        )
        self.db.add(milestone)
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def update(
        self,
        milestone: ContractMilestone,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ContractMilestone:
        for key, value in data.items():
            if hasattr(milestone, key):
                setattr(milestone, key, value)
        milestone.updated_by = updated_by
        milestone.version += 1
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def mark_completed(
        self,
        milestone: ContractMilestone,
        completed_by: UUID,
        actual_date: date = None,
        notes: str = None
    ) -> ContractMilestone:
        milestone.status = "completed"
        milestone.actual_date = actual_date or date.today()
        milestone.completed_at = datetime.utcnow()
        milestone.completed_by = completed_by
        milestone.progress_percentage = 100
        if notes:
            milestone.notes = notes
        self.db.commit()
        self.db.refresh(milestone)
        return milestone

    def soft_delete(
        self,
        milestone: ContractMilestone,
        deleted_by: UUID = None
    ) -> bool:
        milestone.is_deleted = True
        milestone.deleted_at = datetime.utcnow()
        milestone.deleted_by = deleted_by
        self.db.commit()
        return True


class ContractAmendmentRepository:
    """Repository ContractAmendment avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractAmendment).filter(
            ContractAmendment.tenant_id == self.tenant_id,
            ContractAmendment.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractAmendment]:
        return self._base_query().filter(ContractAmendment.id == id).first()

    def get_by_contract(self, contract_id: UUID) -> List[ContractAmendment]:
        return self._base_query().filter(
            ContractAmendment.contract_id == contract_id
        ).order_by(ContractAmendment.amendment_number).all()

    def get_next_amendment_number(self, contract_id: UUID) -> int:
        last = self._base_query().filter(
            ContractAmendment.contract_id == contract_id
        ).order_by(desc(ContractAmendment.amendment_number)).first()
        return (last.amendment_number + 1) if last else 1

    def create(
        self,
        contract_id: UUID,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> ContractAmendment:
        if "amendment_number" not in data:
            data["amendment_number"] = self.get_next_amendment_number(contract_id)

        amendment = ContractAmendment(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            created_by=created_by,
            **data
        )
        self.db.add(amendment)
        self.db.commit()
        self.db.refresh(amendment)
        return amendment

    def update(
        self,
        amendment: ContractAmendment,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ContractAmendment:
        for key, value in data.items():
            if hasattr(amendment, key):
                setattr(amendment, key, value)
        amendment.updated_by = updated_by
        amendment.version += 1
        self.db.commit()
        self.db.refresh(amendment)
        return amendment

    def soft_delete(
        self,
        amendment: ContractAmendment,
        deleted_by: UUID = None
    ) -> bool:
        amendment.is_deleted = True
        amendment.deleted_at = datetime.utcnow()
        amendment.deleted_by = deleted_by
        self.db.commit()
        return True


class ContractAlertRepository:
    """Repository ContractAlert avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractAlert).filter(
            ContractAlert.tenant_id == self.tenant_id,
            ContractAlert.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractAlert]:
        return self._base_query().filter(ContractAlert.id == id).first()

    def get_by_contract(self, contract_id: UUID) -> List[ContractAlert]:
        return self._base_query().filter(
            ContractAlert.contract_id == contract_id
        ).order_by(ContractAlert.due_date).all()

    def get_active_alerts(self, contract_id: UUID = None) -> List[ContractAlert]:
        query = self._base_query().filter(
            ContractAlert.is_active == True,
            ContractAlert.status.in_(["pending", "sent"])
        )
        if contract_id:
            query = query.filter(ContractAlert.contract_id == contract_id)
        return query.order_by(ContractAlert.due_date).all()

    def get_pending_alerts(self, before_date: date = None) -> List[ContractAlert]:
        if not before_date:
            before_date = date.today()
        return self._base_query().filter(
            ContractAlert.is_active == True,
            ContractAlert.is_sent == False,
            ContractAlert.trigger_date <= before_date
        ).order_by(ContractAlert.priority.desc(), ContractAlert.due_date).all()

    def create(
        self,
        contract_id: UUID,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> ContractAlert:
        alert = ContractAlert(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            created_by=created_by,
            **data
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def mark_sent(self, alert: ContractAlert) -> ContractAlert:
        alert.is_sent = True
        alert.sent_at = datetime.utcnow()
        alert.notification_count += 1
        alert.last_notification_at = datetime.utcnow()
        alert.status = "sent"
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def acknowledge(
        self,
        alert: ContractAlert,
        acknowledged_by: UUID,
        notes: str = None,
        action_taken: str = None
    ) -> ContractAlert:
        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = acknowledged_by
        alert.acknowledgement_notes = notes
        alert.action_taken = action_taken
        alert.action_date = datetime.utcnow()
        alert.status = "acknowledged"
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def dismiss(self, alert: ContractAlert) -> ContractAlert:
        alert.is_active = False
        alert.status = "dismissed"
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def soft_delete(self, alert: ContractAlert, deleted_by: UUID = None) -> bool:
        alert.is_deleted = True
        alert.deleted_at = datetime.utcnow()
        alert.deleted_by = deleted_by
        self.db.commit()
        return True


class ContractApprovalRepository:
    """Repository ContractApproval avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractApproval).filter(
            ContractApproval.tenant_id == self.tenant_id,
            ContractApproval.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractApproval]:
        return self._base_query().filter(ContractApproval.id == id).first()

    def get_by_contract(self, contract_id: UUID) -> List[ContractApproval]:
        return self._base_query().filter(
            ContractApproval.contract_id == contract_id
        ).order_by(ContractApproval.level, ContractApproval.sort_order).all()

    def get_pending_for_user(self, user_id: UUID) -> List[ContractApproval]:
        return self._base_query().filter(
            ContractApproval.approver_id == user_id,
            ContractApproval.status == "pending"
        ).order_by(ContractApproval.due_date).all()

    def get_current_approval(self, contract_id: UUID) -> Optional[ContractApproval]:
        return self._base_query().filter(
            ContractApproval.contract_id == contract_id,
            ContractApproval.status == "pending"
        ).order_by(ContractApproval.level).first()

    def create(
        self,
        contract_id: UUID,
        data: Dict[str, Any],
        created_by: UUID = None
    ) -> ContractApproval:
        approval = ContractApproval(
            tenant_id=self.tenant_id,
            contract_id=contract_id,
            created_by=created_by,
            **data
        )
        self.db.add(approval)
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def record_decision(
        self,
        approval: ContractApproval,
        decision: str,
        comments: str = None,
        rejection_reason: str = None,
        conditions: List = None
    ) -> ContractApproval:
        approval.status = "approved" if decision == "approved" else "rejected"
        approval.decision = decision
        approval.decision_date = datetime.utcnow()
        approval.comments = comments
        approval.rejection_reason = rejection_reason
        if conditions:
            approval.approved_with_conditions = True
            approval.conditions = conditions
        self.db.commit()
        self.db.refresh(approval)
        return approval

    def delegate(
        self,
        approval: ContractApproval,
        delegate_to_id: UUID,
        reason: str = None
    ) -> ContractApproval:
        approval.status = "delegated"
        approval.delegated_from_id = approval.approver_id
        approval.delegation_reason = reason

        # Creer nouvelle approbation pour le delegue
        new_approval = ContractApproval(
            tenant_id=self.tenant_id,
            contract_id=approval.contract_id,
            amendment_id=approval.amendment_id,
            level=approval.level,
            level_name=approval.level_name,
            approver_id=delegate_to_id,
            due_date=approval.due_date,
            delegated_from_id=approval.approver_id,
            delegation_reason=reason
        )
        self.db.add(new_approval)
        self.db.commit()
        self.db.refresh(new_approval)
        return new_approval


class ContractCategoryRepository:
    """Repository ContractCategory avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractCategory).filter(
            ContractCategory.tenant_id == self.tenant_id,
            ContractCategory.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractCategory]:
        return self._base_query().filter(ContractCategory.id == id).first()

    def get_by_code(self, code: str) -> Optional[ContractCategory]:
        return self._base_query().filter(
            ContractCategory.code == code.upper()
        ).first()

    def list_all(self, active_only: bool = True) -> List[ContractCategory]:
        query = self._base_query()
        if active_only:
            query = query.filter(ContractCategory.is_active == True)
        return query.order_by(ContractCategory.sort_order, ContractCategory.name).all()

    def get_root_categories(self) -> List[ContractCategory]:
        return self._base_query().filter(
            ContractCategory.parent_id == None,
            ContractCategory.is_active == True
        ).order_by(ContractCategory.sort_order).all()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(ContractCategory.code == code.upper())
        if exclude_id:
            query = query.filter(ContractCategory.id != exclude_id)
        return query.count() > 0

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ContractCategory:
        data["code"] = data["code"].upper()
        category = ContractCategory(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    def update(
        self,
        category: ContractCategory,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ContractCategory:
        for key, value in data.items():
            if hasattr(category, key):
                if key == "code":
                    value = value.upper()
                setattr(category, key, value)
        category.updated_by = updated_by
        category.version += 1
        self.db.commit()
        self.db.refresh(category)
        return category

    def soft_delete(
        self,
        category: ContractCategory,
        deleted_by: UUID = None
    ) -> bool:
        category.is_deleted = True
        category.deleted_at = datetime.utcnow()
        category.deleted_by = deleted_by
        self.db.commit()
        return True


class ContractTemplateRepository:
    """Repository ContractTemplate avec isolation tenant."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def _base_query(self):
        return self.db.query(ContractTemplate).filter(
            ContractTemplate.tenant_id == self.tenant_id,
            ContractTemplate.is_deleted == False
        )

    def get_by_id(self, id: UUID) -> Optional[ContractTemplate]:
        return self._base_query().options(
            selectinload(ContractTemplate.clause_templates)
        ).filter(ContractTemplate.id == id).first()

    def get_by_code(self, code: str) -> Optional[ContractTemplate]:
        return self._base_query().filter(
            ContractTemplate.code == code.upper()
        ).first()

    def list_all(
        self,
        contract_type: str = None,
        active_only: bool = True
    ) -> List[ContractTemplate]:
        query = self._base_query()
        if active_only:
            query = query.filter(ContractTemplate.is_active == True)
        if contract_type:
            query = query.filter(ContractTemplate.contract_type == contract_type)
        return query.order_by(ContractTemplate.name).all()

    def get_default(self, contract_type: str) -> Optional[ContractTemplate]:
        return self._base_query().filter(
            ContractTemplate.contract_type == contract_type,
            ContractTemplate.is_default == True,
            ContractTemplate.is_active == True
        ).first()

    def code_exists(self, code: str, exclude_id: UUID = None) -> bool:
        query = self._base_query().filter(ContractTemplate.code == code.upper())
        if exclude_id:
            query = query.filter(ContractTemplate.id != exclude_id)
        return query.count() > 0

    def create(self, data: Dict[str, Any], created_by: UUID = None) -> ContractTemplate:
        data["code"] = data["code"].upper()

        # Si is_default, desactiver les autres
        if data.get("is_default"):
            self._base_query().filter(
                ContractTemplate.contract_type == data.get("contract_type"),
                ContractTemplate.is_default == True
            ).update({"is_default": False})

        template = ContractTemplate(
            tenant_id=self.tenant_id,
            created_by=created_by,
            **data
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def update(
        self,
        template: ContractTemplate,
        data: Dict[str, Any],
        updated_by: UUID = None
    ) -> ContractTemplate:
        if data.get("is_default") and not template.is_default:
            self._base_query().filter(
                ContractTemplate.contract_type == template.contract_type,
                ContractTemplate.is_default == True,
                ContractTemplate.id != template.id
            ).update({"is_default": False})

        for key, value in data.items():
            if hasattr(template, key):
                if key == "code":
                    value = value.upper()
                setattr(template, key, value)
        template.updated_by = updated_by
        template.version += 1
        self.db.commit()
        self.db.refresh(template)
        return template

    def soft_delete(
        self,
        template: ContractTemplate,
        deleted_by: UUID = None
    ) -> bool:
        template.is_deleted = True
        template.deleted_at = datetime.utcnow()
        template.deleted_by = deleted_by
        self.db.commit()
        return True


class ContractMetricsRepository:
    """Repository ContractMetrics pour les statistiques."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = str(tenant_id)

    def get_by_date(self, metric_date: date) -> Optional[ContractMetrics]:
        return self.db.query(ContractMetrics).filter(
            ContractMetrics.tenant_id == self.tenant_id,
            ContractMetrics.metric_date == metric_date
        ).first()

    def get_range(
        self,
        start_date: date,
        end_date: date
    ) -> List[ContractMetrics]:
        return self.db.query(ContractMetrics).filter(
            ContractMetrics.tenant_id == self.tenant_id,
            ContractMetrics.metric_date >= start_date,
            ContractMetrics.metric_date <= end_date
        ).order_by(ContractMetrics.metric_date).all()

    def save(self, data: Dict[str, Any]) -> ContractMetrics:
        metric_date = data.get("metric_date", date.today())

        # Upsert
        existing = self.get_by_date(metric_date)
        if existing:
            for key, value in data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            metrics = ContractMetrics(
                tenant_id=self.tenant_id,
                **data
            )
            self.db.add(metrics)
            self.db.commit()
            self.db.refresh(metrics)
            return metrics
