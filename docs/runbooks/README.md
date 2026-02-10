# AZALSCORE - Runbooks Opérationnels

## Vue d'ensemble

Ce répertoire contient les runbooks pour la gestion des incidents et opérations AZALSCORE.

## Structure

| Runbook | Description | Criticité |
|---------|-------------|-----------|
| [database-incidents.md](./database-incidents.md) | Incidents base de données | CRITIQUE |
| [auth-incidents.md](./auth-incidents.md) | Incidents authentification | HAUTE |
| [performance-incidents.md](./performance-incidents.md) | Dégradation performance | HAUTE |
| [backup-restore.md](./backup-restore.md) | Procédures backup/restore | CRITIQUE |
| [security-incidents.md](./security-incidents.md) | Incidents sécurité | CRITIQUE |

## Contacts d'urgence

| Rôle | Contact | Disponibilité |
|------|---------|---------------|
| SRE On-Call | ops@azalscore.com | 24/7 |
| DBA | dba@azalscore.com | 24/7 |
| Security | security@azalscore.com | 24/7 |
| Management | escalation@azalscore.com | Heures ouvrées |

## Niveaux de sévérité

| Niveau | Définition | Temps de réponse |
|--------|------------|------------------|
| SEV1 | Service DOWN complet | 15 min |
| SEV2 | Dégradation majeure | 30 min |
| SEV3 | Dégradation mineure | 2h |
| SEV4 | Non-urgent | 24h |

## Utilisation

1. Identifier le type d'incident
2. Ouvrir le runbook correspondant
3. Suivre les étapes dans l'ordre
4. Documenter chaque action dans le ticket
5. Faire un post-mortem si SEV1/SEV2
