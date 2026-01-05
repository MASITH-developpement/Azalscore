"""
AZALS - PACK PAYS FRANCE - Service
====================================
Logique métier pour la localisation française.
"""

import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.orm import Session

from .models import (
    PCGAccount, PCGClass,
    FRVATRate, FRVATDeclaration, TVARate, TVARegime,
    FECExport, FECEntry, FECStatus,
    DSNDeclaration, DSNEmployee, DSNType, DSNStatus,
    FREmploymentContract, ContractType,
    RGPDConsent, RGPDRequest, RGPDDataProcessing, RGPDDataBreach,
    RGPDConsentStatus, RGPDRequestType,
)
from .schemas import (
    PCGAccountCreate, VATDeclarationCreate,
    FECGenerateRequest, FECValidationResult,
    DSNGenerateRequest, DSNEmployeeData,
    FRContractCreate,
    RGPDConsentCreate, RGPDRequestCreate, RGPDProcessingCreate, RGPDBreachCreate,
    FrancePackStats,
)


class FrancePackService:
    """Service Pack Pays France."""

    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ========================================================================
    # PCG - PLAN COMPTABLE GÉNÉRAL
    # ========================================================================

    def initialize_pcg(self) -> int:
        """Initialiser le PCG 2024 standard."""
        # Vérifier si déjà initialisé
        existing = self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.is_custom == False
        ).first()
        if existing:
            return 0

        # Comptes PCG 2024 de base (principaux)
        pcg_accounts = [
            # Classe 1 - Capitaux
            ("10", "Capital et réserves", PCGClass.CLASSE_1, "C"),
            ("101", "Capital", PCGClass.CLASSE_1, "C"),
            ("106", "Réserves", PCGClass.CLASSE_1, "C"),
            ("108", "Compte de l'exploitant", PCGClass.CLASSE_1, "C"),
            ("12", "Résultat de l'exercice", PCGClass.CLASSE_1, "C"),
            ("16", "Emprunts et dettes assimilées", PCGClass.CLASSE_1, "C"),
            ("164", "Emprunts auprès des établissements de crédit", PCGClass.CLASSE_1, "C"),

            # Classe 2 - Immobilisations
            ("20", "Immobilisations incorporelles", PCGClass.CLASSE_2, "D"),
            ("21", "Immobilisations corporelles", PCGClass.CLASSE_2, "D"),
            ("211", "Terrains", PCGClass.CLASSE_2, "D"),
            ("213", "Constructions", PCGClass.CLASSE_2, "D"),
            ("215", "Installations techniques, matériel et outillage", PCGClass.CLASSE_2, "D"),
            ("218", "Autres immobilisations corporelles", PCGClass.CLASSE_2, "D"),
            ("28", "Amortissements des immobilisations", PCGClass.CLASSE_2, "C"),

            # Classe 3 - Stocks
            ("31", "Matières premières", PCGClass.CLASSE_3, "D"),
            ("32", "Autres approvisionnements", PCGClass.CLASSE_3, "D"),
            ("35", "Stocks de produits", PCGClass.CLASSE_3, "D"),
            ("37", "Stocks de marchandises", PCGClass.CLASSE_3, "D"),
            ("39", "Provisions pour dépréciation des stocks", PCGClass.CLASSE_3, "C"),

            # Classe 4 - Tiers
            ("40", "Fournisseurs et comptes rattachés", PCGClass.CLASSE_4, "C"),
            ("401", "Fournisseurs", PCGClass.CLASSE_4, "C"),
            ("404", "Fournisseurs d'immobilisations", PCGClass.CLASSE_4, "C"),
            ("41", "Clients et comptes rattachés", PCGClass.CLASSE_4, "D"),
            ("411", "Clients", PCGClass.CLASSE_4, "D"),
            ("416", "Clients douteux ou litigieux", PCGClass.CLASSE_4, "D"),
            ("42", "Personnel et comptes rattachés", PCGClass.CLASSE_4, "C"),
            ("421", "Personnel - Rémunérations dues", PCGClass.CLASSE_4, "C"),
            ("425", "Personnel - Avances et acomptes", PCGClass.CLASSE_4, "D"),
            ("43", "Sécurité sociale et autres organismes sociaux", PCGClass.CLASSE_4, "C"),
            ("44", "État et autres collectivités publiques", PCGClass.CLASSE_4, "C"),
            ("4452", "TVA due intracommunautaire", PCGClass.CLASSE_4, "C"),
            ("44566", "TVA sur autres biens et services", PCGClass.CLASSE_4, "D"),
            ("44567", "Crédit de TVA à reporter", PCGClass.CLASSE_4, "D"),
            ("44571", "TVA collectée", PCGClass.CLASSE_4, "C"),
            ("44551", "TVA à décaisser", PCGClass.CLASSE_4, "C"),

            # Classe 5 - Financiers
            ("50", "Valeurs mobilières de placement", PCGClass.CLASSE_5, "D"),
            ("51", "Banques, établissements financiers", PCGClass.CLASSE_5, "D"),
            ("512", "Banques", PCGClass.CLASSE_5, "D"),
            ("53", "Caisse", PCGClass.CLASSE_5, "D"),

            # Classe 6 - Charges
            ("60", "Achats", PCGClass.CLASSE_6, "D"),
            ("601", "Achats stockés - Matières premières", PCGClass.CLASSE_6, "D"),
            ("607", "Achats de marchandises", PCGClass.CLASSE_6, "D"),
            ("61", "Services extérieurs", PCGClass.CLASSE_6, "D"),
            ("613", "Locations", PCGClass.CLASSE_6, "D"),
            ("616", "Primes d'assurances", PCGClass.CLASSE_6, "D"),
            ("62", "Autres services extérieurs", PCGClass.CLASSE_6, "D"),
            ("622", "Rémunérations d'intermédiaires", PCGClass.CLASSE_6, "D"),
            ("625", "Déplacements, missions et réceptions", PCGClass.CLASSE_6, "D"),
            ("626", "Frais postaux et de télécommunications", PCGClass.CLASSE_6, "D"),
            ("63", "Impôts, taxes et versements assimilés", PCGClass.CLASSE_6, "D"),
            ("64", "Charges de personnel", PCGClass.CLASSE_6, "D"),
            ("641", "Rémunérations du personnel", PCGClass.CLASSE_6, "D"),
            ("645", "Charges de sécurité sociale et de prévoyance", PCGClass.CLASSE_6, "D"),
            ("65", "Autres charges de gestion courante", PCGClass.CLASSE_6, "D"),
            ("66", "Charges financières", PCGClass.CLASSE_6, "D"),
            ("661", "Charges d'intérêts", PCGClass.CLASSE_6, "D"),
            ("67", "Charges exceptionnelles", PCGClass.CLASSE_6, "D"),
            ("68", "Dotations aux amortissements et provisions", PCGClass.CLASSE_6, "D"),
            ("69", "Participation des salariés - Impôts sur les bénéfices", PCGClass.CLASSE_6, "D"),

            # Classe 7 - Produits
            ("70", "Ventes de produits fabriqués, prestations de services", PCGClass.CLASSE_7, "C"),
            ("701", "Ventes de produits finis", PCGClass.CLASSE_7, "C"),
            ("706", "Prestations de services", PCGClass.CLASSE_7, "C"),
            ("707", "Ventes de marchandises", PCGClass.CLASSE_7, "C"),
            ("71", "Production stockée", PCGClass.CLASSE_7, "C"),
            ("72", "Production immobilisée", PCGClass.CLASSE_7, "C"),
            ("74", "Subventions d'exploitation", PCGClass.CLASSE_7, "C"),
            ("75", "Autres produits de gestion courante", PCGClass.CLASSE_7, "C"),
            ("76", "Produits financiers", PCGClass.CLASSE_7, "C"),
            ("77", "Produits exceptionnels", PCGClass.CLASSE_7, "C"),
            ("78", "Reprises sur amortissements et provisions", PCGClass.CLASSE_7, "C"),
        ]

        count = 0
        for num, label, pcg_class, balance in pcg_accounts:
            account = PCGAccount(
                tenant_id=self.tenant_id,
                account_number=num,
                account_label=label,
                pcg_class=pcg_class,
                normal_balance=balance,
                is_summary=len(num) <= 2,
                is_custom=False,
            )
            self.db.add(account)
            count += 1

        self.db.commit()
        return count

    def get_pcg_account(self, account_number: str) -> Optional[PCGAccount]:
        """Récupérer un compte PCG."""
        return self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.account_number == account_number
        ).first()

    def list_pcg_accounts(
        self, pcg_class: Optional[str] = None,
        active_only: bool = True,
        skip: int = 0, limit: int = 100
    ) -> List[PCGAccount]:
        """Lister les comptes PCG."""
        query = self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id
        )
        if pcg_class:
            query = query.filter(PCGAccount.pcg_class == pcg_class)
        if active_only:
            query = query.filter(PCGAccount.is_active == True)

        return query.order_by(
            PCGAccount.account_number
        ).offset(skip).limit(limit).all()

    def create_pcg_account(self, data: PCGAccountCreate) -> PCGAccount:
        """Créer un compte PCG personnalisé."""
        account = PCGAccount(
            tenant_id=self.tenant_id,
            account_number=data.account_number,
            account_label=data.account_label,
            pcg_class=PCGClass(data.pcg_class),
            parent_account=data.parent_account,
            is_summary=data.is_summary,
            normal_balance=data.normal_balance,
            default_vat_code=data.default_vat_code,
            description=data.description,
            is_custom=True,
        )
        self.db.add(account)
        self.db.commit()
        self.db.refresh(account)
        return account

    # ========================================================================
    # TVA FRANÇAISE
    # ========================================================================

    def initialize_vat_rates(self) -> int:
        """Initialiser les taux de TVA français."""
        existing = self.db.query(FRVATRate).filter(
            FRVATRate.tenant_id == self.tenant_id
        ).first()
        if existing:
            return 0

        vat_rates = [
            ("TVA_20", "TVA taux normal", TVARate.NORMAL, Decimal("20.00"), "44571", "44566"),
            ("TVA_10", "TVA taux intermédiaire", TVARate.INTERMEDIAIRE, Decimal("10.00"), "44571", "44566"),
            ("TVA_5_5", "TVA taux réduit", TVARate.REDUIT, Decimal("5.50"), "44571", "44566"),
            ("TVA_2_1", "TVA taux super réduit", TVARate.SUPER_REDUIT, Decimal("2.10"), "44571", "44566"),
            ("TVA_0", "Exonéré de TVA", TVARate.EXONERE, Decimal("0.00"), None, None),
        ]

        count = 0
        for code, name, rate_type, rate, collected, deductible in vat_rates:
            vat = FRVATRate(
                tenant_id=self.tenant_id,
                code=code,
                name=name,
                rate_type=rate_type,
                rate=rate,
                account_collected=collected,
                account_deductible=deductible,
            )
            self.db.add(vat)
            count += 1

        self.db.commit()
        return count

    def get_vat_rate(self, code: str) -> Optional[FRVATRate]:
        """Récupérer un taux de TVA."""
        return self.db.query(FRVATRate).filter(
            FRVATRate.tenant_id == self.tenant_id,
            FRVATRate.code == code,
            FRVATRate.is_active == True
        ).first()

    def list_vat_rates(self, active_only: bool = True) -> List[FRVATRate]:
        """Lister les taux de TVA."""
        query = self.db.query(FRVATRate).filter(
            FRVATRate.tenant_id == self.tenant_id
        )
        if active_only:
            query = query.filter(FRVATRate.is_active == True)
        return query.order_by(FRVATRate.rate.desc()).all()

    def create_vat_declaration(
        self, data: VATDeclarationCreate
    ) -> FRVATDeclaration:
        """Créer une déclaration de TVA."""
        decl_number = f"TVA-{datetime.utcnow().strftime('%Y%m')}-{uuid.uuid4().hex[:6].upper()}"

        declaration = FRVATDeclaration(
            tenant_id=self.tenant_id,
            declaration_number=decl_number,
            declaration_type=data.declaration_type,
            regime=TVARegime(data.regime),
            period_start=data.period_start,
            period_end=data.period_end,
            due_date=data.due_date,
            status="draft",
        )
        self.db.add(declaration)
        self.db.commit()
        self.db.refresh(declaration)
        return declaration

    def calculate_vat_declaration(self, declaration_id: int) -> FRVATDeclaration:
        """Calculer les montants d'une déclaration TVA."""
        declaration = self.db.query(FRVATDeclaration).filter(
            FRVATDeclaration.tenant_id == self.tenant_id,
            FRVATDeclaration.id == declaration_id
        ).first()
        if not declaration:
            raise ValueError("Déclaration non trouvée")

        # TODO: Calculer depuis les écritures comptables réelles
        # Pour l'instant, simulation
        declaration.total_ht = Decimal("100000.00")
        declaration.total_tva_collectee = Decimal("20000.00")
        declaration.total_tva_deductible = Decimal("8000.00")
        declaration.tva_nette = declaration.total_tva_collectee - declaration.total_tva_deductible
        declaration.credit_tva = Decimal("0") if declaration.tva_nette >= 0 else abs(declaration.tva_nette)

        self.db.commit()
        self.db.refresh(declaration)
        return declaration

    # ========================================================================
    # FEC - FICHIER DES ÉCRITURES COMPTABLES
    # ========================================================================

    def generate_fec(self, data: FECGenerateRequest) -> FECExport:
        """Générer un FEC."""
        fec_code = f"FEC-{data.siren}-{data.fiscal_year}"
        filename = f"{data.siren}FEC{data.period_end.strftime('%Y%m%d')}.txt"

        fec_export = FECExport(
            tenant_id=self.tenant_id,
            fec_code=fec_code,
            siren=data.siren,
            fiscal_year=data.fiscal_year,
            period_start=data.period_start,
            period_end=data.period_end,
            filename=filename,
            status=FECStatus.DRAFT,
        )
        self.db.add(fec_export)
        self.db.flush()

        # TODO: Extraire les écritures comptables réelles
        # Pour l'instant, pas d'entrées

        fec_export.total_entries = 0
        fec_export.total_debit = Decimal("0")
        fec_export.total_credit = Decimal("0")
        fec_export.is_balanced = True
        fec_export.is_valid = True
        fec_export.generated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(fec_export)
        return fec_export

    def validate_fec(self, fec_id: int) -> FECValidationResult:
        """Valider un FEC."""
        fec = self.db.query(FECExport).filter(
            FECExport.tenant_id == self.tenant_id,
            FECExport.id == fec_id
        ).first()
        if not fec:
            raise ValueError("FEC non trouvé")

        errors = []
        warnings = []

        # Validation équilibre débit/crédit
        if fec.total_debit != fec.total_credit:
            errors.append({
                "code": "UNBALANCED",
                "message": f"Le FEC n'est pas équilibré: Débit={fec.total_debit}, Crédit={fec.total_credit}"
            })

        # Validation format SIREN
        if len(fec.siren) != 9 or not fec.siren.isdigit():
            errors.append({
                "code": "INVALID_SIREN",
                "message": "Le SIREN doit contenir exactement 9 chiffres"
            })

        result = FECValidationResult(
            is_valid=len(errors) == 0,
            total_entries=fec.total_entries,
            total_debit=fec.total_debit,
            total_credit=fec.total_credit,
            is_balanced=fec.total_debit == fec.total_credit,
            errors=errors,
            warnings=warnings,
        )

        fec.is_valid = result.is_valid
        fec.validation_errors = errors if errors else None
        if result.is_valid:
            fec.status = FECStatus.VALIDATED
            fec.validated_at = datetime.utcnow()

        self.db.commit()
        return result

    def export_fec_file(self, fec_id: int) -> str:
        """Exporter le FEC au format texte."""
        fec = self.db.query(FECExport).filter(
            FECExport.tenant_id == self.tenant_id,
            FECExport.id == fec_id
        ).first()
        if not fec:
            raise ValueError("FEC non trouvé")

        if not fec.is_valid:
            raise ValueError("Le FEC doit être validé avant export")

        entries = self.db.query(FECEntry).filter(
            FECEntry.fec_export_id == fec_id
        ).order_by(FECEntry.line_number).all()

        # Entête FEC
        header = "JournalCode|JournalLib|EcritureNum|EcritureDate|CompteNum|CompteLib|CompAuxNum|CompAuxLib|PieceRef|PieceDate|EcritureLib|Debit|Credit|EcritureLet|DateLet|ValidDate|Montantdevise|Idevise"

        lines = [header]
        for entry in entries:
            line = "|".join([
                entry.journal_code,
                entry.journal_lib,
                entry.ecriture_num,
                entry.ecriture_date.strftime("%Y%m%d"),
                entry.compte_num,
                entry.compte_lib,
                entry.comp_aux_num or "",
                entry.comp_aux_lib or "",
                entry.piece_ref,
                entry.piece_date.strftime("%Y%m%d"),
                entry.ecriture_lib,
                str(entry.debit).replace(".", ","),
                str(entry.credit).replace(".", ","),
                entry.ecriture_let or "",
                entry.date_let.strftime("%Y%m%d") if entry.date_let else "",
                entry.valid_date.strftime("%Y%m%d") if entry.valid_date else "",
                str(entry.montant_devise).replace(".", ",") if entry.montant_devise else "",
                entry.idevise or "",
            ])
            lines.append(line)

        fec.status = FECStatus.EXPORTED
        fec.exported_at = datetime.utcnow()
        self.db.commit()

        return "\n".join(lines)

    # ========================================================================
    # DSN - DÉCLARATION SOCIALE NOMINATIVE
    # ========================================================================

    def create_dsn(self, data: DSNGenerateRequest) -> DSNDeclaration:
        """Créer une DSN."""
        dsn_code = f"DSN-{data.period_year}{data.period_month:02d}-{uuid.uuid4().hex[:6].upper()}"

        dsn = DSNDeclaration(
            tenant_id=self.tenant_id,
            dsn_code=dsn_code,
            dsn_type=DSNType(data.dsn_type),
            siret=data.siret,
            period_month=data.period_month,
            period_year=data.period_year,
            status=DSNStatus.DRAFT,
        )
        self.db.add(dsn)
        self.db.commit()
        self.db.refresh(dsn)
        return dsn

    def add_dsn_employee(
        self, dsn_id: int, data: DSNEmployeeData
    ) -> DSNEmployee:
        """Ajouter un salarié à la DSN."""
        dsn = self.db.query(DSNDeclaration).filter(
            DSNDeclaration.tenant_id == self.tenant_id,
            DSNDeclaration.id == dsn_id
        ).first()
        if not dsn:
            raise ValueError("DSN non trouvée")

        employee = DSNEmployee(
            tenant_id=self.tenant_id,
            dsn_declaration_id=dsn_id,
            employee_id=data.employee_id,
            nir=data.nir,
            nom=data.nom,
            prenoms=data.prenoms,
            date_naissance=data.date_naissance,
            brut_periode=data.brut_periode,
            net_imposable=data.net_imposable,
            heures_travaillees=data.heures_travaillees,
            cotisations_details=data.cotisations,
            absences=data.absences,
        )
        self.db.add(employee)

        # Mettre à jour totaux DSN
        dsn.total_employees = self.db.query(DSNEmployee).filter(
            DSNEmployee.dsn_declaration_id == dsn_id
        ).count() + 1
        dsn.total_brut = (dsn.total_brut or Decimal("0")) + data.brut_periode

        self.db.commit()
        self.db.refresh(employee)
        return employee

    def submit_dsn(self, dsn_id: int) -> DSNDeclaration:
        """Soumettre la DSN (simulation)."""
        dsn = self.db.query(DSNDeclaration).filter(
            DSNDeclaration.tenant_id == self.tenant_id,
            DSNDeclaration.id == dsn_id
        ).first()
        if not dsn:
            raise ValueError("DSN non trouvée")

        # Simulation de soumission
        dsn.status = DSNStatus.SUBMITTED
        dsn.submitted_at = datetime.utcnow()
        dsn.submission_id = f"NET-{uuid.uuid4().hex[:12].upper()}"

        self.db.commit()
        self.db.refresh(dsn)
        return dsn

    # ========================================================================
    # CONTRATS FRANÇAIS
    # ========================================================================

    def create_contract(self, data: FRContractCreate) -> FREmploymentContract:
        """Créer un contrat de travail français."""
        contract_number = f"CTR-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        contract = FREmploymentContract(
            tenant_id=self.tenant_id,
            employee_id=data.employee_id,
            contract_type=ContractType(data.contract_type),
            contract_number=contract_number,
            start_date=data.start_date,
            end_date=data.end_date,
            trial_period_end=data.trial_period_end,
            convention_collective=data.convention_collective,
            niveau=data.niveau,
            coefficient=data.coefficient,
            is_full_time=data.is_full_time,
            work_hours_weekly=data.work_hours_weekly,
            is_forfait_jours=data.is_forfait_jours,
            forfait_jours_annual=data.forfait_jours_annual,
            base_salary=data.base_salary,
            salary_type=data.salary_type,
            tickets_restaurant=data.tickets_restaurant,
            mutuelle_obligatoire=data.mutuelle_obligatoire,
        )
        self.db.add(contract)
        self.db.commit()
        self.db.refresh(contract)
        return contract

    # ========================================================================
    # RGPD
    # ========================================================================

    def create_consent(self, data: RGPDConsentCreate) -> RGPDConsent:
        """Créer un consentement RGPD."""
        consent = RGPDConsent(
            tenant_id=self.tenant_id,
            data_subject_type=data.data_subject_type,
            data_subject_id=data.data_subject_id,
            data_subject_email=data.data_subject_email,
            purpose=data.purpose,
            purpose_description=data.purpose_description,
            legal_basis=data.legal_basis,
            status=RGPDConsentStatus.GRANTED,
            consent_given_at=datetime.utcnow(),
            consent_method=data.consent_method,
            consent_proof=data.consent_proof,
            valid_until=data.valid_until,
        )
        self.db.add(consent)
        self.db.commit()
        self.db.refresh(consent)
        return consent

    def withdraw_consent(self, consent_id: int, reason: str = None) -> RGPDConsent:
        """Retirer un consentement RGPD."""
        consent = self.db.query(RGPDConsent).filter(
            RGPDConsent.tenant_id == self.tenant_id,
            RGPDConsent.id == consent_id
        ).first()
        if not consent:
            raise ValueError("Consentement non trouvé")

        consent.status = RGPDConsentStatus.WITHDRAWN
        consent.withdrawn_at = datetime.utcnow()
        consent.withdrawn_reason = reason

        self.db.commit()
        self.db.refresh(consent)
        return consent

    def create_rgpd_request(self, data: RGPDRequestCreate) -> RGPDRequest:
        """Créer une demande RGPD."""
        request_code = f"RGPD-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Délai légal: 1 mois
        due_date = date.today() + timedelta(days=30)

        request = RGPDRequest(
            tenant_id=self.tenant_id,
            request_code=request_code,
            request_type=RGPDRequestType(data.request_type),
            data_subject_type=data.data_subject_type,
            data_subject_id=data.data_subject_id,
            requester_name=data.requester_name,
            requester_email=data.requester_email,
            requester_phone=data.requester_phone,
            request_details=data.request_details,
            due_date=due_date,
            status="pending",
        )
        self.db.add(request)
        self.db.commit()
        self.db.refresh(request)
        return request

    def process_rgpd_request(
        self, request_id: int, response: str,
        data_exported: bool = False, data_deleted: bool = False
    ) -> RGPDRequest:
        """Traiter une demande RGPD."""
        request = self.db.query(RGPDRequest).filter(
            RGPDRequest.tenant_id == self.tenant_id,
            RGPDRequest.id == request_id
        ).first()
        if not request:
            raise ValueError("Demande non trouvée")

        request.status = "completed"
        request.processed_at = datetime.utcnow()
        request.response_details = response
        request.data_exported = data_exported
        request.data_deleted = data_deleted

        self.db.commit()
        self.db.refresh(request)
        return request

    def create_data_processing(self, data: RGPDProcessingCreate) -> RGPDDataProcessing:
        """Créer une entrée au registre des traitements."""
        processing = RGPDDataProcessing(
            tenant_id=self.tenant_id,
            processing_code=data.processing_code,
            processing_name=data.processing_name,
            processing_description=data.processing_description,
            purposes=data.purposes,
            legal_basis=data.legal_basis,
            legal_basis_details=data.legal_basis_details,
            data_categories=data.data_categories,
            special_categories=data.special_categories,
            data_subjects=data.data_subjects,
            recipients=data.recipients,
            retention_period=data.retention_period,
            security_measures=data.security_measures,
            start_date=date.today(),
        )
        self.db.add(processing)
        self.db.commit()
        self.db.refresh(processing)
        return processing

    def report_data_breach(self, data: RGPDBreachCreate) -> RGPDDataBreach:
        """Signaler une violation de données."""
        breach_code = f"BREACH-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        # Évaluer si notification CNIL requise (risque pour les personnes)
        cnil_required = data.severity_level in ["high", "critical"]

        breach = RGPDDataBreach(
            tenant_id=self.tenant_id,
            breach_code=breach_code,
            breach_title=data.breach_title,
            detected_at=data.detected_at,
            breach_description=data.breach_description,
            breach_nature=data.breach_nature,
            breach_cause=data.breach_cause,
            data_categories_affected=data.data_categories_affected,
            estimated_subjects_affected=data.estimated_subjects_affected,
            potential_consequences=data.potential_consequences,
            severity_level=data.severity_level,
            containment_measures=data.containment_measures,
            cnil_notification_required=cnil_required,
            subjects_notification_required=data.severity_level == "critical",
            status="detected",
        )
        self.db.add(breach)
        self.db.commit()
        self.db.refresh(breach)
        return breach

    # ========================================================================
    # STATISTIQUES
    # ========================================================================

    def get_stats(self) -> FrancePackStats:
        """Statistiques du pack France."""
        # PCG
        total_pcg = self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id
        ).count()
        custom_pcg = self.db.query(PCGAccount).filter(
            PCGAccount.tenant_id == self.tenant_id,
            PCGAccount.is_custom == True
        ).count()

        # TVA
        total_vat = self.db.query(FRVATDeclaration).filter(
            FRVATDeclaration.tenant_id == self.tenant_id
        ).count()
        pending_vat = self.db.query(FRVATDeclaration).filter(
            FRVATDeclaration.tenant_id == self.tenant_id,
            FRVATDeclaration.status == "draft"
        ).count()

        # FEC
        total_fec = self.db.query(FECExport).filter(
            FECExport.tenant_id == self.tenant_id
        ).count()

        # DSN
        total_dsn = self.db.query(DSNDeclaration).filter(
            DSNDeclaration.tenant_id == self.tenant_id
        ).count()
        pending_dsn = self.db.query(DSNDeclaration).filter(
            DSNDeclaration.tenant_id == self.tenant_id,
            DSNDeclaration.status == DSNStatus.DRAFT
        ).count()
        rejected_dsn = self.db.query(DSNDeclaration).filter(
            DSNDeclaration.tenant_id == self.tenant_id,
            DSNDeclaration.status == DSNStatus.REJECTED
        ).count()

        # RGPD
        pending_requests = self.db.query(RGPDRequest).filter(
            RGPDRequest.tenant_id == self.tenant_id,
            RGPDRequest.status == "pending"
        ).count()
        open_breaches = self.db.query(RGPDDataBreach).filter(
            RGPDDataBreach.tenant_id == self.tenant_id,
            RGPDDataBreach.status.in_(["detected", "investigating"])
        ).count()
        active_consents = self.db.query(RGPDConsent).filter(
            RGPDConsent.tenant_id == self.tenant_id,
            RGPDConsent.status == RGPDConsentStatus.GRANTED
        ).count()

        return FrancePackStats(
            total_pcg_accounts=total_pcg,
            custom_accounts=custom_pcg,
            total_vat_declarations=total_vat,
            pending_vat_declarations=pending_vat,
            total_fec_exports=total_fec,
            total_dsn_declarations=total_dsn,
            pending_dsn=pending_dsn,
            rejected_dsn=rejected_dsn,
            pending_rgpd_requests=pending_requests,
            open_data_breaches=open_breaches,
            active_consents=active_consents,
        )
