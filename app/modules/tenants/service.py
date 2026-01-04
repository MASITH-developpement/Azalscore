"""
AZALS MODULE T9 - Service Tenants
==================================

Logique métier pour la gestion des tenants.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
import uuid
import secrets

from .models import (
    Tenant, TenantSubscription, TenantModule, TenantInvitation,
    TenantUsage, TenantEvent, TenantSettings, TenantOnboarding,
    TenantStatus, SubscriptionPlan, BillingCycle, ModuleStatus, InvitationStatus
)
from .schemas import (
    TenantCreate, TenantUpdate,
    SubscriptionCreate, SubscriptionUpdate,
    ModuleActivation,
    TenantInvitationCreate,
    TenantSettingsUpdate,
    OnboardingStepUpdate,
    ProvisionTenantRequest
)


class TenantService:
    """Service de gestion des tenants."""

    def __init__(self, db: Session, actor_id: Optional[int] = None, actor_email: Optional[str] = None):
        self.db = db
        self.actor_id = actor_id
        self.actor_email = actor_email

    # ========================================================================
    # TENANT CRUD
    # ========================================================================

    def create_tenant(self, data: TenantCreate) -> Tenant:
        """Créer un nouveau tenant."""
        tenant = Tenant(
            tenant_id=data.tenant_id,
            name=data.name,
            legal_name=data.legal_name,
            siret=data.siret,
            vat_number=data.vat_number,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            postal_code=data.postal_code,
            country=data.country,
            email=data.email,
            phone=data.phone,
            website=data.website,
            plan=SubscriptionPlan[data.plan],
            timezone=data.timezone,
            language=data.language,
            currency=data.currency,
            max_users=data.max_users,
            max_storage_gb=data.max_storage_gb,
            logo_url=data.logo_url,
            primary_color=data.primary_color,
            secondary_color=data.secondary_color,
            features=data.features,
            extra_data=data.extra_data,
            created_by=self.actor_email,
        )
        self.db.add(tenant)
        self.db.commit()
        self.db.refresh(tenant)

        # Créer les paramètres par défaut
        self._create_default_settings(data.tenant_id)

        # Créer l'onboarding
        self._create_onboarding(data.tenant_id)

        # Logger l'événement
        self._log_event(data.tenant_id, "tenant.created", {
            "name": data.name,
            "plan": data.plan,
        })

        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Récupérer un tenant par ID."""
        return self.db.query(Tenant).filter(
            Tenant.tenant_id == tenant_id
        ).first()

    def get_tenant_by_pk(self, pk: int) -> Optional[Tenant]:
        """Récupérer un tenant par clé primaire."""
        return self.db.query(Tenant).filter(Tenant.id == pk).first()

    def list_tenants(
        self,
        status: Optional[str] = None,
        plan: Optional[str] = None,
        country: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Tenant]:
        """Lister les tenants."""
        query = self.db.query(Tenant)

        if status:
            query = query.filter(Tenant.status == TenantStatus[status])
        if plan:
            query = query.filter(Tenant.plan == SubscriptionPlan[plan])
        if country:
            query = query.filter(Tenant.country == country)

        return query.order_by(Tenant.created_at.desc()).offset(skip).limit(limit).all()

    def update_tenant(self, tenant_id: str, data: TenantUpdate) -> Optional[Tenant]:
        """Mettre à jour un tenant."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(tenant, key, value)

        self.db.commit()
        self.db.refresh(tenant)

        self._log_event(tenant_id, "tenant.updated", update_data)
        return tenant

    def activate_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Activer un tenant."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        tenant.status = TenantStatus.ACTIVE
        tenant.activated_at = datetime.utcnow()
        tenant.suspended_at = None

        self.db.commit()
        self.db.refresh(tenant)

        self._log_event(tenant_id, "tenant.activated", {})
        return tenant

    def suspend_tenant(self, tenant_id: str, reason: str = None) -> Optional[Tenant]:
        """Suspendre un tenant."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        tenant.status = TenantStatus.SUSPENDED
        tenant.suspended_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(tenant)

        self._log_event(tenant_id, "tenant.suspended", {"reason": reason})
        return tenant

    def cancel_tenant(self, tenant_id: str, reason: str = None) -> Optional[Tenant]:
        """Annuler un tenant."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        tenant.status = TenantStatus.CANCELLED
        tenant.cancelled_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(tenant)

        self._log_event(tenant_id, "tenant.cancelled", {"reason": reason})
        return tenant

    def start_trial(self, tenant_id: str, days: int = 14) -> Optional[Tenant]:
        """Démarrer un essai gratuit."""
        tenant = self.get_tenant(tenant_id)
        if not tenant:
            return None

        tenant.status = TenantStatus.TRIAL
        tenant.trial_ends_at = datetime.utcnow() + timedelta(days=days)
        tenant.activated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(tenant)

        self._log_event(tenant_id, "tenant.trial_started", {"days": days})
        return tenant

    # ========================================================================
    # SUBSCRIPTIONS
    # ========================================================================

    def create_subscription(self, tenant_id: str, data: SubscriptionCreate) -> TenantSubscription:
        """Créer un abonnement."""
        subscription = TenantSubscription(
            tenant_id=tenant_id,
            plan=SubscriptionPlan[data.plan],
            billing_cycle=BillingCycle[data.billing_cycle],
            price_monthly=data.price_monthly,
            price_yearly=data.price_yearly,
            discount_percent=data.discount_percent,
            starts_at=data.starts_at,
            ends_at=data.ends_at,
            is_trial=data.is_trial,
            auto_renew=data.auto_renew,
            payment_method=data.payment_method,
        )

        # Calculer next_billing_at
        if data.billing_cycle == "MONTHLY":
            subscription.next_billing_at = data.starts_at + timedelta(days=30)
        elif data.billing_cycle == "QUARTERLY":
            subscription.next_billing_at = data.starts_at + timedelta(days=90)
        else:
            subscription.next_billing_at = data.starts_at + timedelta(days=365)

        self.db.add(subscription)
        self.db.commit()
        self.db.refresh(subscription)

        # Mettre à jour le plan du tenant
        tenant = self.get_tenant(tenant_id)
        if tenant:
            tenant.plan = SubscriptionPlan[data.plan]
            self.db.commit()

        self._log_event(tenant_id, "subscription.created", {
            "plan": data.plan,
            "billing_cycle": data.billing_cycle,
        })

        return subscription

    def get_active_subscription(self, tenant_id: str) -> Optional[TenantSubscription]:
        """Récupérer l'abonnement actif."""
        return self.db.query(TenantSubscription).filter(
            TenantSubscription.tenant_id == tenant_id,
            TenantSubscription.is_active == True
        ).first()

    def update_subscription(self, tenant_id: str, data: SubscriptionUpdate) -> Optional[TenantSubscription]:
        """Mettre à jour un abonnement."""
        subscription = self.get_active_subscription(tenant_id)
        if not subscription:
            return None

        update_data = data.model_dump(exclude_unset=True)
        if "plan" in update_data:
            update_data["plan"] = SubscriptionPlan[update_data["plan"]]
        if "billing_cycle" in update_data:
            update_data["billing_cycle"] = BillingCycle[update_data["billing_cycle"]]

        for key, value in update_data.items():
            setattr(subscription, key, value)

        self.db.commit()
        self.db.refresh(subscription)

        # Mettre à jour le plan du tenant si changé
        if "plan" in update_data:
            tenant = self.get_tenant(tenant_id)
            if tenant:
                tenant.plan = update_data["plan"]
                self.db.commit()

        self._log_event(tenant_id, "subscription.updated", update_data)
        return subscription

    # ========================================================================
    # MODULES
    # ========================================================================

    def activate_module(self, tenant_id: str, data: ModuleActivation) -> TenantModule:
        """Activer un module pour un tenant."""
        # Vérifier si déjà actif
        existing = self.db.query(TenantModule).filter(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_code == data.module_code
        ).first()

        if existing:
            if existing.status != ModuleStatus.ACTIVE:
                existing.status = ModuleStatus.ACTIVE
                existing.deactivated_at = None
                existing.activated_at = datetime.utcnow()
                self.db.commit()
            return existing

        module = TenantModule(
            tenant_id=tenant_id,
            module_code=data.module_code,
            module_name=data.module_name,
            config=data.config,
            limits=data.limits,
        )
        self.db.add(module)
        self.db.commit()
        self.db.refresh(module)

        self._log_event(tenant_id, "module.activated", {
            "module_code": data.module_code,
        })

        return module

    def deactivate_module(self, tenant_id: str, module_code: str) -> Optional[TenantModule]:
        """Désactiver un module."""
        module = self.db.query(TenantModule).filter(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_code == module_code
        ).first()

        if not module:
            return None

        module.status = ModuleStatus.DISABLED
        module.deactivated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(module)

        self._log_event(tenant_id, "module.deactivated", {
            "module_code": module_code,
        })

        return module

    def list_tenant_modules(self, tenant_id: str, active_only: bool = True) -> List[TenantModule]:
        """Lister les modules d'un tenant."""
        query = self.db.query(TenantModule).filter(
            TenantModule.tenant_id == tenant_id
        )

        if active_only:
            query = query.filter(TenantModule.status == ModuleStatus.ACTIVE)

        return query.all()

    def is_module_active(self, tenant_id: str, module_code: str) -> bool:
        """Vérifier si un module est actif."""
        module = self.db.query(TenantModule).filter(
            TenantModule.tenant_id == tenant_id,
            TenantModule.module_code == module_code,
            TenantModule.status == ModuleStatus.ACTIVE
        ).first()
        return module is not None

    # ========================================================================
    # INVITATIONS
    # ========================================================================

    def create_invitation(self, data: TenantInvitationCreate) -> TenantInvitation:
        """Créer une invitation."""
        invitation = TenantInvitation(
            token=secrets.token_urlsafe(32),
            email=data.email,
            tenant_id=data.tenant_id,
            tenant_name=data.tenant_name,
            plan=SubscriptionPlan[data.plan] if data.plan else None,
            proposed_role=data.proposed_role,
            expires_at=datetime.utcnow() + timedelta(days=data.expires_in_days),
            created_by=self.actor_email,
        )
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)

        self._log_event(
            data.tenant_id or "platform",
            "invitation.created",
            {"email": data.email}
        )

        return invitation

    def get_invitation_by_token(self, token: str) -> Optional[TenantInvitation]:
        """Récupérer une invitation par token."""
        return self.db.query(TenantInvitation).filter(
            TenantInvitation.token == token
        ).first()

    def accept_invitation(self, token: str) -> Optional[TenantInvitation]:
        """Accepter une invitation."""
        invitation = self.get_invitation_by_token(token)
        if not invitation:
            return None

        if invitation.status != InvitationStatus.PENDING:
            return None

        if invitation.expires_at < datetime.utcnow():
            invitation.status = InvitationStatus.EXPIRED
            self.db.commit()
            return None

        invitation.status = InvitationStatus.ACCEPTED
        invitation.accepted_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(invitation)

        return invitation

    # ========================================================================
    # USAGE & EVENTS
    # ========================================================================

    def record_usage(self, tenant_id: str, data: Dict[str, Any]) -> TenantUsage:
        """Enregistrer l'utilisation."""
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        usage = self.db.query(TenantUsage).filter(
            TenantUsage.tenant_id == tenant_id,
            TenantUsage.date == today,
            TenantUsage.period == "daily"
        ).first()

        if not usage:
            usage = TenantUsage(tenant_id=tenant_id, date=today)
            self.db.add(usage)

        for key, value in data.items():
            if hasattr(usage, key):
                setattr(usage, key, value)

        self.db.commit()
        self.db.refresh(usage)
        return usage

    def get_usage(
        self,
        tenant_id: str,
        start_date: datetime,
        end_date: datetime,
        period: str = "daily"
    ) -> List[TenantUsage]:
        """Récupérer l'utilisation sur une période."""
        return self.db.query(TenantUsage).filter(
            TenantUsage.tenant_id == tenant_id,
            TenantUsage.period == period,
            TenantUsage.date >= start_date,
            TenantUsage.date <= end_date
        ).order_by(TenantUsage.date).all()

    def _log_event(self, tenant_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Logger un événement."""
        event = TenantEvent(
            tenant_id=tenant_id,
            event_type=event_type,
            event_data=event_data,
            actor_id=self.actor_id,
            actor_email=self.actor_email,
        )
        self.db.add(event)
        self.db.commit()

    def get_events(
        self,
        tenant_id: str,
        event_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[TenantEvent]:
        """Récupérer les événements."""
        query = self.db.query(TenantEvent).filter(
            TenantEvent.tenant_id == tenant_id
        )

        if event_type:
            query = query.filter(TenantEvent.event_type == event_type)

        return query.order_by(TenantEvent.created_at.desc()).offset(skip).limit(limit).all()

    # ========================================================================
    # SETTINGS
    # ========================================================================

    def get_settings(self, tenant_id: str) -> Optional[TenantSettings]:
        """Récupérer les paramètres."""
        return self.db.query(TenantSettings).filter(
            TenantSettings.tenant_id == tenant_id
        ).first()

    def update_settings(self, tenant_id: str, data: TenantSettingsUpdate) -> TenantSettings:
        """Mettre à jour les paramètres."""
        settings = self.get_settings(tenant_id)

        if not settings:
            settings = TenantSettings(tenant_id=tenant_id)
            self.db.add(settings)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(settings, key, value)

        self.db.commit()
        self.db.refresh(settings)

        self._log_event(tenant_id, "settings.updated", update_data)
        return settings

    def _create_default_settings(self, tenant_id: str) -> TenantSettings:
        """Créer les paramètres par défaut."""
        settings = TenantSettings(tenant_id=tenant_id)
        self.db.add(settings)
        self.db.commit()
        return settings

    # ========================================================================
    # ONBOARDING
    # ========================================================================

    def get_onboarding(self, tenant_id: str) -> Optional[TenantOnboarding]:
        """Récupérer l'onboarding."""
        return self.db.query(TenantOnboarding).filter(
            TenantOnboarding.tenant_id == tenant_id
        ).first()

    def update_onboarding_step(self, tenant_id: str, data: OnboardingStepUpdate) -> Optional[TenantOnboarding]:
        """Mettre à jour une étape onboarding."""
        onboarding = self.get_onboarding(tenant_id)
        if not onboarding:
            return None

        # Mapper les étapes
        step_mapping = {
            "company_info": "company_info_completed",
            "admin": "admin_created",
            "users": "users_invited",
            "modules": "modules_configured",
            "country_pack": "country_pack_selected",
            "data_import": "first_data_imported",
            "training": "training_completed",
        }

        if data.step in step_mapping:
            setattr(onboarding, step_mapping[data.step], data.completed)

        # Calculer la progression
        completed_steps = sum([
            onboarding.company_info_completed,
            onboarding.admin_created,
            onboarding.users_invited,
            onboarding.modules_configured,
            onboarding.country_pack_selected,
            onboarding.first_data_imported,
            onboarding.training_completed,
        ])
        onboarding.progress_percent = int((completed_steps / 7) * 100)

        # Définir l'étape courante
        if not onboarding.company_info_completed:
            onboarding.current_step = "company_info"
        elif not onboarding.admin_created:
            onboarding.current_step = "admin"
        elif not onboarding.users_invited:
            onboarding.current_step = "users"
        elif not onboarding.modules_configured:
            onboarding.current_step = "modules"
        elif not onboarding.country_pack_selected:
            onboarding.current_step = "country_pack"
        elif not onboarding.first_data_imported:
            onboarding.current_step = "data_import"
        elif not onboarding.training_completed:
            onboarding.current_step = "training"
        else:
            onboarding.current_step = "completed"
            onboarding.completed_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(onboarding)

        return onboarding

    def _create_onboarding(self, tenant_id: str) -> TenantOnboarding:
        """Créer l'onboarding."""
        onboarding = TenantOnboarding(tenant_id=tenant_id)
        self.db.add(onboarding)
        self.db.commit()
        return onboarding

    # ========================================================================
    # PROVISIONING
    # ========================================================================

    def provision_tenant(self, data: ProvisionTenantRequest) -> Dict[str, Any]:
        """Provisionner un tenant complet."""
        # 1. Créer le tenant
        tenant = self.create_tenant(data.tenant)

        # 2. Démarrer l'essai ou activer
        self.start_trial(data.tenant.tenant_id, 14)

        # 3. Activer les modules demandés
        activated_modules = []
        for module_code in data.modules:
            self.activate_module(data.tenant.tenant_id, ModuleActivation(
                module_code=module_code,
                module_name=f"Module {module_code}"
            ))
            activated_modules.append(module_code)

        # 4. Générer mot de passe si nécessaire
        temp_password = data.admin_password or secrets.token_urlsafe(12)

        # 5. Mettre à jour l'onboarding
        onboarding = self.get_onboarding(data.tenant.tenant_id)
        if onboarding:
            onboarding.company_info_completed = True
            onboarding.admin_created = True
            onboarding.modules_configured = True
            onboarding.country_pack_selected = True
            onboarding.progress_percent = 57
            onboarding.current_step = "users"
            self.db.commit()

        # Logger
        self._log_event(data.tenant.tenant_id, "tenant.provisioned", {
            "admin_email": data.admin_email,
            "modules": activated_modules,
            "country_pack": data.country_pack,
        })

        return {
            "tenant": tenant,
            "admin_user_id": 0,  # Serait créé via IAM
            "admin_email": data.admin_email,
            "temporary_password": temp_password if not data.admin_password else None,
            "activated_modules": activated_modules,
            "onboarding_url": f"/onboarding/{data.tenant.tenant_id}",
        }

    def provision_masith(self) -> Dict[str, Any]:
        """Provisionner le tenant SAS MASITH (premier client)."""
        from . import FIRST_TENANT

        # Vérifier si déjà créé
        existing = self.get_tenant(FIRST_TENANT["id"])
        if existing:
            return {"tenant": existing, "already_exists": True}

        request = ProvisionTenantRequest(
            tenant=TenantCreate(
                tenant_id=FIRST_TENANT["id"],
                name=FIRST_TENANT["name"],
                legal_name="SAS MASITH",
                siret="12345678901234",
                country=FIRST_TENANT["country"],
                email="admin@masith.fr",
                plan=FIRST_TENANT["plan"],
            ),
            admin_email="admin@masith.fr",
            admin_first_name="Admin",
            admin_last_name="MASITH",
            modules=["T0", "T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"],
            country_pack="FR",
            send_welcome_email=False,
        )

        return self.provision_tenant(request)

    # ========================================================================
    # PLATFORM STATS
    # ========================================================================

    def get_platform_stats(self) -> Dict[str, Any]:
        """Statistiques globales de la plateforme."""
        total = self.db.query(Tenant).count()
        active = self.db.query(Tenant).filter(Tenant.status == TenantStatus.ACTIVE).count()
        trial = self.db.query(Tenant).filter(Tenant.status == TenantStatus.TRIAL).count()
        suspended = self.db.query(Tenant).filter(Tenant.status == TenantStatus.SUSPENDED).count()

        # Par plan
        plan_counts = self.db.query(
            Tenant.plan,
            func.count(Tenant.id)
        ).group_by(Tenant.plan).all()
        tenants_by_plan = {p.value: c for p, c in plan_counts}

        # Par pays
        country_counts = self.db.query(
            Tenant.country,
            func.count(Tenant.id)
        ).group_by(Tenant.country).all()
        tenants_by_country = {c: count for c, count in country_counts}

        # Nouveaux ce mois
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_this_month = self.db.query(Tenant).filter(
            Tenant.created_at >= month_start
        ).count()

        # Stockage total
        total_storage = self.db.query(func.sum(Tenant.storage_used_gb)).scalar() or 0

        return {
            "total_tenants": total,
            "active_tenants": active,
            "trial_tenants": trial,
            "suspended_tenants": suspended,
            "total_users": 0,  # Serait calculé via IAM
            "storage_used_gb": float(total_storage),
            "tenants_by_plan": tenants_by_plan,
            "tenants_by_country": tenants_by_country,
            "new_tenants_this_month": new_this_month,
            "revenue_this_month": 0,  # Serait calculé via facturation
        }


def get_tenant_service(
    db: Session,
    actor_id: Optional[int] = None,
    actor_email: Optional[str] = None
) -> TenantService:
    """Factory pour le service tenant."""
    return TenantService(db, actor_id, actor_email)
