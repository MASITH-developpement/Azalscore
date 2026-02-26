"""
AZALSCORE - Workflow Automation Templates
Templates de workflows prédéfinis
"""
from __future__ import annotations

from .builder import WorkflowBuilder
from .types import WorkflowDefinition


def create_invoice_approval_workflow(tenant_id: str) -> WorkflowDefinition:
    """Crée un workflow d'approbation de factures."""
    return (
        WorkflowBuilder("invoice_approval", "Approbation Factures", tenant_id)
        .description("Workflow d'approbation des factures fournisseurs")
        .for_entity("invoice")
        .on_event("invoice.created", [
            {"field": "type", "operator": "equals", "value": "supplier_invoice"},
            {"field": "amount_total", "operator": "greater_than", "value": 1000}
        ])
        .variable("approval_threshold", "decimal", 5000)
        .send_notification(
            recipients=["${entity.created_by}"],
            title="Facture en attente d'approbation",
            message="La facture ${entity.number} de ${entity.amount_total}€ nécessite une approbation"
        )
        .require_approval(
            approvers=["manager", "accountant"],
            approval_type="any",
            escalation_timeout_hours=48
        )
        .update_record(
            entity_type="invoice",
            entity_id="${__entity_id__}",
            updates={"status": "approved", "approved_at": "${__now__}"}
        )
        .send_notification(
            recipients=["${entity.created_by}"],
            title="Facture approuvée",
            message="La facture ${entity.number} a été approuvée"
        )
        .build()
    )


def create_expense_report_workflow(tenant_id: str) -> WorkflowDefinition:
    """Crée un workflow de notes de frais."""
    return (
        WorkflowBuilder("expense_report", "Notes de Frais", tenant_id)
        .description("Workflow de validation des notes de frais")
        .for_entity("expense_report")
        .on_event("expense_report.submitted")
        .variable("auto_approve_limit", "decimal", 100)
        .log("Nouvelle note de frais soumise: ${entity.id}")
        .require_approval(
            approvers=["${entity.manager_id}"],
            approval_type="all",
            require_comment=True
        )
        .update_record(
            entity_type="expense_report",
            entity_id="${__entity_id__}",
            updates={"status": "validated"}
        )
        .send_email(
            to="${entity.employee_email}",
            subject="Note de frais validée",
            body="Votre note de frais #${entity.id} a été validée pour un montant de ${entity.total}€"
        )
        .build()
    )


def create_customer_onboarding_workflow(tenant_id: str) -> WorkflowDefinition:
    """Crée un workflow d'onboarding client."""
    return (
        WorkflowBuilder("customer_onboarding", "Onboarding Client", tenant_id)
        .description("Workflow d'intégration des nouveaux clients")
        .for_entity("customer")
        .on_event("customer.created")
        .send_email(
            to="${entity.email}",
            subject="Bienvenue chez AZALSCORE",
            body="Bonjour ${entity.name}, bienvenue !"
        )
        .delay(seconds=86400)  # 1 jour
        .send_email(
            to="${entity.email}",
            subject="Premiers pas avec AZALSCORE",
            body="Découvrez nos fonctionnalités..."
        )
        .delay(seconds=259200)  # 3 jours
        .send_notification(
            recipients=["sales_team"],
            title="Suivi client",
            message="Le client ${entity.name} a été créé il y a 3 jours"
        )
        .build()
    )


def create_purchase_order_workflow(tenant_id: str) -> WorkflowDefinition:
    """Crée un workflow de validation des commandes d'achat."""
    return (
        WorkflowBuilder("purchase_order_approval", "Validation Commandes", tenant_id)
        .description("Workflow de validation des commandes fournisseurs")
        .for_entity("purchase_order")
        .on_event("purchase_order.created")
        .variable("approval_limit", "decimal", 2000)
        .log("Nouvelle commande créée: ${entity.number}")
        .require_approval(
            approvers=["purchasing_manager"],
            approval_type="any",
            escalation_timeout_hours=24
        )
        .update_record(
            entity_type="purchase_order",
            entity_id="${__entity_id__}",
            updates={"status": "validated", "validated_at": "${__now__}"}
        )
        .send_notification(
            recipients=["${entity.created_by}"],
            title="Commande validée",
            message="La commande ${entity.number} a été validée"
        )
        .build()
    )


def create_contract_renewal_workflow(tenant_id: str) -> WorkflowDefinition:
    """Crée un workflow de renouvellement de contrats."""
    return (
        WorkflowBuilder("contract_renewal", "Renouvellement Contrats", tenant_id)
        .description("Rappels de renouvellement de contrats")
        .for_entity("contract")
        .on_schedule("@daily")
        .log("Vérification des contrats à renouveler")
        .send_notification(
            recipients=["contract_manager"],
            title="Contrats à renouveler",
            message="Des contrats arrivent à échéance dans les 30 prochains jours"
        )
        .build()
    )
