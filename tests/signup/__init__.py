"""
AZALSCORE - Suite de Tests
===========================

Structure des tests:
- test_signup_service.py   : Tests du service d'inscription
- test_signup_router.py    : Tests des endpoints signup
- test_tenant_guard.py     : Tests du blocage impayés
- test_stripe_webhooks.py  : Tests des webhooks Stripe
- test_email_service.py    : Tests du service email
- test_e2e.py              : Tests end-to-end

Exécution:
    pytest tests/ -v                    # Tous les tests
    pytest tests/test_signup_service.py # Un fichier spécifique
    ./tests/run_tests.sh coverage       # Avec rapport de couverture

Fixtures disponibles (dans conftest.py):
    - db                    : Session de base de données
    - client                : Client de test FastAPI
    - sample_tenant         : Tenant actif de test
    - trial_tenant          : Tenant en période d'essai
    - suspended_tenant      : Tenant suspendu
    - sample_user           : Utilisateur de test
    - auth_headers          : Headers avec JWT valide
    - mock_stripe           : Mock du module Stripe
    - mock_email_service    : Mock du service email
"""
