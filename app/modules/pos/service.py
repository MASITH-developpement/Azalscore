"""
AZALS MODULE 13 - POS Service
==============================
Logique métier pour le Point de Vente.
"""
from __future__ import annotations


import logging
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import case, func, or_
from sqlalchemy.orm import Session

from .models import (
    CashMovement,
    DiscountType,
    PaymentMethodType,
    POSDailyReport,
    POSHoldTransaction,
    POSOfflineQueue,
    POSPayment,
    POSProductQuickKey,
    POSSession,
    POSSessionStatus,
    POSStore,
    POSTerminal,
    POSTerminalStatus,
    POSTransaction,
    POSTransactionLine,
    POSTransactionStatus,
    POSUser,
)
from .schemas import (
    CashMovementCreate,
    HoldTransactionCreate,
    PaymentCreate,
    POSUserCreate,
    POSUserLogin,
    POSUserUpdate,
    QuickKeyCreate,
    SessionCloseRequest,
    SessionOpenRequest,
    StoreCreate,
    StoreUpdate,
    TerminalCreate,
    TerminalUpdate,
    TransactionCreate,
    TransactionLineCreate,
)

logger = logging.getLogger(__name__)


class POSService:
    """Service POS complet."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # STORES
    # ========================================================================

    def create_store(self, data: StoreCreate) -> POSStore:
        """Créer un magasin."""
        # Vérifier code unique
        existing = self.db.query(POSStore).filter(
            POSStore.tenant_id == self.tenant_id,
            POSStore.code == data.code
        ).first()
        if existing:
            raise ValueError(f"Code magasin '{data.code}' déjà utilisé")

        store = POSStore(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(store)
        self.db.commit()
        self.db.refresh(store)
        return store

    def get_store(self, store_id: int) -> POSStore | None:
        """Récupérer un magasin."""
        return self.db.query(POSStore).filter(
            POSStore.tenant_id == self.tenant_id,
            POSStore.id == store_id
        ).first()

    def get_store_by_code(self, code: str) -> POSStore | None:
        """Récupérer magasin par code."""
        return self.db.query(POSStore).filter(
            POSStore.tenant_id == self.tenant_id,
            POSStore.code == code
        ).first()

    def list_stores(
        self,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[POSStore]:
        """Lister les magasins."""
        query = self.db.query(POSStore).filter(
            POSStore.tenant_id == self.tenant_id
        )
        if is_active is not None:
            query = query.filter(POSStore.is_active == is_active)
        return query.offset(skip).limit(limit).all()

    def update_store(self, store_id: int, data: StoreUpdate) -> POSStore | None:
        """Mettre à jour un magasin."""
        store = self.get_store(store_id)
        if not store:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(store, field, value)

        store.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(store)
        return store

    def delete_store(self, store_id: int) -> bool:
        """Supprimer un magasin (soft delete)."""
        store = self.get_store(store_id)
        if not store:
            return False

        store.is_active = False
        store.updated_at = datetime.utcnow()
        self.db.commit()
        return True

    # ========================================================================
    # TERMINALS
    # ========================================================================

    def create_terminal(self, data: TerminalCreate) -> POSTerminal:
        """Créer un terminal."""
        # Vérifier magasin existe
        store = self.get_store(data.store_id)
        if not store:
            raise ValueError("Magasin introuvable")

        # Vérifier terminal_id unique
        existing = self.db.query(POSTerminal).filter(
            POSTerminal.tenant_id == self.tenant_id,
            POSTerminal.terminal_id == data.terminal_id
        ).first()
        if existing:
            raise ValueError(f"Terminal ID '{data.terminal_id}' déjà utilisé")

        terminal = POSTerminal(
            tenant_id=self.tenant_id,
            status=POSTerminalStatus.OFFLINE,
            **data.model_dump()
        )
        self.db.add(terminal)
        self.db.commit()
        self.db.refresh(terminal)
        return terminal

    def get_terminal(self, terminal_id: int) -> POSTerminal | None:
        """Récupérer un terminal."""
        return self.db.query(POSTerminal).filter(
            POSTerminal.tenant_id == self.tenant_id,
            POSTerminal.id == terminal_id
        ).first()

    def get_terminal_by_code(self, terminal_code: str) -> POSTerminal | None:
        """Récupérer terminal par code."""
        return self.db.query(POSTerminal).filter(
            POSTerminal.tenant_id == self.tenant_id,
            POSTerminal.terminal_id == terminal_code
        ).first()

    def list_terminals(
        self,
        store_id: int | None = None,
        status: POSTerminalStatus | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[POSTerminal]:
        """Lister les terminaux."""
        query = self.db.query(POSTerminal).filter(
            POSTerminal.tenant_id == self.tenant_id
        )
        if store_id:
            query = query.filter(POSTerminal.store_id == store_id)
        if status:
            query = query.filter(POSTerminal.status == status)
        return query.offset(skip).limit(limit).all()

    def update_terminal(
        self, terminal_id: int, data: TerminalUpdate
    ) -> POSTerminal | None:
        """Mettre à jour un terminal."""
        terminal = self.get_terminal(terminal_id)
        if not terminal:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(terminal, field, value)

        self.db.commit()
        self.db.refresh(terminal)
        return terminal

    def ping_terminal(self, terminal_id: int) -> POSTerminal | None:
        """Signal heartbeat du terminal."""
        terminal = self.get_terminal(terminal_id)
        if not terminal:
            return None

        terminal.last_ping = datetime.utcnow()
        if terminal.status == POSTerminalStatus.OFFLINE:
            terminal.status = POSTerminalStatus.ONLINE

        self.db.commit()
        self.db.refresh(terminal)
        return terminal

    def sync_terminal(self, terminal_id: int) -> POSTerminal | None:
        """Marquer terminal synchronisé."""
        terminal = self.get_terminal(terminal_id)
        if not terminal:
            return None

        terminal.last_sync = datetime.utcnow()
        self.db.commit()
        self.db.refresh(terminal)
        return terminal

    # ========================================================================
    # POS USERS (Cashiers)
    # ========================================================================

    def create_pos_user(self, data: POSUserCreate) -> POSUser:
        """Créer un utilisateur POS."""
        # Vérifier code employé unique
        existing = self.db.query(POSUser).filter(
            POSUser.tenant_id == self.tenant_id,
            POSUser.employee_code == data.employee_code
        ).first()
        if existing:
            raise ValueError(f"Code employé '{data.employee_code}' déjà utilisé")

        pos_user = POSUser(
            tenant_id=self.tenant_id,
            is_active=True,
            **data.model_dump()
        )
        self.db.add(pos_user)
        self.db.commit()
        self.db.refresh(pos_user)
        return pos_user

    def get_pos_user(self, user_id: int) -> POSUser | None:
        """Récupérer un utilisateur POS."""
        return self.db.query(POSUser).filter(
            POSUser.tenant_id == self.tenant_id,
            POSUser.id == user_id
        ).first()

    def get_pos_user_by_code(self, employee_code: str) -> POSUser | None:
        """Récupérer utilisateur par code employé."""
        return self.db.query(POSUser).filter(
            POSUser.tenant_id == self.tenant_id,
            POSUser.employee_code == employee_code,
            POSUser.is_active
        ).first()

    def list_pos_users(
        self,
        is_active: bool | None = None,
        is_manager: bool | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[POSUser]:
        """Lister les utilisateurs POS."""
        query = self.db.query(POSUser).filter(
            POSUser.tenant_id == self.tenant_id
        )
        if is_active is not None:
            query = query.filter(POSUser.is_active == is_active)
        if is_manager is not None:
            query = query.filter(POSUser.is_manager == is_manager)
        return query.offset(skip).limit(limit).all()

    def update_pos_user(
        self, user_id: int, data: POSUserUpdate
    ) -> POSUser | None:
        """Mettre à jour un utilisateur POS."""
        pos_user = self.get_pos_user(user_id)
        if not pos_user:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(pos_user, field, value)

        self.db.commit()
        self.db.refresh(pos_user)
        return pos_user

    def authenticate_pos_user(
        self, data: POSUserLogin
    ) -> POSUser | None:
        """Authentifier utilisateur POS."""
        pos_user = self.get_pos_user_by_code(data.employee_code)
        if not pos_user:
            return None

        # Vérifier PIN si requis
        if pos_user.pin_code and pos_user.pin_code != data.pin_code:
            return None

        return pos_user

    # ========================================================================
    # SESSIONS
    # ========================================================================

    def _generate_session_number(self, terminal_id: int) -> str:
        """Générer numéro de session."""
        today = date.today()
        prefix = f"S{today.strftime('%Y%m%d')}"

        last_session = self.db.query(POSSession).filter(
            POSSession.tenant_id == self.tenant_id,
            POSSession.session_number.like(f"{prefix}%")
        ).order_by(POSSession.id.desc()).first()

        if last_session:
            last_num = int(last_session.session_number[-4:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def open_session(self, data: SessionOpenRequest) -> POSSession:
        """Ouvrir une session de caisse."""
        logger.info(
            "Opening POS session | tenant=%s user=%s terminal_id=%s opening_cash=%s",
            self.tenant_id, data.cashier_id, data.terminal_id, data.opening_cash
        )
        # Vérifier terminal
        terminal = self.get_terminal(data.terminal_id)
        if not terminal:
            raise ValueError("Terminal introuvable")

        if terminal.current_session_id:
            raise ValueError("Une session est déjà ouverte sur ce terminal")

        # Vérifier caissier
        cashier = self.get_pos_user(data.cashier_id)
        if not cashier:
            raise ValueError("Caissier introuvable")

        if not cashier.is_active:
            raise ValueError("Caissier inactif")

        # Créer session
        session = POSSession(
            tenant_id=self.tenant_id,
            terminal_id=data.terminal_id,
            session_number=self._generate_session_number(data.terminal_id),
            status=POSSessionStatus.OPEN,
            opened_by_id=data.cashier_id,
            opening_cash=data.opening_cash,
            opening_note=data.opening_note,
            opened_at=datetime.utcnow(),
            total_sales=Decimal("0"),
            total_refunds=Decimal("0"),
            total_discounts=Decimal("0"),
            transaction_count=0,
            cash_total=Decimal("0"),
            card_total=Decimal("0"),
            check_total=Decimal("0"),
            voucher_total=Decimal("0"),
            other_total=Decimal("0")
        )
        self.db.add(session)
        self.db.flush()

        # Mettre à jour terminal
        terminal.current_session_id = session.id
        terminal.status = POSTerminalStatus.IN_USE

        self.db.commit()
        self.db.refresh(session)
        logger.info(
            "POS session opened | session_id=%s session_number=%s",
            session.id, session.session_number
        )
        return session

    def get_session(self, session_id: int) -> POSSession | None:
        """Récupérer une session."""
        return self.db.query(POSSession).filter(
            POSSession.tenant_id == self.tenant_id,
            POSSession.id == session_id
        ).first()

    def get_current_session(self, terminal_id: int) -> POSSession | None:
        """Récupérer session active du terminal."""
        terminal = self.get_terminal(terminal_id)
        if not terminal or not terminal.current_session_id:
            return None
        return self.get_session(terminal.current_session_id)

    def list_sessions(
        self,
        terminal_id: int | None = None,
        status: POSSessionStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> list[POSSession]:
        """Lister les sessions."""
        query = self.db.query(POSSession).filter(
            POSSession.tenant_id == self.tenant_id
        )
        if terminal_id:
            query = query.filter(POSSession.terminal_id == terminal_id)
        if status:
            query = query.filter(POSSession.status == status)
        if date_from:
            query = query.filter(POSSession.opened_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            query = query.filter(POSSession.opened_at <= datetime.combine(date_to, datetime.max.time()))

        return query.order_by(POSSession.opened_at.desc()).offset(skip).limit(limit).all()

    def close_session(
        self, session_id: int, data: SessionCloseRequest, closed_by_id: int
    ) -> POSSession:
        """Fermer une session de caisse."""
        logger.info(
            "Closing POS session | tenant=%s user=%s session_id=%s actual_cash=%s",
            self.tenant_id, closed_by_id, session_id, data.actual_cash
        )
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session introuvable")

        if session.status != POSSessionStatus.OPEN:
            raise ValueError("Session non ouverte")

        # Vérifier permissions
        closer = self.get_pos_user(closed_by_id)
        if not closer:
            raise ValueError("Utilisateur introuvable")

        if not closer.can_close_session and not closer.is_manager and closer.id != session.opened_by_id:
            raise ValueError("Pas autorisé à fermer cette session")

        # Calculer caisse attendue
        expected_cash = (
            session.opening_cash +
            session.cash_total -
            session.total_refunds
        )

        # Ajouter mouvements de caisse
        cash_movements = self.db.query(func.coalesce(
            func.sum(
                case(
                    (CashMovement.movement_type == "IN", CashMovement.amount),
                    else_=-CashMovement.amount
                )
            ), 0
        )).filter(CashMovement.session_id == session_id).scalar()

        expected_cash += cash_movements

        # Mettre à jour session
        session.status = POSSessionStatus.CLOSED
        session.closed_by_id = closed_by_id
        session.closed_at = datetime.utcnow()
        session.actual_cash = data.actual_cash
        session.expected_cash = expected_cash
        session.cash_difference = data.actual_cash - expected_cash
        session.closing_note = data.closing_note

        # Libérer terminal
        terminal = self.get_terminal(session.terminal_id)
        if terminal:
            terminal.current_session_id = None
            terminal.status = POSTerminalStatus.ONLINE

        self.db.commit()
        self.db.refresh(session)
        logger.info(
            "POS session closed | session_id=%s session_number=%s cash_difference=%s",
            session.id, session.session_number, session.cash_difference
        )
        return session

    def add_cash_movement(
        self, session_id: int, data: CashMovementCreate, performed_by_id: int
    ) -> CashMovement:
        """Ajouter un mouvement de caisse."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session introuvable")

        if session.status != POSSessionStatus.OPEN:
            raise ValueError("Session fermée")

        # Vérifier permissions
        user = self.get_pos_user(performed_by_id)
        if not user:
            raise ValueError("Utilisateur introuvable")

        if data.movement_type == "OUT" and not user.can_open_drawer:
            raise ValueError("Pas autorisé à ouvrir le tiroir")

        movement = CashMovement(
            tenant_id=self.tenant_id,
            session_id=session_id,
            movement_type=data.movement_type,
            amount=data.amount,
            reason=data.reason,
            description=data.description,
            performed_by_id=performed_by_id
        )
        self.db.add(movement)
        self.db.commit()
        self.db.refresh(movement)
        return movement

    def list_cash_movements(self, session_id: int) -> list[CashMovement]:
        """Lister mouvements de caisse d'une session."""
        return self.db.query(CashMovement).filter(
            CashMovement.tenant_id == self.tenant_id,
            CashMovement.session_id == session_id
        ).order_by(CashMovement.created_at).all()

    # ========================================================================
    # TRANSACTIONS
    # ========================================================================

    def _generate_receipt_number(self, session_id: int) -> str:
        """Générer numéro de ticket."""
        today = date.today()
        prefix = f"T{today.strftime('%Y%m%d')}"

        last_tx = self.db.query(POSTransaction).filter(
            POSTransaction.tenant_id == self.tenant_id,
            POSTransaction.receipt_number.like(f"{prefix}%")
        ).order_by(POSTransaction.id.desc()).first()

        if last_tx:
            last_num = int(last_tx.receipt_number[-6:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:06d}"

    def create_transaction(
        self, session_id: int, data: TransactionCreate, cashier_id: int
    ) -> POSTransaction:
        """Créer une transaction."""
        logger.info(
            "Creating POS transaction | tenant=%s session_id=%s cashier_id=%s lines_count=%s",
            self.tenant_id, session_id, cashier_id, len(data.lines) if data.lines else 0
        )
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session introuvable")

        if session.status != POSSessionStatus.OPEN:
            raise ValueError("Session fermée")

        if not data.lines:
            raise ValueError("Transaction sans ligne")

        # Créer transaction
        transaction = POSTransaction(
            tenant_id=self.tenant_id,
            session_id=session_id,
            receipt_number=self._generate_receipt_number(session_id),
            status=POSTransactionStatus.PENDING,
            customer_id=data.customer_id,
            customer_name=data.customer_name,
            customer_email=data.customer_email,
            customer_phone=data.customer_phone,
            cashier_id=cashier_id,
            salesperson_id=data.salesperson_id,
            subtotal=Decimal("0"),
            discount_total=Decimal("0"),
            tax_total=Decimal("0"),
            total=Decimal("0"),
            amount_paid=Decimal("0"),
            amount_due=Decimal("0"),
            change_given=Decimal("0"),
            notes=data.notes
        )
        self.db.add(transaction)
        self.db.flush()

        # Ajouter lignes
        subtotal = Decimal("0")
        discount_total = Decimal("0")
        tax_total = Decimal("0")

        for line_data in data.lines:
            line = self._create_transaction_line(transaction.id, line_data)
            subtotal += line.line_total + line.discount_amount
            discount_total += line.discount_amount
            tax_total += line.tax_amount

        # Remise globale
        if data.discount_type and data.discount_value:
            if data.discount_type == DiscountType.PERCENTAGE:
                global_discount = subtotal * data.discount_value / 100
            else:
                global_discount = data.discount_value
            discount_total += global_discount
            transaction.discount_type = data.discount_type
            transaction.discount_value = data.discount_value
            transaction.discount_reason = data.discount_reason

        # Calculer totaux
        transaction.subtotal = subtotal
        transaction.discount_total = discount_total
        transaction.tax_total = tax_total
        transaction.total = subtotal - discount_total + tax_total
        transaction.amount_due = transaction.total

        # Ajouter paiements si fournis
        if data.payments:
            for payment_data in data.payments:
                self._create_payment(transaction.id, payment_data)

            # Recalculer amount_paid
            transaction.amount_paid = sum(
                p.amount for p in transaction.payments
                if p.status == "completed"
            )
            transaction.amount_due = transaction.total - transaction.amount_paid

            if transaction.amount_due <= 0:
                transaction.status = POSTransactionStatus.COMPLETED
                transaction.completed_at = datetime.utcnow()
                if transaction.amount_due < 0:
                    transaction.change_given = -transaction.amount_due
                    transaction.amount_due = Decimal("0")

        self.db.commit()
        self.db.refresh(transaction)
        logger.info(
            "POS transaction created | transaction_id=%s receipt_number=%s total=%s status=%s",
            transaction.id, transaction.receipt_number, transaction.total, transaction.status.value
        )
        return transaction

    def _create_transaction_line(
        self, transaction_id: int, data: TransactionLineCreate
    ) -> POSTransactionLine:
        """Créer une ligne de transaction."""
        # Calculer remise ligne
        line_subtotal = data.quantity * data.unit_price
        discount_amount = Decimal("0")

        if data.discount_type and data.discount_value:
            if data.discount_type == DiscountType.PERCENTAGE:
                discount_amount = line_subtotal * data.discount_value / 100
            else:
                discount_amount = min(data.discount_value, line_subtotal)

        # Calculer TVA
        line_total = line_subtotal - discount_amount
        tax_amount = line_total * data.tax_rate / 100 if not data.is_return else Decimal("0")

        # Ajuster pour retour
        if data.is_return:
            line_total = -line_total
            tax_amount = -tax_amount
            discount_amount = -discount_amount

        line = POSTransactionLine(
            tenant_id=self.tenant_id,
            transaction_id=transaction_id,
            line_number=1,  # Sera ajusté
            product_id=data.product_id,
            variant_id=data.variant_id,
            sku=data.sku,
            barcode=data.barcode,
            name=data.name,
            quantity=data.quantity if not data.is_return else -data.quantity,
            unit_price=data.unit_price,
            discount_type=data.discount_type,
            discount_value=data.discount_value,
            discount_amount=discount_amount,
            discount_reason=data.discount_reason,
            tax_rate=data.tax_rate,
            tax_amount=tax_amount,
            line_total=line_total,
            salesperson_id=data.salesperson_id,
            notes=data.notes,
            is_return=data.is_return,
            return_reason=data.return_reason
        )
        self.db.add(line)
        self.db.flush()
        return line

    def _create_payment(
        self, transaction_id: int, data: PaymentCreate
    ) -> POSPayment:
        """Créer un paiement."""
        change_amount = Decimal("0")
        if data.payment_method == PaymentMethodType.CASH and data.amount_tendered:
            if data.amount_tendered > data.amount:
                change_amount = data.amount_tendered - data.amount

        payment = POSPayment(
            tenant_id=self.tenant_id,
            transaction_id=transaction_id,
            payment_method=data.payment_method,
            amount=data.amount,
            amount_tendered=data.amount_tendered,
            change_amount=change_amount,
            card_type=data.card_type,
            card_last4=data.card_last4,
            card_auth_code=data.card_auth_code,
            check_number=data.check_number,
            check_bank=data.check_bank,
            gift_card_number=data.gift_card_number,
            status="completed"
        )
        self.db.add(payment)
        self.db.flush()
        return payment

    def get_transaction(self, transaction_id: int) -> POSTransaction | None:
        """Récupérer une transaction."""
        return self.db.query(POSTransaction).filter(
            POSTransaction.tenant_id == self.tenant_id,
            POSTransaction.id == transaction_id
        ).first()

    def get_transaction_by_receipt(
        self, receipt_number: str
    ) -> POSTransaction | None:
        """Récupérer transaction par numéro ticket."""
        return self.db.query(POSTransaction).filter(
            POSTransaction.tenant_id == self.tenant_id,
            POSTransaction.receipt_number == receipt_number
        ).first()

    def list_transactions(
        self,
        session_id: int | None = None,
        status: POSTransactionStatus | None = None,
        customer_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[list[POSTransaction], int]:
        """Lister les transactions."""
        query = self.db.query(POSTransaction).filter(
            POSTransaction.tenant_id == self.tenant_id
        )
        if session_id:
            query = query.filter(POSTransaction.session_id == session_id)
        if status:
            query = query.filter(POSTransaction.status == status)
        if customer_id:
            query = query.filter(POSTransaction.customer_id == customer_id)
        if date_from:
            query = query.filter(POSTransaction.created_at >= datetime.combine(date_from, datetime.min.time()))
        if date_to:
            query = query.filter(POSTransaction.created_at <= datetime.combine(date_to, datetime.max.time()))

        total = query.count()
        items = query.order_by(POSTransaction.created_at.desc()).offset(skip).limit(limit).all()
        return items, total

    def add_payment(
        self, transaction_id: int, data: PaymentCreate
    ) -> POSTransaction:
        """Ajouter un paiement à une transaction."""
        logger.info(
            "Processing payment | tenant=%s transaction_id=%s method=%s amount=%s",
            self.tenant_id, transaction_id, data.payment_method.value, data.amount
        )
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError("Transaction introuvable")

        if transaction.status == POSTransactionStatus.COMPLETED:
            raise ValueError("Transaction déjà payée")

        if transaction.status == POSTransactionStatus.VOIDED:
            raise ValueError("Transaction annulée")

        # Créer paiement
        payment = self._create_payment(transaction_id, data)

        # Mettre à jour transaction
        transaction.amount_paid += payment.amount
        transaction.amount_due = max(
            Decimal("0"), transaction.total - transaction.amount_paid
        )

        if transaction.amount_due <= 0:
            transaction.status = POSTransactionStatus.COMPLETED
            transaction.completed_at = datetime.utcnow()
            if transaction.amount_paid > transaction.total:
                transaction.change_given = transaction.amount_paid - transaction.total

            # Mettre à jour session
            self._update_session_totals(transaction)

        self.db.commit()
        self.db.refresh(transaction)
        logger.info(
            "Payment processed | transaction_id=%s amount_paid=%s amount_due=%s status=%s",
            transaction.id, transaction.amount_paid, transaction.amount_due, transaction.status.value
        )
        return transaction

    def _update_session_totals(self, transaction: POSTransaction):
        """Mettre à jour totaux session après transaction complétée."""
        session = self.get_session(transaction.session_id)
        if not session:
            return

        # Ventes ou remboursements
        tx_total = transaction.total or Decimal("0")
        if tx_total >= 0:
            session.total_sales = (session.total_sales or Decimal("0")) + tx_total
        else:
            session.total_refunds = (session.total_refunds or Decimal("0")) + abs(tx_total)

        session.total_discounts = (session.total_discounts or Decimal("0")) + (transaction.discount_total or Decimal("0"))
        session.transaction_count = (session.transaction_count or 0) + 1

        # Par mode de paiement
        payments = getattr(transaction, 'payments', None) or []
        for payment in payments:
            if payment.status == "completed":
                amount = payment.amount or Decimal("0")
                if payment.payment_method == PaymentMethodType.CASH:
                    session.cash_total = (session.cash_total or Decimal("0")) + amount
                elif payment.payment_method == PaymentMethodType.CARD:
                    session.card_total = (session.card_total or Decimal("0")) + amount
                elif payment.payment_method == PaymentMethodType.CHECK:
                    session.check_total = (session.check_total or Decimal("0")) + amount
                elif payment.payment_method == PaymentMethodType.VOUCHER:
                    session.voucher_total = (session.voucher_total or Decimal("0")) + amount
                else:
                    session.other_total = (session.other_total or Decimal("0")) + amount

    def void_transaction(
        self, transaction_id: int, reason: str, voided_by_id: int
    ) -> POSTransaction:
        """Annuler une transaction."""
        logger.info(
            "Voiding POS transaction | tenant=%s transaction_id=%s voided_by=%s reason=%s",
            self.tenant_id, transaction_id, voided_by_id, reason
        )
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            raise ValueError("Transaction introuvable")

        if transaction.status == POSTransactionStatus.VOIDED:
            raise ValueError("Transaction déjà annulée")

        # Vérifier permissions
        user = self.get_pos_user(voided_by_id)
        if not user:
            raise ValueError("Utilisateur introuvable")

        if not user.can_void_transaction and not user.is_manager:
            raise ValueError("Pas autorisé à annuler des transactions")

        # Annuler
        transaction.status = POSTransactionStatus.VOIDED
        transaction.void_reason = reason
        transaction.voided_by_id = voided_by_id
        transaction.voided_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(transaction)
        logger.info(
            "POS transaction voided | transaction_id=%s receipt_number=%s",
            transaction.id, transaction.receipt_number
        )
        return transaction

    def refund_transaction(
        self, original_transaction_id: int, line_items: list[dict],
        session_id: int, cashier_id: int, reason: str
    ) -> POSTransaction:
        """Créer un remboursement."""
        logger.info(
            "Processing refund | tenant=%s original_transaction_id=%s cashier_id=%s lines_count=%s reason=%s",
            self.tenant_id, original_transaction_id, cashier_id, len(line_items), reason
        )
        original = self.get_transaction(original_transaction_id)
        if not original:
            raise ValueError("Transaction originale introuvable")

        # Vérifier permissions
        user = self.get_pos_user(cashier_id)
        if not user:
            raise ValueError("Utilisateur introuvable")

        if not user.can_refund and not user.is_manager:
            raise ValueError("Pas autorisé à rembourser")

        # SÉCURITÉ: Créer lignes de remboursement (filtrer par tenant_id)
        refund_lines = []
        for item in line_items:
            original_line = self.db.query(POSTransactionLine).filter(
                POSTransactionLine.tenant_id == self.tenant_id,
                POSTransactionLine.id == item["line_id"]
            ).first()
            if not original_line:
                continue

            refund_lines.append(TransactionLineCreate(
                product_id=original_line.product_id,
                variant_id=original_line.variant_id,
                sku=original_line.sku,
                barcode=original_line.barcode,
                name=original_line.name,
                quantity=Decimal(str(item.get("quantity", original_line.quantity))),
                unit_price=original_line.unit_price,
                tax_rate=original_line.tax_rate,
                is_return=True,
                return_reason=reason
            ))

        if not refund_lines:
            raise ValueError("Aucune ligne à rembourser")

        # Créer transaction de remboursement
        refund_data = TransactionCreate(
            customer_id=original.customer_id,
            customer_name=original.customer_name,
            notes=f"Remboursement de {original.receipt_number}: {reason}",
            lines=refund_lines
        )

        refund = self.create_transaction(session_id, refund_data, cashier_id)
        refund.original_transaction_id = original_transaction_id

        self.db.commit()
        self.db.refresh(refund)
        logger.info(
            "Refund processed | refund_transaction_id=%s receipt_number=%s original_transaction_id=%s total=%s",
            refund.id, refund.receipt_number, original_transaction_id, refund.total
        )
        return refund

    # ========================================================================
    # QUICK KEYS
    # ========================================================================

    def create_quick_key(self, data: QuickKeyCreate) -> POSProductQuickKey:
        """Créer un raccourci produit."""
        # Vérifier position disponible
        existing = self.db.query(POSProductQuickKey).filter(
            POSProductQuickKey.tenant_id == self.tenant_id,
            POSProductQuickKey.store_id == data.store_id,
            POSProductQuickKey.page == data.page,
            POSProductQuickKey.position == data.position
        ).first()

        if existing:
            raise ValueError(f"Position {data.position} déjà utilisée sur page {data.page}")

        quick_key = POSProductQuickKey(
            tenant_id=self.tenant_id,
            **data.model_dump()
        )
        self.db.add(quick_key)
        self.db.commit()
        self.db.refresh(quick_key)
        return quick_key

    def list_quick_keys(
        self, store_id: int | None = None, page: int = 1
    ) -> list[POSProductQuickKey]:
        """Lister raccourcis."""
        query = self.db.query(POSProductQuickKey).filter(
            POSProductQuickKey.tenant_id == self.tenant_id,
            POSProductQuickKey.page == page
        )
        if store_id:
            query = query.filter(
                or_(
                    POSProductQuickKey.store_id == store_id,
                    POSProductQuickKey.store_id is None
                )
            )
        else:
            query = query.filter(POSProductQuickKey.store_id is None)

        return query.order_by(POSProductQuickKey.position).all()

    def delete_quick_key(self, quick_key_id: int) -> bool:
        """Supprimer un raccourci."""
        quick_key = self.db.query(POSProductQuickKey).filter(
            POSProductQuickKey.tenant_id == self.tenant_id,
            POSProductQuickKey.id == quick_key_id
        ).first()

        if not quick_key:
            return False

        self.db.delete(quick_key)
        self.db.commit()
        return True

    # ========================================================================
    # HOLD TRANSACTIONS
    # ========================================================================

    def _generate_hold_number(self) -> str:
        """Générer numéro d'attente."""
        today = date.today()
        prefix = f"H{today.strftime('%Y%m%d')}"

        last = self.db.query(POSHoldTransaction).filter(
            POSHoldTransaction.tenant_id == self.tenant_id,
            POSHoldTransaction.hold_number.like(f"{prefix}%")
        ).order_by(POSHoldTransaction.id.desc()).first()

        if last:
            last_num = int(last.hold_number[-4:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:04d}"

    def hold_transaction(
        self, session_id: int, data: HoldTransactionCreate, held_by_id: int
    ) -> POSHoldTransaction:
        """Mettre une transaction en attente."""
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session introuvable")

        hold = POSHoldTransaction(
            tenant_id=self.tenant_id,
            session_id=session_id,
            hold_number=self._generate_hold_number(),
            hold_name=data.hold_name,
            customer_id=data.customer_id,
            customer_name=data.customer_name,
            transaction_data=data.transaction_data,
            held_by_id=held_by_id,
            is_active=True
        )
        self.db.add(hold)
        self.db.commit()
        self.db.refresh(hold)
        return hold

    def list_held_transactions(
        self, session_id: int | None = None
    ) -> list[POSHoldTransaction]:
        """Lister transactions en attente."""
        query = self.db.query(POSHoldTransaction).filter(
            POSHoldTransaction.tenant_id == self.tenant_id,
            POSHoldTransaction.is_active
        )
        if session_id:
            query = query.filter(POSHoldTransaction.session_id == session_id)
        return query.order_by(POSHoldTransaction.created_at.desc()).all()

    def recall_held_transaction(self, hold_id: int) -> dict | None:
        """Récupérer et supprimer transaction en attente."""
        hold = self.db.query(POSHoldTransaction).filter(
            POSHoldTransaction.tenant_id == self.tenant_id,
            POSHoldTransaction.id == hold_id,
            POSHoldTransaction.is_active
        ).first()

        if not hold:
            return None

        data = hold.transaction_data
        hold.is_active = False
        self.db.commit()
        return data

    # ========================================================================
    # DAILY REPORTS (Z-Report)
    # ========================================================================

    def _generate_report_number(self, store_id: int) -> str:
        """Générer numéro de rapport."""
        today = date.today()
        prefix = f"Z{today.strftime('%Y%m%d')}"

        last = self.db.query(POSDailyReport).filter(
            POSDailyReport.tenant_id == self.tenant_id,
            POSDailyReport.store_id == store_id,
            POSDailyReport.report_number.like(f"{prefix}%")
        ).order_by(POSDailyReport.id.desc()).first()

        if last:
            last_num = int(last.report_number[-2:])
            new_num = last_num + 1
        else:
            new_num = 1

        return f"{prefix}{new_num:02d}"

    def generate_daily_report(
        self, store_id: int, report_date: date
    ) -> POSDailyReport:
        """Générer rapport journalier (Z-Report)."""
        store = self.get_store(store_id)
        if not store:
            raise ValueError("Magasin introuvable")

        # Récupérer tous les terminaux du magasin
        terminals = self.list_terminals(store_id=store_id)
        terminal_ids = [t.id for t in terminals]

        # Récupérer sessions fermées du jour
        start = datetime.combine(report_date, datetime.min.time())
        end = datetime.combine(report_date, datetime.max.time())

        sessions = self.db.query(POSSession).filter(
            POSSession.tenant_id == self.tenant_id,
            POSSession.terminal_id.in_(terminal_ids),
            POSSession.opened_at >= start,
            POSSession.opened_at <= end,
            POSSession.status == POSSessionStatus.CLOSED
        ).all()

        if not sessions:
            raise ValueError("Aucune session fermée pour ce jour")

        # Agréger données
        gross_sales = Decimal("0")
        total_discounts = Decimal("0")
        total_refunds = Decimal("0")
        total_tax = Decimal("0")
        transaction_count = 0
        items_sold = 0
        cash_total = Decimal("0")
        card_total = Decimal("0")
        check_total = Decimal("0")
        opening_cash = Decimal("0")
        closing_cash = Decimal("0")

        for session in sessions:
            gross_sales += session.total_sales
            total_discounts += session.total_discounts
            total_refunds += session.total_refunds
            transaction_count += session.transaction_count
            cash_total += session.cash_total
            card_total += session.card_total
            check_total += session.check_total
            opening_cash += session.opening_cash
            closing_cash += session.actual_cash or Decimal("0")

            # Compter articles vendus
            tx_count = self.db.query(func.sum(POSTransactionLine.quantity)).join(
                POSTransaction
            ).filter(
                POSTransaction.session_id == session.id,
                POSTransaction.status == POSTransactionStatus.COMPLETED,
                POSTransactionLine.quantity > 0
            ).scalar() or 0
            items_sold += int(tx_count)

            # Total TVA
            tax = self.db.query(func.sum(POSTransactionLine.tax_amount)).join(
                POSTransaction
            ).filter(
                POSTransaction.session_id == session.id,
                POSTransaction.status == POSTransactionStatus.COMPLETED
            ).scalar() or Decimal("0")
            total_tax += tax

        net_sales = gross_sales - total_discounts - total_refunds
        average_transaction = (
            net_sales / transaction_count if transaction_count > 0
            else Decimal("0")
        )
        cash_variance = closing_cash - (opening_cash + cash_total - total_refunds)

        # Créer rapport
        report = POSDailyReport(
            tenant_id=self.tenant_id,
            store_id=store_id,
            report_date=report_date,
            report_number=self._generate_report_number(store_id),
            gross_sales=gross_sales,
            net_sales=net_sales,
            total_discounts=total_discounts,
            total_refunds=total_refunds,
            total_tax=total_tax,
            transaction_count=transaction_count,
            items_sold=items_sold,
            average_transaction=average_transaction,
            cash_total=cash_total,
            card_total=card_total,
            check_total=check_total,
            opening_cash=opening_cash,
            closing_cash=closing_cash,
            cash_variance=cash_variance,
            generated_at=datetime.utcnow()
        )
        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)
        return report

    def get_daily_report(
        self, store_id: int, report_date: date
    ) -> POSDailyReport | None:
        """Récupérer rapport journalier."""
        return self.db.query(POSDailyReport).filter(
            POSDailyReport.tenant_id == self.tenant_id,
            POSDailyReport.store_id == store_id,
            POSDailyReport.report_date == report_date
        ).first()

    def list_daily_reports(
        self,
        store_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        skip: int = 0,
        limit: int = 30
    ) -> list[POSDailyReport]:
        """Lister rapports journaliers."""
        query = self.db.query(POSDailyReport).filter(
            POSDailyReport.tenant_id == self.tenant_id
        )
        if store_id:
            query = query.filter(POSDailyReport.store_id == store_id)
        if date_from:
            query = query.filter(POSDailyReport.report_date >= date_from)
        if date_to:
            query = query.filter(POSDailyReport.report_date <= date_to)

        return query.order_by(POSDailyReport.report_date.desc()).offset(skip).limit(limit).all()

    # ========================================================================
    # DASHBOARDS
    # ========================================================================

    def get_pos_dashboard(self, store_id: int | None = None) -> dict:
        """Dashboard POS global."""
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())

        # Filtrer par magasin si spécifié
        terminal_filter = []
        if store_id:
            terminals = self.list_terminals(store_id=store_id)
            terminal_filter = [t.id for t in terminals]

        # Transactions du jour
        tx_query = self.db.query(POSTransaction).filter(
            POSTransaction.tenant_id == self.tenant_id,
            POSTransaction.status == POSTransactionStatus.COMPLETED,
            POSTransaction.created_at >= start,
            POSTransaction.created_at <= end
        )
        if terminal_filter:
            tx_query = tx_query.join(POSSession).filter(
                POSSession.terminal_id.in_(terminal_filter)
            )

        transactions = tx_query.all()

        sales_today = sum(t.total for t in transactions if t.total > 0)
        transactions_today = len(transactions)
        avg_transaction = (
            sales_today / transactions_today if transactions_today > 0
            else Decimal("0")
        )

        # Articles vendus
        items_query = self.db.query(func.sum(POSTransactionLine.quantity)).join(
            POSTransaction
        ).filter(
            POSTransaction.tenant_id == self.tenant_id,
            POSTransaction.status == POSTransactionStatus.COMPLETED,
            POSTransaction.created_at >= start,
            POSTransaction.created_at <= end,
            POSTransactionLine.quantity > 0
        )
        if terminal_filter:
            items_query = items_query.join(
                POSSession, POSTransaction.session_id == POSSession.id
            ).filter(POSSession.terminal_id.in_(terminal_filter))

        items_sold = int(items_query.scalar() or 0)

        # Sessions actives
        active_sessions = self.db.query(POSSession).filter(
            POSSession.tenant_id == self.tenant_id,
            POSSession.status == POSSessionStatus.OPEN
        )
        if terminal_filter:
            active_sessions = active_sessions.filter(
                POSSession.terminal_id.in_(terminal_filter)
            )
        active_count = active_sessions.count()

        # Terminaux actifs
        active_terminals = self.db.query(POSTerminal).filter(
            POSTerminal.tenant_id == self.tenant_id,
            POSTerminal.status.in_([POSTerminalStatus.ONLINE, POSTerminalStatus.IN_USE])
        )
        if store_id:
            active_terminals = active_terminals.filter(
                POSTerminal.store_id == store_id
            )
        terminal_count = active_terminals.count()

        # Par mode de paiement
        cash_today = Decimal("0")
        card_today = Decimal("0")
        other_today = Decimal("0")

        for tx in transactions:
            for payment in tx.payments:
                if payment.status == "completed":
                    if payment.payment_method == PaymentMethodType.CASH:
                        cash_today += payment.amount
                    elif payment.payment_method == PaymentMethodType.CARD:
                        card_today += payment.amount
                    else:
                        other_today += payment.amount

        # Top produits
        top_products_query = self.db.query(
            POSTransactionLine.name,
            func.sum(POSTransactionLine.quantity).label("qty"),
            func.sum(POSTransactionLine.line_total).label("total")
        ).join(POSTransaction).filter(
            POSTransaction.tenant_id == self.tenant_id,
            POSTransaction.status == POSTransactionStatus.COMPLETED,
            POSTransaction.created_at >= start,
            POSTransaction.created_at <= end,
            POSTransactionLine.quantity > 0
        ).group_by(POSTransactionLine.name).order_by(
            func.sum(POSTransactionLine.line_total).desc()
        ).limit(5)

        top_products = [
            {"name": p.name, "quantity": float(p.qty), "total": float(p.total)}
            for p in top_products_query.all()
        ]

        # Dernières transactions
        recent = tx_query.order_by(
            POSTransaction.created_at.desc()
        ).limit(5).all()

        recent_transactions = [
            {
                "id": t.id,
                "receipt_number": t.receipt_number,
                "total": float(t.total),
                "created_at": t.created_at.isoformat()
            }
            for t in recent
        ]

        return {
            "sales_today": float(sales_today),
            "transactions_today": transactions_today,
            "average_transaction_today": float(avg_transaction),
            "items_sold_today": items_sold,
            "active_sessions": active_count,
            "active_terminals": terminal_count,
            "cash_today": float(cash_today),
            "card_today": float(card_today),
            "other_today": float(other_today),
            "top_products": top_products,
            "recent_transactions": recent_transactions
        }

    def get_terminal_dashboard(self, terminal_id: int) -> dict:
        """Dashboard d'un terminal."""
        terminal = self.get_terminal(terminal_id)
        if not terminal:
            raise ValueError("Terminal introuvable")

        session = self.get_current_session(terminal_id)

        result = {
            "terminal_id": terminal.id,
            "terminal_name": terminal.name,
            "session_status": session.status.value if session else None,
            "session_id": session.id if session else None,
            "cashier_name": None,
            "sales_this_session": Decimal("0"),
            "transactions_this_session": 0,
            "last_transaction": None
        }

        if session:
            # Caissier
            cashier = self.get_pos_user(session.opened_by_id)
            if cashier:
                result["cashier_name"] = f"{cashier.first_name} {cashier.last_name}"

            result["sales_this_session"] = float(session.total_sales)
            result["transactions_this_session"] = session.transaction_count

            # SÉCURITÉ: Dernière transaction (filtrer par tenant_id)
            last_tx = self.db.query(POSTransaction).filter(
                POSTransaction.tenant_id == self.tenant_id,
                POSTransaction.session_id == session.id
            ).order_by(POSTransaction.created_at.desc()).first()

            if last_tx:
                result["last_transaction"] = {
                    "id": last_tx.id,
                    "receipt_number": last_tx.receipt_number,
                    "total": float(last_tx.total),
                    "status": last_tx.status.value,
                    "created_at": last_tx.created_at.isoformat()
                }

        return result

    # ========================================================================
    # OFFLINE QUEUE
    # ========================================================================

    def queue_offline_transaction(
        self, terminal_id: int, transaction_data: dict
    ) -> POSOfflineQueue:
        """Mettre en file une transaction offline."""
        queue_item = POSOfflineQueue(
            tenant_id=self.tenant_id,
            terminal_id=terminal_id,
            transaction_data=transaction_data,
            is_synced=False
        )
        self.db.add(queue_item)
        self.db.commit()
        self.db.refresh(queue_item)
        return queue_item

    def sync_offline_transactions(self, terminal_id: int) -> int:
        """Synchroniser transactions offline."""
        pending = self.db.query(POSOfflineQueue).filter(
            POSOfflineQueue.tenant_id == self.tenant_id,
            POSOfflineQueue.terminal_id == terminal_id,
            not POSOfflineQueue.is_synced
        ).order_by(POSOfflineQueue.created_at).all()

        synced_count = 0
        for item in pending:
            try:
                # Traiter transaction
                data = item.transaction_data
                session_id = data.get("session_id")
                cashier_id = data.get("cashier_id")
                tx_data = TransactionCreate(**data.get("transaction", {}))

                self.create_transaction(session_id, tx_data, cashier_id)

                item.is_synced = True
                item.synced_at = datetime.utcnow()
                synced_count += 1
            except Exception as e:
                item.sync_error = str(e)

        self.db.commit()
        return synced_count
