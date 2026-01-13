"""
AZALSCORE Enterprise Architecture
=================================
Module enterprise pour les fonctionnalités niveau Salesforce/SAP.

Ce module fournit:
- Observabilité niveau SRE (métriques, alertes, tracing)
- Scalabilité et résilience enterprise
- Gouvernance des tenants et SLA
- Sécurité et conformité RSSI-ready
- Operations industrielles (PRA/PCA)
- Tests de validation grands comptes

Version: 1.0.0
Target: Enterprise / CAC40 / ETI internationales
"""

__version__ = "1.0.0"
__enterprise_level__ = "salesforce-grade"

# Enterprise modules
from app.enterprise.sla import TenantTier, SLAConfig
from app.enterprise.governance import TenantGovernor
from app.enterprise.resilience import CircuitBreaker, BackPressure
