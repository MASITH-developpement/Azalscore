"""
AZALS MODULE M7 - Service Qualité
=================================

Logique métier pour le module de gestion de la qualité.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session, joinedload

from app.modules.quality.models import (
    CAPA,
    AuditFinding,
    AuditStatus,
    AuditType,
    CAPAAction,
    CAPAStatus,
    CAPAType,
    Certification,
    CertificationAudit,
    CertificationStatus,
    ClaimAction,
    ClaimStatus,
    ControlResult,
    ControlStatus,
    ControlType,
    CustomerClaim,
    FindingSeverity,
    IndicatorMeasurement,
    NonConformance,
    NonConformanceAction,
    NonConformanceSeverity,
    NonConformanceStatus,
    NonConformanceType,
    QualityAudit,
    QualityControl,
    QualityControlLine,
    QualityControlTemplate,
    QualityControlTemplateItem,
    QualityIndicator,
)
from app.modules.quality.schemas import (
    AuditClose,
    AuditCreate,
    AuditFindingCreate,
    AuditFindingUpdate,
    AuditUpdate,
    CAPAActionCreate,
    CAPAActionUpdate,
    CAPAClose,
    CAPACreate,
    CAPAUpdate,
    CertificationAuditCreate,
    CertificationAuditUpdate,
    CertificationCreate,
    CertificationUpdate,
    ClaimActionCreate,
    ClaimClose,
    ClaimCreate,
    ClaimResolve,
    ClaimRespond,
    ClaimUpdate,
    ControlCreate,
    ControlLineUpdate,
    ControlTemplateCreate,
    ControlTemplateItemCreate,
    ControlTemplateUpdate,
    ControlUpdate,
    IndicatorCreate,
    IndicatorMeasurementCreate,
    IndicatorUpdate,
    NonConformanceActionCreate,
    NonConformanceActionUpdate,
    NonConformanceClose,
    NonConformanceCreate,
    NonConformanceUpdate,
    QualityDashboard,
)


class QualityService:
    """Service de gestion de la qualité"""

    def __init__(self, db: Session, tenant_id: int, user_id: int = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2 (déjà existant, juste rendre optionnel)

    # ========================================================================
    # NON-CONFORMITÉS
    # ========================================================================

    def _generate_nc_number(self) -> str:
        """Génère un numéro de non-conformité"""
        year = datetime.now().year
        count = self.db.query(func.count(NonConformance.id)).filter(
            NonConformance.tenant_id == self.tenant_id,
            func.extract("year", NonConformance.created_at) == year
        ).scalar() or 0
        return f"NC-{year}-{count + 1:05d}"

    def create_non_conformance(self, data: NonConformanceCreate) -> NonConformance:
        """Crée une nouvelle non-conformité"""
        nc = NonConformance(
            tenant_id=self.tenant_id,
            nc_number=self._generate_nc_number(),
            title=data.title,
            description=data.description,
            nc_type=data.nc_type,
            severity=data.severity,
            status=NonConformanceStatus.DRAFT,
            detected_date=data.detected_date,
            detected_by_id=self.user_id,
            detection_location=data.detection_location,
            detection_phase=data.detection_phase,
            source_type=data.source_type,
            source_reference=data.source_reference,
            source_id=data.source_id,
            product_id=data.product_id,
            lot_number=data.lot_number,
            serial_number=data.serial_number,
            quantity_affected=data.quantity_affected,
            unit_id=data.unit_id,
            supplier_id=data.supplier_id,
            customer_id=data.customer_id,
            immediate_action=data.immediate_action,
            responsible_id=data.responsible_id,
            department=data.department,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(nc)
        self.db.commit()
        self.db.refresh(nc)
        return nc

    def get_non_conformance(self, nc_id: int) -> NonConformance | None:
        """Récupère une non-conformité par ID"""
        return self.db.query(NonConformance).options(
            joinedload(NonConformance.actions)
        ).filter(
            NonConformance.id == nc_id,
            NonConformance.tenant_id == self.tenant_id
        ).first()

    def get_non_conformance_by_number(self, nc_number: str) -> NonConformance | None:
        """Récupère une non-conformité par numéro"""
        return self.db.query(NonConformance).options(
            joinedload(NonConformance.actions)
        ).filter(
            NonConformance.nc_number == nc_number,
            NonConformance.tenant_id == self.tenant_id
        ).first()

    def list_non_conformances(
        self,
        skip: int = 0,
        limit: int = 50,
        nc_type: NonConformanceType | None = None,
        status: NonConformanceStatus | None = None,
        severity: NonConformanceSeverity | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
    ) -> tuple[list[NonConformance], int]:
        """Liste les non-conformités avec filtres"""
        query = self.db.query(NonConformance).filter(
            NonConformance.tenant_id == self.tenant_id
        )

        if nc_type:
            query = query.filter(NonConformance.nc_type == nc_type)
        if status:
            query = query.filter(NonConformance.status == status)
        if severity:
            query = query.filter(NonConformance.severity == severity)
        if date_from:
            query = query.filter(NonConformance.detected_date >= date_from)
        if date_to:
            query = query.filter(NonConformance.detected_date <= date_to)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    NonConformance.nc_number.ilike(search_filter),
                    NonConformance.title.ilike(search_filter),
                    NonConformance.description.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(joinedload(NonConformance.actions)).order_by(
            desc(NonConformance.detected_date)
        ).offset(skip).limit(limit).all()

        return items, total

    def update_non_conformance(
        self, nc_id: int, data: NonConformanceUpdate
    ) -> NonConformance | None:
        """Met à jour une non-conformité"""
        nc = self.get_non_conformance(nc_id)
        if not nc:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(nc, field, value)

        nc.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(nc)
        return nc

    def open_non_conformance(self, nc_id: int) -> NonConformance | None:
        """Ouvre une non-conformité"""
        nc = self.get_non_conformance(nc_id)
        if not nc or nc.status != NonConformanceStatus.DRAFT:
            return None

        nc.status = NonConformanceStatus.OPEN
        nc.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(nc)
        return nc

    def close_non_conformance(
        self, nc_id: int, data: NonConformanceClose
    ) -> NonConformance | None:
        """Clôture une non-conformité"""
        nc = self.get_non_conformance(nc_id)
        if not nc:
            return None

        nc.status = NonConformanceStatus.CLOSED
        nc.closed_date = date.today()
        nc.closed_by_id = self.user_id
        nc.closure_justification = data.closure_justification
        nc.effectiveness_verified = data.effectiveness_verified
        if data.effectiveness_verified:
            nc.effectiveness_date = date.today()

        nc.updated_by = self.user_id
        self.db.commit()
        self.db.refresh(nc)
        return nc

    def add_nc_action(
        self, nc_id: int, data: NonConformanceActionCreate
    ) -> NonConformanceAction | None:
        """Ajoute une action à une non-conformité"""
        nc = self.get_non_conformance(nc_id)
        if not nc:
            return None

        # Numéro d'action
        action_count = self.db.query(func.count(NonConformanceAction.id)).filter(
            NonConformanceAction.nc_id == nc_id
        ).scalar() or 0

        action = NonConformanceAction(
            tenant_id=self.tenant_id,
            nc_id=nc_id,
            action_number=action_count + 1,
            action_type=data.action_type,
            description=data.description,
            responsible_id=data.responsible_id,
            planned_date=data.planned_date,
            due_date=data.due_date,
            status="PLANNED",
            comments=data.comments,
            created_by=self.user_id,
        )
        self.db.add(action)

        # Mettre à jour statut NC si nécessaire
        if nc.status == NonConformanceStatus.OPEN:
            nc.status = NonConformanceStatus.ACTION_REQUIRED
            nc.updated_by = self.user_id

        self.db.commit()
        self.db.refresh(action)
        return action

    def update_nc_action(
        self, action_id: int, data: NonConformanceActionUpdate
    ) -> NonConformanceAction | None:
        """Met à jour une action de non-conformité"""
        action = self.db.query(NonConformanceAction).filter(
            NonConformanceAction.id == action_id,
            NonConformanceAction.tenant_id == self.tenant_id
        ).first()
        if not action:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(action, field, value)

        self.db.commit()
        self.db.refresh(action)
        return action

    # ========================================================================
    # TEMPLATES DE CONTRÔLE QUALITÉ
    # ========================================================================

    def create_control_template(
        self, data: ControlTemplateCreate
    ) -> QualityControlTemplate:
        """Crée un template de contrôle qualité"""
        template = QualityControlTemplate(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            version=data.version,
            control_type=data.control_type,
            applies_to=data.applies_to,
            product_category_id=data.product_category_id,
            instructions=data.instructions,
            sampling_plan=data.sampling_plan,
            acceptance_criteria=data.acceptance_criteria,
            estimated_duration_minutes=data.estimated_duration_minutes,
            required_equipment=data.required_equipment,
            is_active=True,
            created_by=self.user_id,
        )
        self.db.add(template)
        self.db.flush()

        # Ajouter les items
        if data.items:
            for item_data in data.items:
                item = QualityControlTemplateItem(
                    tenant_id=self.tenant_id,
                    template_id=template.id,
                    sequence=item_data.sequence,
                    characteristic=item_data.characteristic,
                    description=item_data.description,
                    measurement_type=item_data.measurement_type,
                    unit=item_data.unit,
                    nominal_value=item_data.nominal_value,
                    tolerance_min=item_data.tolerance_min,
                    tolerance_max=item_data.tolerance_max,
                    expected_result=item_data.expected_result,
                    measurement_method=item_data.measurement_method,
                    equipment_code=item_data.equipment_code,
                    is_critical=item_data.is_critical,
                    is_mandatory=item_data.is_mandatory,
                    sampling_frequency=item_data.sampling_frequency,
                )
                self.db.add(item)

        self.db.commit()
        self.db.refresh(template)
        return template

    def get_control_template(self, template_id: int) -> QualityControlTemplate | None:
        """Récupère un template par ID"""
        return self.db.query(QualityControlTemplate).options(
            joinedload(QualityControlTemplate.items)
        ).filter(
            QualityControlTemplate.id == template_id,
            QualityControlTemplate.tenant_id == self.tenant_id
        ).first()

    def list_control_templates(
        self,
        skip: int = 0,
        limit: int = 50,
        control_type: ControlType | None = None,
        active_only: bool = True,
        search: str | None = None,
    ) -> tuple[list[QualityControlTemplate], int]:
        """Liste les templates de contrôle"""
        query = self.db.query(QualityControlTemplate).filter(
            QualityControlTemplate.tenant_id == self.tenant_id
        )

        if control_type:
            query = query.filter(QualityControlTemplate.control_type == control_type)
        if active_only:
            query = query.filter(QualityControlTemplate.is_active)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    QualityControlTemplate.code.ilike(search_filter),
                    QualityControlTemplate.name.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(joinedload(QualityControlTemplate.items)).order_by(
            QualityControlTemplate.code
        ).offset(skip).limit(limit).all()

        return items, total

    def update_control_template(
        self, template_id: int, data: ControlTemplateUpdate
    ) -> QualityControlTemplate | None:
        """Met à jour un template"""
        template = self.get_control_template(template_id)
        if not template:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)

        self.db.commit()
        self.db.refresh(template)
        return template

    def add_template_item(
        self, template_id: int, data: ControlTemplateItemCreate
    ) -> QualityControlTemplateItem | None:
        """Ajoute un item à un template"""
        template = self.get_control_template(template_id)
        if not template:
            return None

        item = QualityControlTemplateItem(
            tenant_id=self.tenant_id,
            template_id=template_id,
            sequence=data.sequence,
            characteristic=data.characteristic,
            description=data.description,
            measurement_type=data.measurement_type,
            unit=data.unit,
            nominal_value=data.nominal_value,
            tolerance_min=data.tolerance_min,
            tolerance_max=data.tolerance_max,
            expected_result=data.expected_result,
            measurement_method=data.measurement_method,
            equipment_code=data.equipment_code,
            is_critical=data.is_critical,
            is_mandatory=data.is_mandatory,
            sampling_frequency=data.sampling_frequency,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    # ========================================================================
    # CONTRÔLES QUALITÉ
    # ========================================================================

    def _generate_control_number(self) -> str:
        """Génère un numéro de contrôle"""
        year = datetime.now().year
        count = self.db.query(func.count(QualityControl.id)).filter(
            QualityControl.tenant_id == self.tenant_id,
            func.extract("year", QualityControl.created_at) == year
        ).scalar() or 0
        return f"QC-{year}-{count + 1:05d}"

    def create_control(self, data: ControlCreate) -> QualityControl:
        """Crée un contrôle qualité"""
        control = QualityControl(
            tenant_id=self.tenant_id,
            control_number=self._generate_control_number(),
            template_id=data.template_id,
            control_type=data.control_type,
            source_type=data.source_type,
            source_reference=data.source_reference,
            source_id=data.source_id,
            product_id=data.product_id,
            lot_number=data.lot_number,
            serial_number=data.serial_number,
            quantity_to_control=data.quantity_to_control,
            unit_id=data.unit_id,
            supplier_id=data.supplier_id,
            customer_id=data.customer_id,
            control_date=data.control_date,
            start_time=datetime.now(),
            location=data.location,
            controller_id=data.controller_id or self.user_id,
            status=ControlStatus.PLANNED,
            observations=data.observations,
            created_by=self.user_id,
        )
        self.db.add(control)
        self.db.flush()

        # Créer les lignes depuis le template si spécifié
        if data.template_id:
            template = self.get_control_template(data.template_id)
            if template and template.items:
                for item in template.items:
                    line = QualityControlLine(
                        tenant_id=self.tenant_id,
                        control_id=control.id,
                        template_item_id=item.id,
                        sequence=item.sequence,
                        characteristic=item.characteristic,
                        nominal_value=item.nominal_value,
                        tolerance_min=item.tolerance_min,
                        tolerance_max=item.tolerance_max,
                        unit=item.unit,
                        result=ControlResult.PENDING,
                        created_by=self.user_id,
                    )
                    self.db.add(line)

        # Ou créer les lignes passées en paramètre
        elif data.lines:
            for line_data in data.lines:
                line = QualityControlLine(
                    tenant_id=self.tenant_id,
                    control_id=control.id,
                    template_item_id=line_data.template_item_id,
                    sequence=line_data.sequence,
                    characteristic=line_data.characteristic,
                    nominal_value=line_data.nominal_value,
                    tolerance_min=line_data.tolerance_min,
                    tolerance_max=line_data.tolerance_max,
                    unit=line_data.unit,
                    measured_value=line_data.measured_value,
                    measured_text=line_data.measured_text,
                    measured_boolean=line_data.measured_boolean,
                    result=line_data.result or ControlResult.PENDING,
                    equipment_code=line_data.equipment_code,
                    comments=line_data.comments,
                    created_by=self.user_id,
                )
                self.db.add(line)

        self.db.commit()
        self.db.refresh(control)
        return control

    def get_control(self, control_id: int) -> QualityControl | None:
        """Récupère un contrôle par ID"""
        return self.db.query(QualityControl).options(
            joinedload(QualityControl.lines)
        ).filter(
            QualityControl.id == control_id,
            QualityControl.tenant_id == self.tenant_id
        ).first()

    def list_controls(
        self,
        skip: int = 0,
        limit: int = 50,
        control_type: ControlType | None = None,
        status: ControlStatus | None = None,
        result: ControlResult | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
    ) -> tuple[list[QualityControl], int]:
        """Liste les contrôles qualité"""
        query = self.db.query(QualityControl).filter(
            QualityControl.tenant_id == self.tenant_id
        )

        if control_type:
            query = query.filter(QualityControl.control_type == control_type)
        if status:
            query = query.filter(QualityControl.status == status)
        if result:
            query = query.filter(QualityControl.result == result)
        if date_from:
            query = query.filter(QualityControl.control_date >= date_from)
        if date_to:
            query = query.filter(QualityControl.control_date <= date_to)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    QualityControl.control_number.ilike(search_filter),
                    QualityControl.lot_number.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(joinedload(QualityControl.lines)).order_by(
            desc(QualityControl.control_date)
        ).offset(skip).limit(limit).all()

        return items, total

    def update_control(
        self, control_id: int, data: ControlUpdate
    ) -> QualityControl | None:
        """Met à jour un contrôle"""
        control = self.get_control(control_id)
        if not control:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(control, field, value)

        self.db.commit()
        self.db.refresh(control)
        return control

    def start_control(self, control_id: int) -> QualityControl | None:
        """Démarre un contrôle"""
        control = self.get_control(control_id)
        if not control:
            return None

        control.status = ControlStatus.IN_PROGRESS
        control.start_time = datetime.now()
        control.controller_id = self.user_id
        self.db.commit()
        self.db.refresh(control)
        return control

    def update_control_line(
        self, line_id: int, data: ControlLineUpdate
    ) -> QualityControlLine | None:
        """Met à jour une ligne de contrôle"""
        line = self.db.query(QualityControlLine).filter(
            QualityControlLine.id == line_id,
            QualityControlLine.tenant_id == self.tenant_id
        ).first()
        if not line:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(line, field, value)

        line.measurement_date = datetime.now()

        # Calculer le résultat si valeur mesurée
        if data.measured_value is not None and line.nominal_value is not None:
            if line.tolerance_min is not None and line.tolerance_max is not None:
                lower = line.nominal_value + line.tolerance_min
                upper = line.nominal_value + line.tolerance_max
                if lower <= data.measured_value <= upper:
                    line.result = ControlResult.PASSED
                else:
                    line.result = ControlResult.FAILED
                line.deviation = data.measured_value - line.nominal_value

        self.db.commit()
        self.db.refresh(line)
        return line

    def complete_control(
        self, control_id: int, decision: str, comments: str | None = None
    ) -> QualityControl | None:
        """Termine un contrôle qualité"""
        control = self.get_control(control_id)
        if not control:
            return None

        control.status = ControlStatus.COMPLETED
        control.end_time = datetime.now()
        control.decision = decision
        control.decision_by_id = self.user_id
        control.decision_date = datetime.now()
        control.decision_comments = comments
        control.result_date = datetime.now()

        # Calculer le résultat global
        lines = control.lines
        if lines:
            failed_count = sum(1 for l in lines if l.result == ControlResult.FAILED)
            control.quantity_controlled = control.quantity_to_control
            control.quantity_non_conforming = Decimal(failed_count)
            control.quantity_conforming = control.quantity_to_control - control.quantity_non_conforming if control.quantity_to_control else None

            if failed_count > 0:
                control.result = ControlResult.FAILED if decision == "REJECT" else ControlResult.CONDITIONAL
            else:
                control.result = ControlResult.PASSED

        self.db.commit()
        self.db.refresh(control)
        return control

    # ========================================================================
    # AUDITS
    # ========================================================================

    def _generate_audit_number(self) -> str:
        """Génère un numéro d'audit"""
        year = datetime.now().year
        count = self.db.query(func.count(QualityAudit.id)).filter(
            QualityAudit.tenant_id == self.tenant_id,
            func.extract("year", QualityAudit.created_at) == year
        ).scalar() or 0
        return f"AUD-{year}-{count + 1:04d}"

    def create_audit(self, data: AuditCreate) -> QualityAudit:
        """Crée un audit"""
        audit = QualityAudit(
            tenant_id=self.tenant_id,
            audit_number=self._generate_audit_number(),
            title=data.title,
            description=data.description,
            audit_type=data.audit_type,
            reference_standard=data.reference_standard,
            reference_version=data.reference_version,
            audit_scope=data.audit_scope,
            planned_date=data.planned_date,
            planned_end_date=data.planned_end_date,
            status=AuditStatus.PLANNED,
            lead_auditor_id=data.lead_auditor_id,
            auditors=data.auditors,
            audited_entity=data.audited_entity,
            audited_department=data.audited_department,
            auditee_contact_id=data.auditee_contact_id,
            supplier_id=data.supplier_id,
            created_by=self.user_id,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def get_audit(self, audit_id: int) -> QualityAudit | None:
        """Récupère un audit par ID"""
        return self.db.query(QualityAudit).options(
            joinedload(QualityAudit.findings)
        ).filter(
            QualityAudit.id == audit_id,
            QualityAudit.tenant_id == self.tenant_id
        ).first()

    def list_audits(
        self,
        skip: int = 0,
        limit: int = 50,
        audit_type: AuditType | None = None,
        status: AuditStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
    ) -> tuple[list[QualityAudit], int]:
        """Liste les audits"""
        query = self.db.query(QualityAudit).filter(
            QualityAudit.tenant_id == self.tenant_id
        )

        if audit_type:
            query = query.filter(QualityAudit.audit_type == audit_type)
        if status:
            query = query.filter(QualityAudit.status == status)
        if date_from:
            query = query.filter(QualityAudit.planned_date >= date_from)
        if date_to:
            query = query.filter(QualityAudit.planned_date <= date_to)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    QualityAudit.audit_number.ilike(search_filter),
                    QualityAudit.title.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(joinedload(QualityAudit.findings)).order_by(
            desc(QualityAudit.planned_date)
        ).offset(skip).limit(limit).all()

        return items, total

    def update_audit(self, audit_id: int, data: AuditUpdate) -> QualityAudit | None:
        """Met à jour un audit"""
        audit = self.get_audit(audit_id)
        if not audit:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(audit, field, value)

        self.db.commit()
        self.db.refresh(audit)
        return audit

    def start_audit(self, audit_id: int) -> QualityAudit | None:
        """Démarre un audit"""
        audit = self.get_audit(audit_id)
        if not audit:
            return None

        audit.status = AuditStatus.IN_PROGRESS
        audit.actual_date = date.today()
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def add_finding(
        self, audit_id: int, data: AuditFindingCreate
    ) -> AuditFinding | None:
        """Ajoute un constat à un audit"""
        audit = self.get_audit(audit_id)
        if not audit:
            return None

        finding_count = self.db.query(func.count(AuditFinding.id)).filter(
            AuditFinding.audit_id == audit_id
        ).scalar() or 0

        finding = AuditFinding(
            tenant_id=self.tenant_id,
            audit_id=audit_id,
            finding_number=finding_count + 1,
            title=data.title,
            description=data.description,
            severity=data.severity,
            category=data.category,
            clause_reference=data.clause_reference,
            process_reference=data.process_reference,
            evidence=data.evidence,
            risk_description=data.risk_description,
            capa_required=data.capa_required,
            action_due_date=data.action_due_date,
            status="OPEN",
            created_by=self.user_id,
        )
        self.db.add(finding)

        # Mettre à jour les compteurs de l'audit
        audit.total_findings = (audit.total_findings or 0) + 1
        if data.severity == FindingSeverity.CRITICAL:
            audit.critical_findings = (audit.critical_findings or 0) + 1
        elif data.severity == FindingSeverity.MAJOR:
            audit.major_findings = (audit.major_findings or 0) + 1
        elif data.severity == FindingSeverity.MINOR:
            audit.minor_findings = (audit.minor_findings or 0) + 1
        else:
            audit.observations = (audit.observations or 0) + 1

        self.db.commit()
        self.db.refresh(finding)
        return finding

    def update_finding(
        self, finding_id: int, data: AuditFindingUpdate
    ) -> AuditFinding | None:
        """Met à jour un constat"""
        finding = self.db.query(AuditFinding).filter(
            AuditFinding.id == finding_id,
            AuditFinding.tenant_id == self.tenant_id
        ).first()
        if not finding:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(finding, field, value)

        self.db.commit()
        self.db.refresh(finding)
        return finding

    def close_audit(self, audit_id: int, data: AuditClose) -> QualityAudit | None:
        """Clôture un audit"""
        audit = self.get_audit(audit_id)
        if not audit:
            return None

        audit.status = AuditStatus.CLOSED
        audit.actual_end_date = date.today()
        audit.closed_date = date.today()
        audit.closed_by_id = self.user_id
        audit.audit_conclusion = data.audit_conclusion
        audit.recommendation = data.recommendation
        audit.report_date = date.today()

        self.db.commit()
        self.db.refresh(audit)
        return audit

    # ========================================================================
    # CAPA
    # ========================================================================

    def _generate_capa_number(self) -> str:
        """Génère un numéro CAPA"""
        year = datetime.now().year
        count = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            func.extract("year", CAPA.created_at) == year
        ).scalar() or 0
        return f"CAPA-{year}-{count + 1:04d}"

    def create_capa(self, data: CAPACreate) -> CAPA:
        """Crée un CAPA"""
        capa = CAPA(
            tenant_id=self.tenant_id,
            capa_number=self._generate_capa_number(),
            title=data.title,
            description=data.description,
            capa_type=data.capa_type,
            source_type=data.source_type,
            source_reference=data.source_reference,
            source_id=data.source_id,
            status=CAPAStatus.DRAFT,
            priority=data.priority,
            open_date=data.open_date,
            target_close_date=data.target_close_date,
            owner_id=data.owner_id,
            department=data.department,
            problem_statement=data.problem_statement,
            immediate_containment=data.immediate_containment,
            effectiveness_criteria=data.effectiveness_criteria,
            created_by=self.user_id,
        )
        self.db.add(capa)
        self.db.commit()
        self.db.refresh(capa)
        return capa

    def get_capa(self, capa_id: int) -> CAPA | None:
        """Récupère un CAPA par ID"""
        return self.db.query(CAPA).options(
            joinedload(CAPA.actions)
        ).filter(
            CAPA.id == capa_id,
            CAPA.tenant_id == self.tenant_id
        ).first()

    def list_capas(
        self,
        skip: int = 0,
        limit: int = 50,
        capa_type: CAPAType | None = None,
        status: CAPAStatus | None = None,
        priority: str | None = None,
        owner_id: int | None = None,
        search: str | None = None,
    ) -> tuple[list[CAPA], int]:
        """Liste les CAPA"""
        query = self.db.query(CAPA).filter(CAPA.tenant_id == self.tenant_id)

        if capa_type:
            query = query.filter(CAPA.capa_type == capa_type)
        if status:
            query = query.filter(CAPA.status == status)
        if priority:
            query = query.filter(CAPA.priority == priority)
        if owner_id:
            query = query.filter(CAPA.owner_id == owner_id)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    CAPA.capa_number.ilike(search_filter),
                    CAPA.title.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(joinedload(CAPA.actions)).order_by(
            desc(CAPA.open_date)
        ).offset(skip).limit(limit).all()

        return items, total

    def update_capa(self, capa_id: int, data: CAPAUpdate) -> CAPA | None:
        """Met à jour un CAPA"""
        capa = self.get_capa(capa_id)
        if not capa:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(capa, field, value)

        self.db.commit()
        self.db.refresh(capa)
        return capa

    def add_capa_action(
        self, capa_id: int, data: CAPAActionCreate
    ) -> CAPAAction | None:
        """Ajoute une action à un CAPA"""
        capa = self.get_capa(capa_id)
        if not capa:
            return None

        action_count = self.db.query(func.count(CAPAAction.id)).filter(
            CAPAAction.capa_id == capa_id
        ).scalar() or 0

        action = CAPAAction(
            tenant_id=self.tenant_id,
            capa_id=capa_id,
            action_number=action_count + 1,
            action_type=data.action_type,
            description=data.description,
            responsible_id=data.responsible_id,
            planned_date=data.planned_date,
            due_date=data.due_date,
            status="PLANNED",
            verification_required=data.verification_required,
            estimated_cost=data.estimated_cost,
            created_by=self.user_id,
        )
        self.db.add(action)

        # Mettre à jour statut CAPA
        if capa.status in [CAPAStatus.DRAFT, CAPAStatus.OPEN, CAPAStatus.ANALYSIS]:
            capa.status = CAPAStatus.ACTION_PLANNING

        self.db.commit()
        self.db.refresh(action)
        return action

    def update_capa_action(
        self, action_id: int, data: CAPAActionUpdate
    ) -> CAPAAction | None:
        """Met à jour une action CAPA"""
        action = self.db.query(CAPAAction).filter(
            CAPAAction.id == action_id,
            CAPAAction.tenant_id == self.tenant_id
        ).first()
        if not action:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(action, field, value)

        self.db.commit()
        self.db.refresh(action)
        return action

    def close_capa(self, capa_id: int, data: CAPAClose) -> CAPA | None:
        """Clôture un CAPA"""
        capa = self.get_capa(capa_id)
        if not capa:
            return None

        capa.effectiveness_verified = data.effectiveness_verified
        capa.effectiveness_result = data.effectiveness_result
        capa.effectiveness_date = date.today()
        capa.verified_by_id = self.user_id
        capa.closure_comments = data.closure_comments
        capa.actual_close_date = date.today()
        capa.closed_by_id = self.user_id

        if data.effectiveness_verified:
            capa.status = CAPAStatus.CLOSED_EFFECTIVE
        else:
            capa.status = CAPAStatus.CLOSED_INEFFECTIVE

        self.db.commit()
        self.db.refresh(capa)
        return capa

    # ========================================================================
    # RÉCLAMATIONS CLIENTS
    # ========================================================================

    def _generate_claim_number(self) -> str:
        """Génère un numéro de réclamation"""
        year = datetime.now().year
        count = self.db.query(func.count(CustomerClaim.id)).filter(
            CustomerClaim.tenant_id == self.tenant_id,
            func.extract("year", CustomerClaim.created_at) == year
        ).scalar() or 0
        return f"REC-{year}-{count + 1:05d}"

    def create_claim(self, data: ClaimCreate) -> CustomerClaim:
        """Crée une réclamation client"""
        claim = CustomerClaim(
            tenant_id=self.tenant_id,
            claim_number=self._generate_claim_number(),
            title=data.title,
            description=data.description,
            customer_id=data.customer_id,
            customer_contact=data.customer_contact,
            customer_reference=data.customer_reference,
            received_date=data.received_date,
            received_via=data.received_via,
            received_by_id=self.user_id,
            product_id=data.product_id,
            order_reference=data.order_reference,
            invoice_reference=data.invoice_reference,
            lot_number=data.lot_number,
            quantity_affected=data.quantity_affected,
            claim_type=data.claim_type,
            severity=data.severity,
            priority=data.priority,
            status=ClaimStatus.RECEIVED,
            owner_id=data.owner_id,
            response_due_date=data.response_due_date,
            claim_amount=data.claim_amount,
            created_by=self.user_id,
        )
        self.db.add(claim)
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def get_claim(self, claim_id: int) -> CustomerClaim | None:
        """Récupère une réclamation par ID"""
        return self.db.query(CustomerClaim).options(
            joinedload(CustomerClaim.actions)
        ).filter(
            CustomerClaim.id == claim_id,
            CustomerClaim.tenant_id == self.tenant_id
        ).first()

    def list_claims(
        self,
        skip: int = 0,
        limit: int = 50,
        status: ClaimStatus | None = None,
        customer_id: int | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        search: str | None = None,
    ) -> tuple[list[CustomerClaim], int]:
        """Liste les réclamations"""
        query = self.db.query(CustomerClaim).filter(
            CustomerClaim.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(CustomerClaim.status == status)
        if customer_id:
            query = query.filter(CustomerClaim.customer_id == customer_id)
        if date_from:
            query = query.filter(CustomerClaim.received_date >= date_from)
        if date_to:
            query = query.filter(CustomerClaim.received_date <= date_to)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    CustomerClaim.claim_number.ilike(search_filter),
                    CustomerClaim.title.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(joinedload(CustomerClaim.actions)).order_by(
            desc(CustomerClaim.received_date)
        ).offset(skip).limit(limit).all()

        return items, total

    def update_claim(
        self, claim_id: int, data: ClaimUpdate
    ) -> CustomerClaim | None:
        """Met à jour une réclamation"""
        claim = self.get_claim(claim_id)
        if not claim:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(claim, field, value)

        self.db.commit()
        self.db.refresh(claim)
        return claim

    def acknowledge_claim(self, claim_id: int) -> CustomerClaim | None:
        """Accuse réception d'une réclamation"""
        claim = self.get_claim(claim_id)
        if not claim:
            return None

        claim.status = ClaimStatus.ACKNOWLEDGED
        self.db.commit()
        self.db.refresh(claim)
        return claim

    def respond_claim(
        self, claim_id: int, data: ClaimRespond
    ) -> CustomerClaim | None:
        """Répond à une réclamation"""
        claim = self.get_claim(claim_id)
        if not claim:
            return None

        claim.response_content = data.response_content
        claim.response_date = date.today()
        claim.response_by_id = self.user_id
        claim.status = ClaimStatus.RESPONSE_SENT

        self.db.commit()
        self.db.refresh(claim)
        return claim

    def resolve_claim(
        self, claim_id: int, data: ClaimResolve
    ) -> CustomerClaim | None:
        """Résout une réclamation"""
        claim = self.get_claim(claim_id)
        if not claim:
            return None

        claim.resolution_type = data.resolution_type
        claim.resolution_description = data.resolution_description
        claim.accepted_amount = data.accepted_amount
        claim.resolution_date = date.today()
        claim.status = ClaimStatus.RESOLVED

        self.db.commit()
        self.db.refresh(claim)
        return claim

    def close_claim(self, claim_id: int, data: ClaimClose) -> CustomerClaim | None:
        """Clôture une réclamation"""
        claim = self.get_claim(claim_id)
        if not claim:
            return None

        claim.customer_satisfied = data.customer_satisfied
        claim.satisfaction_feedback = data.satisfaction_feedback
        claim.closed_date = date.today()
        claim.closed_by_id = self.user_id
        claim.status = ClaimStatus.CLOSED

        self.db.commit()
        self.db.refresh(claim)
        return claim

    def add_claim_action(
        self, claim_id: int, data: ClaimActionCreate
    ) -> ClaimAction | None:
        """Ajoute une action à une réclamation"""
        claim = self.get_claim(claim_id)
        if not claim:
            return None

        action_count = self.db.query(func.count(ClaimAction.id)).filter(
            ClaimAction.claim_id == claim_id
        ).scalar() or 0

        action = ClaimAction(
            tenant_id=self.tenant_id,
            claim_id=claim_id,
            action_number=action_count + 1,
            action_type=data.action_type,
            description=data.description,
            responsible_id=data.responsible_id,
            due_date=data.due_date,
            status="PLANNED",
            created_by=self.user_id,
        )
        self.db.add(action)
        self.db.commit()
        self.db.refresh(action)
        return action

    # ========================================================================
    # INDICATEURS QUALITÉ
    # ========================================================================

    def create_indicator(self, data: IndicatorCreate) -> QualityIndicator:
        """Crée un indicateur qualité"""
        indicator = QualityIndicator(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            category=data.category,
            formula=data.formula,
            unit=data.unit,
            target_value=data.target_value,
            target_min=data.target_min,
            target_max=data.target_max,
            warning_threshold=data.warning_threshold,
            critical_threshold=data.critical_threshold,
            direction=data.direction,
            measurement_frequency=data.measurement_frequency,
            data_source=data.data_source,
            owner_id=data.owner_id,
            is_active=True,
            created_by=self.user_id,
        )
        self.db.add(indicator)
        self.db.commit()
        self.db.refresh(indicator)
        return indicator

    def get_indicator(self, indicator_id: int) -> QualityIndicator | None:
        """Récupère un indicateur par ID"""
        return self.db.query(QualityIndicator).options(
            joinedload(QualityIndicator.measurements)
        ).filter(
            QualityIndicator.id == indicator_id,
            QualityIndicator.tenant_id == self.tenant_id
        ).first()

    def list_indicators(
        self,
        skip: int = 0,
        limit: int = 50,
        category: str | None = None,
        active_only: bool = True,
        search: str | None = None,
    ) -> tuple[list[QualityIndicator], int]:
        """Liste les indicateurs"""
        query = self.db.query(QualityIndicator).filter(
            QualityIndicator.tenant_id == self.tenant_id
        )

        if category:
            query = query.filter(QualityIndicator.category == category)
        if active_only:
            query = query.filter(QualityIndicator.is_active)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    QualityIndicator.code.ilike(search_filter),
                    QualityIndicator.name.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.order_by(QualityIndicator.code).offset(skip).limit(limit).all()

        return items, total

    def update_indicator(
        self, indicator_id: int, data: IndicatorUpdate
    ) -> QualityIndicator | None:
        """Met à jour un indicateur"""
        indicator = self.get_indicator(indicator_id)
        if not indicator:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(indicator, field, value)

        self.db.commit()
        self.db.refresh(indicator)
        return indicator

    def add_measurement(
        self, indicator_id: int, data: IndicatorMeasurementCreate
    ) -> IndicatorMeasurement | None:
        """Ajoute une mesure à un indicateur"""
        indicator = self.get_indicator(indicator_id)
        if not indicator:
            return None

        # Calculer les métriques
        target_value = indicator.target_value
        deviation = None
        achievement_rate = None
        status = None

        if target_value:
            deviation = data.value - target_value
            if indicator.direction == "HIGHER_BETTER":
                achievement_rate = (data.value / target_value * 100) if target_value != 0 else None
            elif indicator.direction == "LOWER_BETTER":
                achievement_rate = (target_value / data.value * 100) if data.value != 0 else None
            else:
                achievement_rate = 100 - abs(deviation / target_value * 100) if target_value != 0 else None

        # Déterminer le statut
        if indicator.critical_threshold is not None:
            if indicator.direction == "HIGHER_BETTER":
                if data.value <= indicator.critical_threshold:
                    status = "CRITICAL"
                elif indicator.warning_threshold and data.value <= indicator.warning_threshold:
                    status = "WARNING"
                else:
                    status = "ON_TARGET"
            else:
                if data.value >= indicator.critical_threshold:
                    status = "CRITICAL"
                elif indicator.warning_threshold and data.value >= indicator.warning_threshold:
                    status = "WARNING"
                else:
                    status = "ON_TARGET"

        measurement = IndicatorMeasurement(
            tenant_id=self.tenant_id,
            indicator_id=indicator_id,
            measurement_date=data.measurement_date,
            period_start=data.period_start,
            period_end=data.period_end,
            value=data.value,
            numerator=data.numerator,
            denominator=data.denominator,
            target_value=target_value,
            deviation=deviation,
            achievement_rate=achievement_rate,
            status=status,
            comments=data.comments,
            action_required=status in ["WARNING", "CRITICAL"],
            source=data.source,
            created_by=self.user_id,
        )
        self.db.add(measurement)
        self.db.commit()
        self.db.refresh(measurement)
        return measurement

    # ========================================================================
    # CERTIFICATIONS
    # ========================================================================

    def create_certification(self, data: CertificationCreate) -> Certification:
        """Crée une certification"""
        certification = Certification(
            tenant_id=self.tenant_id,
            code=data.code,
            name=data.name,
            description=data.description,
            standard=data.standard,
            standard_version=data.standard_version,
            scope=data.scope,
            certification_body=data.certification_body,
            certification_body_accreditation=data.certification_body_accreditation,
            initial_certification_date=data.initial_certification_date,
            status=CertificationStatus.PLANNED,
            manager_id=data.manager_id,
            annual_cost=data.annual_cost,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(certification)
        self.db.commit()
        self.db.refresh(certification)
        return certification

    def get_certification(self, cert_id: int) -> Certification | None:
        """Récupère une certification par ID"""
        return self.db.query(Certification).options(
            joinedload(Certification.audits)
        ).filter(
            Certification.id == cert_id,
            Certification.tenant_id == self.tenant_id
        ).first()

    def list_certifications(
        self,
        skip: int = 0,
        limit: int = 50,
        status: CertificationStatus | None = None,
        search: str | None = None,
    ) -> tuple[list[Certification], int]:
        """Liste les certifications"""
        query = self.db.query(Certification).filter(
            Certification.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(Certification.status == status)
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Certification.code.ilike(search_filter),
                    Certification.name.ilike(search_filter),
                    Certification.standard.ilike(search_filter),
                )
            )

        total = query.count()
        items = query.options(joinedload(Certification.audits)).order_by(
            Certification.code
        ).offset(skip).limit(limit).all()

        return items, total

    def update_certification(
        self, cert_id: int, data: CertificationUpdate
    ) -> Certification | None:
        """Met à jour une certification"""
        certification = self.get_certification(cert_id)
        if not certification:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(certification, field, value)

        self.db.commit()
        self.db.refresh(certification)
        return certification

    def add_certification_audit(
        self, cert_id: int, data: CertificationAuditCreate
    ) -> CertificationAudit | None:
        """Ajoute un audit à une certification"""
        certification = self.get_certification(cert_id)
        if not certification:
            return None

        audit = CertificationAudit(
            tenant_id=self.tenant_id,
            certification_id=cert_id,
            audit_type=data.audit_type,
            audit_date=data.audit_date,
            audit_end_date=data.audit_end_date,
            lead_auditor=data.lead_auditor,
            audit_team=data.audit_team,
            notes=data.notes,
            created_by=self.user_id,
        )
        self.db.add(audit)
        self.db.commit()
        self.db.refresh(audit)
        return audit

    def update_certification_audit(
        self, audit_id: int, data: CertificationAuditUpdate
    ) -> CertificationAudit | None:
        """Met à jour un audit de certification"""
        audit = self.db.query(CertificationAudit).filter(
            CertificationAudit.id == audit_id,
            CertificationAudit.tenant_id == self.tenant_id
        ).first()
        if not audit:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(audit, field, value)

        self.db.commit()
        self.db.refresh(audit)
        return audit

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    def get_dashboard(self) -> QualityDashboard:
        """Récupère les statistiques du dashboard qualité"""
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # Non-conformités
        nc_total = self.db.query(func.count(NonConformance.id)).filter(
            NonConformance.tenant_id == self.tenant_id
        ).scalar() or 0

        nc_open = self.db.query(func.count(NonConformance.id)).filter(
            NonConformance.tenant_id == self.tenant_id,
            NonConformance.status.notin_([
                NonConformanceStatus.CLOSED,
                NonConformanceStatus.CANCELLED
            ])
        ).scalar() or 0

        nc_critical = self.db.query(func.count(NonConformance.id)).filter(
            NonConformance.tenant_id == self.tenant_id,
            NonConformance.severity == NonConformanceSeverity.CRITICAL,
            NonConformance.status.notin_([
                NonConformanceStatus.CLOSED,
                NonConformanceStatus.CANCELLED
            ])
        ).scalar() or 0

        # Contrôles qualité
        controls_total = self.db.query(func.count(QualityControl.id)).filter(
            QualityControl.tenant_id == self.tenant_id,
            QualityControl.control_date >= thirty_days_ago
        ).scalar() or 0

        controls_completed = self.db.query(func.count(QualityControl.id)).filter(
            QualityControl.tenant_id == self.tenant_id,
            QualityControl.status == ControlStatus.COMPLETED,
            QualityControl.control_date >= thirty_days_ago
        ).scalar() or 0

        controls_passed = self.db.query(func.count(QualityControl.id)).filter(
            QualityControl.tenant_id == self.tenant_id,
            QualityControl.result == ControlResult.PASSED,
            QualityControl.control_date >= thirty_days_ago
        ).scalar() or 0

        controls_pass_rate = Decimal(
            controls_passed / controls_completed * 100
        ) if controls_completed > 0 else Decimal("0")

        # Audits
        audits_planned = self.db.query(func.count(QualityAudit.id)).filter(
            QualityAudit.tenant_id == self.tenant_id,
            QualityAudit.status.in_([AuditStatus.PLANNED, AuditStatus.SCHEDULED])
        ).scalar() or 0

        audits_completed = self.db.query(func.count(QualityAudit.id)).filter(
            QualityAudit.tenant_id == self.tenant_id,
            QualityAudit.status.in_([AuditStatus.COMPLETED, AuditStatus.CLOSED]),
            func.extract("year", QualityAudit.actual_date) == today.year
        ).scalar() or 0

        audit_findings_open = self.db.query(func.count(AuditFinding.id)).filter(
            AuditFinding.tenant_id == self.tenant_id,
            AuditFinding.status == "OPEN"
        ).scalar() or 0

        # CAPA
        capa_total = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id
        ).scalar() or 0

        capa_open = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.status.notin_([
                CAPAStatus.CLOSED_EFFECTIVE,
                CAPAStatus.CLOSED_INEFFECTIVE,
                CAPAStatus.CANCELLED
            ])
        ).scalar() or 0

        capa_overdue = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.target_close_date < today,
            CAPA.status.notin_([
                CAPAStatus.CLOSED_EFFECTIVE,
                CAPAStatus.CLOSED_INEFFECTIVE,
                CAPAStatus.CANCELLED
            ])
        ).scalar() or 0

        capa_effective = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.status == CAPAStatus.CLOSED_EFFECTIVE
        ).scalar() or 0

        capa_closed = self.db.query(func.count(CAPA.id)).filter(
            CAPA.tenant_id == self.tenant_id,
            CAPA.status.in_([CAPAStatus.CLOSED_EFFECTIVE, CAPAStatus.CLOSED_INEFFECTIVE])
        ).scalar() or 0

        capa_effectiveness_rate = Decimal(
            capa_effective / capa_closed * 100
        ) if capa_closed > 0 else Decimal("0")

        # Réclamations
        claims_total = self.db.query(func.count(CustomerClaim.id)).filter(
            CustomerClaim.tenant_id == self.tenant_id,
            func.extract("year", CustomerClaim.received_date) == today.year
        ).scalar() or 0

        claims_open = self.db.query(func.count(CustomerClaim.id)).filter(
            CustomerClaim.tenant_id == self.tenant_id,
            CustomerClaim.status.notin_([ClaimStatus.CLOSED, ClaimStatus.REJECTED])
        ).scalar() or 0

        # Certifications
        certifications_active = self.db.query(func.count(Certification.id)).filter(
            Certification.tenant_id == self.tenant_id,
            Certification.status == CertificationStatus.CERTIFIED
        ).scalar() or 0

        certifications_expiring = self.db.query(func.count(Certification.id)).filter(
            Certification.tenant_id == self.tenant_id,
            Certification.status == CertificationStatus.CERTIFIED,
            Certification.expiry_date <= today + timedelta(days=90),
            Certification.expiry_date >= today
        ).scalar() or 0

        # Indicateurs
        indicators_data = self.db.query(
            IndicatorMeasurement.status,
            func.count(IndicatorMeasurement.id)
        ).join(QualityIndicator).filter(
            QualityIndicator.tenant_id == self.tenant_id,
            QualityIndicator.is_active
        ).group_by(IndicatorMeasurement.status).all()

        indicators_on_target = 0
        indicators_warning = 0
        indicators_critical = 0
        for status_val, count in indicators_data:
            if status_val == "ON_TARGET":
                indicators_on_target = count
            elif status_val == "WARNING":
                indicators_warning = count
            elif status_val == "CRITICAL":
                indicators_critical = count

        return QualityDashboard(
            nc_total=nc_total,
            nc_open=nc_open,
            nc_critical=nc_critical,
            controls_total=controls_total,
            controls_completed=controls_completed,
            controls_pass_rate=controls_pass_rate,
            audits_planned=audits_planned,
            audits_completed=audits_completed,
            audit_findings_open=audit_findings_open,
            capa_total=capa_total,
            capa_open=capa_open,
            capa_overdue=capa_overdue,
            capa_effectiveness_rate=capa_effectiveness_rate,
            claims_total=claims_total,
            claims_open=claims_open,
            certifications_active=certifications_active,
            certifications_expiring_soon=certifications_expiring,
            indicators_on_target=indicators_on_target,
            indicators_warning=indicators_warning,
            indicators_critical=indicators_critical,
        )


def get_quality_service(db: Session, tenant_id: int, user_id: int) -> QualityService:
    """Factory function pour le service qualité"""
    return QualityService(db, tenant_id, user_id)
