"""
AZALS MODULE T5 - Service Packs Pays
=====================================

Service principal pour la gestion des configurations pays.
"""
from __future__ import annotations


from datetime import date
from typing import Any

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.modules.country_packs.models import (
    BankConfig,
    BankFormat,
    CountryPack,
    DateFormatStyle,
    DocumentTemplate,
    DocumentType,
    LegalRequirement,
    NumberFormatStyle,
    PackStatus,
    PublicHoliday,
    TaxRate,
    TaxType,
    TenantCountrySettings,
)


class CountryPackService:
    """Service de gestion des packs pays."""

    def __init__(self, db: Session, tenant_id: str, user_id: str = None):
        self.db = db
        self.tenant_id = tenant_id
        self.user_id = user_id  # Pour CORE SaaS v2

    # ========================================================================
    # GESTION DES PACKS PAYS
    # ========================================================================

    def create_country_pack(
        self,
        country_code: str,
        country_name: str,
        default_currency: str,
        country_name_local: str = None,
        default_language: str = "fr",
        currency_symbol: str = None,
        date_format: DateFormatStyle = DateFormatStyle.DMY,
        number_format: NumberFormatStyle = NumberFormatStyle.EU,
        timezone: str = "Europe/Paris",
        fiscal_year_start_month: int = 1,
        default_vat_rate: float = 20.0,
        company_id_label: str = "SIRET",
        vat_id_label: str = "TVA",
        config: dict = None,
        is_default: bool = False,
        created_by: int = None
    ) -> CountryPack:
        """Crée un nouveau pack pays."""
        # Si is_default, désactiver l'ancien défaut
        if is_default:
            self.db.query(CountryPack).filter(
                CountryPack.tenant_id == self.tenant_id,
                CountryPack.is_default
            ).update({"is_default": False})

        pack = CountryPack(
            tenant_id=self.tenant_id,
            country_code=country_code.upper(),
            country_name=country_name,
            country_name_local=country_name_local,
            default_language=default_language,
            default_currency=default_currency.upper(),
            currency_symbol=currency_symbol,
            date_format=date_format,
            number_format=number_format,
            timezone=timezone,
            fiscal_year_start_month=fiscal_year_start_month,
            default_vat_rate=default_vat_rate,
            company_id_label=company_id_label,
            vat_id_label=vat_id_label,
            config=config,
            is_default=is_default,
            created_by=created_by
        )
        self.db.add(pack)
        self.db.commit()
        self.db.refresh(pack)
        return pack

    def get_country_pack(self, pack_id: int) -> CountryPack | None:
        """Récupère un pack par ID."""
        return self.db.query(CountryPack).filter(
            CountryPack.id == pack_id,
            CountryPack.tenant_id == self.tenant_id
        ).first()

    def get_country_pack_by_code(self, country_code: str) -> CountryPack | None:
        """Récupère un pack par code pays."""
        return self.db.query(CountryPack).filter(
            CountryPack.country_code == country_code.upper(),
            CountryPack.tenant_id == self.tenant_id
        ).first()

    def get_default_pack(self) -> CountryPack | None:
        """Récupère le pack par défaut."""
        return self.db.query(CountryPack).filter(
            CountryPack.tenant_id == self.tenant_id,
            CountryPack.is_default
        ).first()

    def list_country_packs(
        self,
        status: PackStatus = None,
        skip: int = 0,
        limit: int = 50
    ) -> tuple[list[CountryPack], int]:
        """Liste les packs pays."""
        query = self.db.query(CountryPack).filter(
            CountryPack.tenant_id == self.tenant_id
        )

        if status:
            query = query.filter(CountryPack.status == status)

        total = query.count()
        packs = query.order_by(CountryPack.country_code).offset(skip).limit(limit).all()

        return packs, total

    def update_country_pack(self, pack_id: int, **updates) -> CountryPack | None:
        """Met à jour un pack pays."""
        pack = self.get_country_pack(pack_id)
        if not pack:
            return None

        # Si on définit comme défaut, désactiver les autres
        if updates.get("is_default"):
            self.db.query(CountryPack).filter(
                CountryPack.tenant_id == self.tenant_id,
                CountryPack.id != pack_id,
                CountryPack.is_default
            ).update({"is_default": False})

        for key, value in updates.items():
            if hasattr(pack, key) and value is not None:
                setattr(pack, key, value)

        self.db.commit()
        self.db.refresh(pack)
        return pack

    def delete_country_pack(self, pack_id: int) -> bool:
        """Supprime un pack pays."""
        pack = self.get_country_pack(pack_id)
        if not pack:
            return False

        self.db.delete(pack)
        self.db.commit()
        return True

    # ========================================================================
    # GESTION DES TAUX DE TAXE
    # ========================================================================

    def create_tax_rate(
        self,
        country_pack_id: int,
        tax_type: TaxType,
        code: str,
        name: str,
        rate: float,
        description: str = None,
        applies_to: str = "both",
        region: str = None,
        account_collected: str = None,
        account_deductible: str = None,
        account_payable: str = None,
        valid_from: date = None,
        valid_to: date = None,
        is_default: bool = False
    ) -> TaxRate:
        """Crée un taux de taxe."""
        if is_default:
            self.db.query(TaxRate).filter(
                TaxRate.tenant_id == self.tenant_id,
                TaxRate.country_pack_id == country_pack_id,
                TaxRate.tax_type == tax_type,
                TaxRate.is_default
            ).update({"is_default": False})

        tax = TaxRate(
            tenant_id=self.tenant_id,
            country_pack_id=country_pack_id,
            tax_type=tax_type,
            code=code,
            name=name,
            description=description,
            rate=rate,
            applies_to=applies_to,
            region=region,
            account_collected=account_collected,
            account_deductible=account_deductible,
            account_payable=account_payable,
            valid_from=valid_from or date.today(),
            valid_to=valid_to,
            is_default=is_default
        )
        self.db.add(tax)
        self.db.commit()
        self.db.refresh(tax)
        return tax

    def get_tax_rates(
        self,
        country_pack_id: int = None,
        tax_type: TaxType = None,
        is_active: bool = True
    ) -> list[TaxRate]:
        """Récupère les taux de taxe."""
        query = self.db.query(TaxRate).filter(TaxRate.tenant_id == self.tenant_id)

        if country_pack_id:
            query = query.filter(TaxRate.country_pack_id == country_pack_id)
        if tax_type:
            query = query.filter(TaxRate.tax_type == tax_type)
        if is_active is not None:
            query = query.filter(TaxRate.is_active == is_active)

        return query.order_by(TaxRate.code).all()

    def get_vat_rates(self, country_code: str) -> list[TaxRate]:
        """Récupère les taux de TVA pour un pays."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return []

        return self.get_tax_rates(
            country_pack_id=pack.id,
            tax_type=TaxType.VAT
        )

    def get_default_vat_rate(self, country_code: str) -> TaxRate | None:
        """Récupère le taux de TVA par défaut pour un pays."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return None

        return self.db.query(TaxRate).filter(
            TaxRate.tenant_id == self.tenant_id,
            TaxRate.country_pack_id == pack.id,
            TaxRate.tax_type == TaxType.VAT,
            TaxRate.is_default,
            TaxRate.is_active
        ).first()

    def update_tax_rate(self, tax_id: int, **updates) -> TaxRate | None:
        """Met à jour un taux de taxe."""
        tax = self.db.query(TaxRate).filter(
            TaxRate.id == tax_id,
            TaxRate.tenant_id == self.tenant_id
        ).first()

        if not tax:
            return None

        for key, value in updates.items():
            if hasattr(tax, key) and value is not None:
                setattr(tax, key, value)

        self.db.commit()
        self.db.refresh(tax)
        return tax

    def delete_tax_rate(self, tax_id: int) -> bool:
        """Supprime un taux de taxe."""
        tax = self.db.query(TaxRate).filter(
            TaxRate.id == tax_id,
            TaxRate.tenant_id == self.tenant_id
        ).first()

        if not tax:
            return False

        self.db.delete(tax)
        self.db.commit()
        return True

    # ========================================================================
    # GESTION DES TEMPLATES DE DOCUMENTS
    # ========================================================================

    def create_document_template(
        self,
        country_pack_id: int,
        document_type: DocumentType,
        code: str,
        name: str,
        description: str = None,
        template_format: str = "html",
        template_content: str = None,
        template_path: str = None,
        mandatory_fields: list[str] = None,
        legal_mentions: str = None,
        numbering_prefix: str = None,
        numbering_pattern: str = None,
        language: str = "fr",
        is_default: bool = False,
        created_by: int = None
    ) -> DocumentTemplate:
        """Crée un template de document."""
        if is_default:
            self.db.query(DocumentTemplate).filter(
                DocumentTemplate.tenant_id == self.tenant_id,
                DocumentTemplate.country_pack_id == country_pack_id,
                DocumentTemplate.document_type == document_type,
                DocumentTemplate.is_default
            ).update({"is_default": False})

        template = DocumentTemplate(
            tenant_id=self.tenant_id,
            country_pack_id=country_pack_id,
            document_type=document_type,
            code=code,
            name=name,
            description=description,
            template_format=template_format,
            template_content=template_content,
            template_path=template_path,
            mandatory_fields=mandatory_fields,
            legal_mentions=legal_mentions,
            numbering_prefix=numbering_prefix,
            numbering_pattern=numbering_pattern,
            language=language,
            is_default=is_default,
            created_by=created_by
        )
        self.db.add(template)
        self.db.commit()
        self.db.refresh(template)
        return template

    def get_document_templates(
        self,
        country_pack_id: int = None,
        document_type: DocumentType = None,
        is_active: bool = True
    ) -> list[DocumentTemplate]:
        """Récupère les templates de documents."""
        query = self.db.query(DocumentTemplate).filter(
            DocumentTemplate.tenant_id == self.tenant_id
        )

        if country_pack_id:
            query = query.filter(DocumentTemplate.country_pack_id == country_pack_id)
        if document_type:
            query = query.filter(DocumentTemplate.document_type == document_type)
        if is_active is not None:
            query = query.filter(DocumentTemplate.is_active == is_active)

        return query.order_by(DocumentTemplate.code).all()

    def get_default_template(
        self,
        country_code: str,
        document_type: DocumentType
    ) -> DocumentTemplate | None:
        """Récupère le template par défaut pour un type de document."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return None

        return self.db.query(DocumentTemplate).filter(
            DocumentTemplate.tenant_id == self.tenant_id,
            DocumentTemplate.country_pack_id == pack.id,
            DocumentTemplate.document_type == document_type,
            DocumentTemplate.is_default,
            DocumentTemplate.is_active
        ).first()

    # ========================================================================
    # GESTION DES CONFIGURATIONS BANCAIRES
    # ========================================================================

    def create_bank_config(
        self,
        country_pack_id: int,
        bank_format: BankFormat,
        code: str,
        name: str,
        description: str = None,
        iban_prefix: str = None,
        iban_length: int = None,
        bic_required: bool = True,
        export_format: str = "xml",
        export_encoding: str = "utf-8",
        export_template: str = None,
        config: dict = None,
        is_default: bool = False
    ) -> BankConfig:
        """Crée une configuration bancaire."""
        bank = BankConfig(
            tenant_id=self.tenant_id,
            country_pack_id=country_pack_id,
            bank_format=bank_format,
            code=code,
            name=name,
            description=description,
            iban_prefix=iban_prefix,
            iban_length=iban_length,
            bic_required=bic_required,
            export_format=export_format,
            export_encoding=export_encoding,
            export_template=export_template,
            config=config,
            is_default=is_default
        )
        self.db.add(bank)
        self.db.commit()
        self.db.refresh(bank)
        return bank

    def get_bank_configs(
        self,
        country_pack_id: int = None,
        bank_format: BankFormat = None
    ) -> list[BankConfig]:
        """Récupère les configurations bancaires."""
        query = self.db.query(BankConfig).filter(
            BankConfig.tenant_id == self.tenant_id,
            BankConfig.is_active
        )

        if country_pack_id:
            query = query.filter(BankConfig.country_pack_id == country_pack_id)
        if bank_format:
            query = query.filter(BankConfig.bank_format == bank_format)

        return query.order_by(BankConfig.code).all()

    def validate_iban(self, iban: str, country_code: str) -> dict[str, Any]:
        """Valide un IBAN pour un pays."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return {"valid": False, "error": "Country pack not found"}

        bank_config = self.db.query(BankConfig).filter(
            BankConfig.tenant_id == self.tenant_id,
            BankConfig.country_pack_id == pack.id,
            BankConfig.is_default
        ).first()

        if not bank_config:
            return {"valid": False, "error": "Bank config not found"}

        # Validation basique
        iban = iban.replace(" ", "").upper()

        if bank_config.iban_prefix and not iban.startswith(bank_config.iban_prefix):
            return {"valid": False, "error": f"IBAN should start with {bank_config.iban_prefix}"}

        if bank_config.iban_length and len(iban) != bank_config.iban_length:
            return {"valid": False, "error": f"IBAN should have {bank_config.iban_length} characters"}

        return {"valid": True, "formatted_iban": iban}

    # ========================================================================
    # GESTION DES JOURS FÉRIÉS
    # ========================================================================

    def create_holiday(
        self,
        country_pack_id: int,
        name: str,
        name_local: str = None,
        holiday_date: date = None,
        month: int = None,
        day: int = None,
        is_fixed: bool = True,
        calculation_rule: str = None,
        year: int = None,
        region: str = None,
        is_national: bool = True,
        is_work_day: bool = False,
        affects_banks: bool = True,
        affects_business: bool = True
    ) -> PublicHoliday:
        """Crée un jour férié."""
        holiday = PublicHoliday(
            tenant_id=self.tenant_id,
            country_pack_id=country_pack_id,
            name=name,
            name_local=name_local,
            holiday_date=holiday_date,
            month=month,
            day=day,
            is_fixed=is_fixed,
            calculation_rule=calculation_rule,
            year=year,
            region=region,
            is_national=is_national,
            is_work_day=is_work_day,
            affects_banks=affects_banks,
            affects_business=affects_business
        )
        self.db.add(holiday)
        self.db.commit()
        self.db.refresh(holiday)
        return holiday

    def get_holidays(
        self,
        country_pack_id: int = None,
        year: int = None,
        region: str = None
    ) -> list[PublicHoliday]:
        """Récupère les jours fériés."""
        query = self.db.query(PublicHoliday).filter(
            PublicHoliday.tenant_id == self.tenant_id,
            PublicHoliday.is_active
        )

        if country_pack_id:
            query = query.filter(PublicHoliday.country_pack_id == country_pack_id)
        if year:
            query = query.filter(
                or_(
                    PublicHoliday.year == year,
                    PublicHoliday.year.is_(None)
                )
            )
        if region:
            query = query.filter(
                or_(
                    PublicHoliday.region == region,
                    PublicHoliday.is_national
                )
            )

        return query.order_by(PublicHoliday.month, PublicHoliday.day).all()

    def get_holidays_for_year(self, country_code: str, year: int) -> list[dict[str, Any]]:
        """Récupère les jours fériés pour une année avec dates calculées."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return []

        holidays = self.get_holidays(country_pack_id=pack.id, year=year)
        result = []

        for h in holidays:
            if h.is_fixed and h.month and h.day:
                try:
                    holiday_date = date(year, h.month, h.day)
                    result.append({
                        "id": h.id,
                        "name": h.name,
                        "name_local": h.name_local,
                        "date": holiday_date.isoformat(),
                        "is_work_day": h.is_work_day,
                        "affects_banks": h.affects_banks,
                        "region": h.region
                    })
                except ValueError:
                    pass  # Date invalide (ex: 31 février)
            elif h.holiday_date:
                result.append({
                    "id": h.id,
                    "name": h.name,
                    "name_local": h.name_local,
                    "date": h.holiday_date.isoformat(),
                    "is_work_day": h.is_work_day,
                    "affects_banks": h.affects_banks,
                    "region": h.region
                })

        return sorted(result, key=lambda x: x["date"])

    def is_holiday(self, check_date: date, country_code: str) -> bool:
        """Vérifie si une date est un jour férié."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return False

        # Vérifier par date exacte
        exact = self.db.query(PublicHoliday).filter(
            PublicHoliday.tenant_id == self.tenant_id,
            PublicHoliday.country_pack_id == pack.id,
            PublicHoliday.holiday_date == check_date,
            PublicHoliday.is_active
        ).first()

        if exact:
            return True

        # Vérifier par mois/jour
        recurring = self.db.query(PublicHoliday).filter(
            PublicHoliday.tenant_id == self.tenant_id,
            PublicHoliday.country_pack_id == pack.id,
            PublicHoliday.month == check_date.month,
            PublicHoliday.day == check_date.day,
            PublicHoliday.is_fixed,
            PublicHoliday.is_active
        ).first()

        return recurring is not None

    # ========================================================================
    # GESTION DES EXIGENCES LÉGALES
    # ========================================================================

    def create_legal_requirement(
        self,
        country_pack_id: int,
        category: str,
        code: str,
        name: str,
        description: str = None,
        requirement_type: str = None,
        frequency: str = None,
        deadline_rule: str = None,
        config: dict = None,
        legal_reference: str = None,
        effective_date: date = None,
        is_mandatory: bool = True
    ) -> LegalRequirement:
        """Crée une exigence légale."""
        req = LegalRequirement(
            tenant_id=self.tenant_id,
            country_pack_id=country_pack_id,
            category=category,
            code=code,
            name=name,
            description=description,
            requirement_type=requirement_type,
            frequency=frequency,
            deadline_rule=deadline_rule,
            config=config,
            legal_reference=legal_reference,
            effective_date=effective_date,
            is_mandatory=is_mandatory
        )
        self.db.add(req)
        self.db.commit()
        self.db.refresh(req)
        return req

    def get_legal_requirements(
        self,
        country_pack_id: int = None,
        category: str = None
    ) -> list[LegalRequirement]:
        """Récupère les exigences légales."""
        query = self.db.query(LegalRequirement).filter(
            LegalRequirement.tenant_id == self.tenant_id,
            LegalRequirement.is_active
        )

        if country_pack_id:
            query = query.filter(LegalRequirement.country_pack_id == country_pack_id)
        if category:
            query = query.filter(LegalRequirement.category == category)

        return query.order_by(LegalRequirement.category, LegalRequirement.code).all()

    # ========================================================================
    # GESTION DES PARAMÈTRES TENANT
    # ========================================================================

    def activate_country_for_tenant(
        self,
        country_pack_id: int,
        is_primary: bool = False,
        custom_config: dict = None,
        activated_by: int = None
    ) -> TenantCountrySettings:
        """Active un pack pays pour le tenant."""
        # Si primaire, désactiver l'ancien
        if is_primary:
            self.db.query(TenantCountrySettings).filter(
                TenantCountrySettings.tenant_id == self.tenant_id,
                TenantCountrySettings.is_primary
            ).update({"is_primary": False})

        # Vérifier si déjà activé
        existing = self.db.query(TenantCountrySettings).filter(
            TenantCountrySettings.tenant_id == self.tenant_id,
            TenantCountrySettings.country_pack_id == country_pack_id
        ).first()

        if existing:
            existing.is_primary = is_primary
            existing.is_active = True
            existing.custom_config = custom_config
            self.db.commit()
            self.db.refresh(existing)
            return existing

        settings = TenantCountrySettings(
            tenant_id=self.tenant_id,
            country_pack_id=country_pack_id,
            is_primary=is_primary,
            custom_config=custom_config,
            activated_by=activated_by
        )
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def get_tenant_countries(self, active_only: bool = True) -> list[TenantCountrySettings]:
        """Récupère les pays activés pour le tenant."""
        query = self.db.query(TenantCountrySettings).filter(
            TenantCountrySettings.tenant_id == self.tenant_id
        )

        if active_only:
            query = query.filter(TenantCountrySettings.is_active)

        return query.order_by(desc(TenantCountrySettings.is_primary)).all()

    def get_primary_country(self) -> CountryPack | None:
        """Récupère le pack pays principal du tenant."""
        settings = self.db.query(TenantCountrySettings).filter(
            TenantCountrySettings.tenant_id == self.tenant_id,
            TenantCountrySettings.is_primary,
            TenantCountrySettings.is_active
        ).first()

        if not settings:
            return self.get_default_pack()

        return self.get_country_pack(settings.country_pack_id)

    # ========================================================================
    # UTILITAIRES
    # ========================================================================

    def format_currency(self, amount: float, country_code: str) -> str:
        """Formate un montant selon les conventions du pays."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return f"{amount:.2f}"

        # Formater le nombre
        if pack.number_format == NumberFormatStyle.EU:
            formatted = f"{amount:,.2f}".replace(",", " ").replace(".", ",")
        elif pack.number_format == NumberFormatStyle.US:
            formatted = f"{amount:,.2f}"
        elif pack.number_format == NumberFormatStyle.CH:
            formatted = f"{amount:,.2f}".replace(",", "'")
        else:
            formatted = f"{amount:.2f}"

        # Ajouter le symbole
        symbol = pack.currency_symbol or pack.default_currency
        if pack.currency_position == "before":
            return f"{symbol} {formatted}"
        else:
            return f"{formatted} {symbol}"

    def format_date(self, d: date, country_code: str) -> str:
        """Formate une date selon les conventions du pays."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return d.isoformat()

        if pack.date_format == DateFormatStyle.DMY:
            return d.strftime("%d/%m/%Y")
        elif pack.date_format == DateFormatStyle.MDY:
            return d.strftime("%m/%d/%Y")
        elif pack.date_format == DateFormatStyle.YMD:
            return d.strftime("%Y-%m-%d")
        else:
            return d.isoformat()

    def get_country_summary(self, country_code: str) -> dict[str, Any]:
        """Récupère un résumé complet du pack pays."""
        pack = self.get_country_pack_by_code(country_code)
        if not pack:
            return {}

        vat_rates = self.get_vat_rates(country_code)
        templates = self.get_document_templates(country_pack_id=pack.id)
        bank_configs = self.get_bank_configs(country_pack_id=pack.id)
        holidays = self.get_holidays(country_pack_id=pack.id)
        requirements = self.get_legal_requirements(country_pack_id=pack.id)

        return {
            "country_code": pack.country_code,
            "country_name": pack.country_name,
            "currency": pack.default_currency,
            "language": pack.default_language,
            "timezone": pack.timezone,
            "vat_rates_count": len(vat_rates),
            "templates_count": len(templates),
            "bank_configs_count": len(bank_configs),
            "holidays_count": len(holidays),
            "requirements_count": len(requirements),
            "default_vat_rate": pack.default_vat_rate,
            "fiscal_year_start": f"{pack.fiscal_year_start_day}/{pack.fiscal_year_start_month}"
        }


def get_country_pack_service(db: Session, tenant_id: str) -> CountryPackService:
    """Factory pour obtenir une instance du service."""
    return CountryPackService(db, tenant_id)
