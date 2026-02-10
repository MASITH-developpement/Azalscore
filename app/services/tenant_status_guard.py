"""
AZALS - Middleware de Vérification Statut Tenant
=================================================
CRITIQUE : Bloque l'accès aux tenants SUSPENDED, CANCELLED ou en fin de TRIAL.

Ce middleware DOIT être appelé sur TOUTES les routes protégées.
"""

from datetime import datetime
from functools import wraps
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_tenant_id, get_current_user
from app.core.logging_config import get_logger
from app.modules.tenants.models import Tenant, TenantStatus, TenantSubscription

logger = get_logger(__name__)


class TenantAccessError(HTTPException):
    """Exception pour accès tenant refusé."""
    pass


def get_tenant_with_status(
    tenant_id: str = Depends(get_tenant_id),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Récupère le tenant et vérifie son statut.
    
    Bloque si :
    - Tenant SUSPENDED (impayé)
    - Tenant CANCELLED
    - Tenant TRIAL avec trial_ends_at dépassé
    
    Raises:
        HTTPException 402: Paiement requis (trial expiré ou suspension)
        HTTPException 403: Compte annulé
        HTTPException 404: Tenant non trouvé
    """
    # Récupérer le tenant
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant:
        logger.warning(f"[TENANT_CHECK] Tenant non trouvé: {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Vérifier statut CANCELLED
    if tenant.status == TenantStatus.CANCELLED:
        logger.warning(f"[TENANT_CHECK] Accès refusé - Tenant annulé: {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "TENANT_CANCELLED",
                "message": "Ce compte a été annulé. Contactez le support pour le réactiver.",
                "support_email": "support@azalscore.com"
            }
        )
    
    # Vérifier statut SUSPENDED (impayé)
    if tenant.status == TenantStatus.SUSPENDED:
        logger.warning(f"[TENANT_CHECK] Accès refusé - Tenant suspendu: {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail={
                "code": "PAYMENT_REQUIRED",
                "message": "Votre abonnement est suspendu pour défaut de paiement.",
                "action": "Mettez à jour vos informations de paiement pour réactiver votre compte.",
                "billing_url": "/billing/update-payment"
            }
        )
    
    # Vérifier TRIAL expiré
    if tenant.status == TenantStatus.TRIAL:
        if tenant.trial_ends_at and tenant.trial_ends_at < datetime.utcnow():
            logger.warning(f"[TENANT_CHECK] Trial expiré: {tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "TRIAL_EXPIRED",
                    "message": "Votre période d'essai est terminée.",
                    "action": "Souscrivez un abonnement pour continuer.",
                    "pricing_url": "/pricing",
                    "trial_ended_at": tenant.trial_ends_at.isoformat()
                }
            )
    
    # Vérifier statut PENDING (onboarding non terminé)
    if tenant.status == TenantStatus.PENDING:
        # On laisse passer mais on log
        logger.info(f"[TENANT_CHECK] Tenant en attente d'activation: {tenant_id}")
    
    return tenant


def require_active_subscription(
    tenant: Tenant = Depends(get_tenant_with_status),
    db: Session = Depends(get_db)
) -> Tenant:
    """
    Vérifie que le tenant a un abonnement actif et valide.
    
    Plus strict que get_tenant_with_status :
    - Vérifie qu'un abonnement existe
    - Vérifie que l'abonnement n'est pas expiré
    """
    # Récupérer l'abonnement actif
    subscription = db.query(TenantSubscription).filter(
        TenantSubscription.tenant_id == tenant.tenant_id,
        TenantSubscription.is_active == True
    ).first()
    
    # Si en trial, pas besoin d'abonnement
    if tenant.status == TenantStatus.TRIAL:
        return tenant
    
    # Si ACTIVE, vérifier l'abonnement
    if tenant.status == TenantStatus.ACTIVE:
        if not subscription:
            logger.error(f"[TENANT_CHECK] Tenant ACTIVE sans abonnement: {tenant.tenant_id}")
            # Cas anormal - ne devrait pas arriver
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "NO_SUBSCRIPTION",
                    "message": "Aucun abonnement actif trouvé.",
                    "action": "Contactez le support.",
                    "support_email": "support@azalscore.com"
                }
            )
        
        # Vérifier date d'expiration
        if subscription.ends_at and subscription.ends_at < datetime.utcnow():
            logger.warning(f"[TENANT_CHECK] Abonnement expiré: {tenant.tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "code": "SUBSCRIPTION_EXPIRED",
                    "message": "Votre abonnement a expiré.",
                    "expired_at": subscription.ends_at.isoformat(),
                    "action": "Renouvelez votre abonnement.",
                    "billing_url": "/billing"
                }
            )
    
    return tenant


def check_module_access(module_code: str):
    """
    Décorateur pour vérifier l'accès à un module spécifique.
    
    Usage:
        @router.get("/invoices")
        @check_module_access("M1")  # Module Commercial
        def list_invoices(...):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, tenant: Tenant = Depends(get_tenant_with_status), 
                         db: Session = Depends(get_db), **kwargs):
            from app.modules.tenants.models import TenantModule, ModuleStatus
            
            # Vérifier si le module est activé pour ce tenant
            module = db.query(TenantModule).filter(
                TenantModule.tenant_id == tenant.tenant_id,
                TenantModule.module_code == module_code,
                TenantModule.status == ModuleStatus.ACTIVE
            ).first()
            
            if not module:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "code": "MODULE_NOT_ENABLED",
                        "message": f"Le module {module_code} n'est pas activé pour votre compte.",
                        "module_code": module_code,
                        "action": "Mettez à niveau votre abonnement pour accéder à ce module.",
                        "upgrade_url": "/billing/upgrade"
                    }
                )
            
            return await func(*args, tenant=tenant, db=db, **kwargs)
        return wrapper
    return decorator


def check_user_limit(
    tenant: Tenant = Depends(get_tenant_with_status),
    db: Session = Depends(get_db)
) -> bool:
    """
    Vérifie si le tenant peut encore ajouter des utilisateurs.
    
    À utiliser avant la création d'un utilisateur.
    """
    from app.core.models import User
    
    current_users = db.query(User).filter(
        User.tenant_id == tenant.tenant_id,
        User.is_active == True
    ).count()
    
    if tenant.max_users > 0 and current_users >= tenant.max_users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "USER_LIMIT_REACHED",
                "message": f"Limite d'utilisateurs atteinte ({tenant.max_users}).",
                "current_users": current_users,
                "max_users": tenant.max_users,
                "action": "Mettez à niveau votre abonnement pour ajouter plus d'utilisateurs.",
                "upgrade_url": "/billing/upgrade"
            }
        )
    
    return True


def check_storage_limit(
    required_gb: float,
    tenant: Tenant = Depends(get_tenant_with_status)
) -> bool:
    """
    Vérifie si le tenant a assez de stockage disponible.
    
    Args:
        required_gb: Espace nécessaire en Go
    """
    available = tenant.max_storage_gb - (tenant.storage_used_gb or 0)
    
    if required_gb > available:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "STORAGE_LIMIT_REACHED",
                "message": "Espace de stockage insuffisant.",
                "used_gb": tenant.storage_used_gb,
                "max_gb": tenant.max_storage_gb,
                "required_gb": required_gb,
                "action": "Mettez à niveau votre abonnement pour plus d'espace.",
                "upgrade_url": "/billing/upgrade"
            }
        )
    
    return True


# ============================================================================
# FONCTIONS DE GESTION DU STATUT TENANT
# ============================================================================

def suspend_tenant(db: Session, tenant_id: str, reason: str = "payment_failed") -> bool:
    """
    Suspendre un tenant (appelé par le webhook Stripe en cas d'impayé).
    
    Args:
        db: Session SQLAlchemy
        tenant_id: ID du tenant à suspendre
        reason: Raison de la suspension
        
    Returns:
        True si suspendu, False si erreur
    """
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant:
        logger.error(f"[SUSPEND] Tenant non trouvé: {tenant_id}")
        return False
    
    tenant.status = TenantStatus.SUSPENDED
    tenant.suspended_at = datetime.utcnow()
    
    # Ajouter un event d'audit
    from app.modules.tenants.models import TenantEvent
    import uuid as uuid_module
    event = TenantEvent(
        tenant_id=tenant_id,
        event_type="TENANT_SUSPENDED",
        event_data={"reason": reason},
        description=f"Tenant suspendu: {reason}",
        actor_id=uuid_module.UUID("00000000-0000-0000-0000-000000000000"),  # System
        actor_email="system@azalscore.com"
    )
    db.add(event)
    
    db.commit()
    
    logger.warning(f"[SUSPEND] Tenant suspendu: {tenant_id} - Raison: {reason}")
    return True


def reactivate_tenant(db: Session, tenant_id: str) -> bool:
    """
    Réactiver un tenant après régularisation du paiement.
    
    Args:
        db: Session SQLAlchemy
        tenant_id: ID du tenant à réactiver
        
    Returns:
        True si réactivé, False si erreur
    """
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant:
        logger.error(f"[REACTIVATE] Tenant non trouvé: {tenant_id}")
        return False
    
    tenant.status = TenantStatus.ACTIVE
    tenant.suspended_at = None
    
    # Ajouter un event d'audit
    from app.modules.tenants.models import TenantEvent
    import uuid as uuid_module
    event = TenantEvent(
        tenant_id=tenant_id,
        event_type="TENANT_REACTIVATED",
        event_data={},
        description="Tenant réactivé après régularisation",
        actor_id=uuid_module.UUID("00000000-0000-0000-0000-000000000000"),  # System
        actor_email="system@azalscore.com"
    )
    db.add(event)
    
    db.commit()
    
    logger.info(f"[REACTIVATE] Tenant réactivé: {tenant_id}")
    return True


def convert_trial_to_active(db: Session, tenant_id: str, plan: str) -> bool:
    """
    Convertir un tenant TRIAL en ACTIVE après paiement.
    
    Args:
        db: Session SQLAlchemy
        tenant_id: ID du tenant
        plan: Plan souscrit (STARTER, PROFESSIONAL, ENTERPRISE)
        
    Returns:
        True si converti, False si erreur
    """
    from app.modules.tenants.models import SubscriptionPlan
    
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    
    if not tenant:
        logger.error(f"[CONVERT] Tenant non trouvé: {tenant_id}")
        return False
    
    # Mettre à jour le statut
    tenant.status = TenantStatus.ACTIVE
    tenant.activated_at = datetime.utcnow()
    
    # Mettre à jour le plan
    try:
        tenant.plan = SubscriptionPlan(plan.upper())
    except ValueError:
        tenant.plan = SubscriptionPlan.STARTER
    
    # Mettre à jour les limites selon le plan
    plan_limits = {
        "STARTER": {"max_users": 5, "max_storage_gb": 10},
        "PROFESSIONAL": {"max_users": 25, "max_storage_gb": 50},
        "ENTERPRISE": {"max_users": -1, "max_storage_gb": 500},  # -1 = illimité
    }
    
    limits = plan_limits.get(plan.upper(), plan_limits["STARTER"])
    tenant.max_users = limits["max_users"]
    tenant.max_storage_gb = limits["max_storage_gb"]
    
    # Ajouter un event d'audit
    from app.modules.tenants.models import TenantEvent
    import uuid as uuid_module
    event = TenantEvent(
        tenant_id=tenant_id,
        event_type="TRIAL_CONVERTED",
        event_data={"plan": plan},
        description=f"Essai converti en abonnement {plan}",
        actor_id=uuid_module.UUID("00000000-0000-0000-0000-000000000000"),  # System
        actor_email="system@azalscore.com"
    )
    db.add(event)
    
    db.commit()
    
    logger.info(f"[CONVERT] Trial converti: {tenant_id} → Plan {plan}")
    return True
