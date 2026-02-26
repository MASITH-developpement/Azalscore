"""
Implémentation du sous-programme : validate_cvv

RÈGLES STRICTES :
- Code métier PUR (pas de try/except)
- Pas de side effects
- Idempotent

Utilisation : 20+ endroits dans le codebase

SÉCURITÉ:
- Ne JAMAIS stocker le CVV (interdit par PCI-DSS)
- Ne JAMAIS logger le CVV
- Validation côté client uniquement (format)
- Le CVV réel est vérifié par le processeur de paiement
"""

from typing import Dict, Any


def execute(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valide le format d'un code CVV/CVC/CID.

    Le CVV (Card Verification Value) est un code de sécurité:
    - 3 chiffres pour Visa, Mastercard, Discover, JCB
    - 4 chiffres pour American Express (CID)

    IMPORTANT: Cette validation vérifie uniquement le FORMAT.
    La validation réelle du CVV est effectuée par le processeur de paiement.

    Args:
        inputs: {
            "cvv": string,  # Code CVV/CVC
            "card_type": string (optional),  # Type de carte pour longueur attendue
        }

    Returns:
        {
            "is_valid": boolean,  # True si le format est valide
            "error": string (optional),  # Message d'erreur si invalide
        }

    SÉCURITÉ (PCI-DSS):
    - Ne JAMAIS stocker le CVV
    - Ne JAMAIS logger le CVV (même masqué)
    - Utiliser uniquement pour validation côté formulaire
    """
    cvv = inputs.get("cvv", "")
    card_type = inputs.get("card_type", "").lower()

    # Convertir en string et nettoyer
    cvv_str = str(cvv).strip()

    # Vérifier que c'est non vide
    if not cvv_str:
        return {
            "is_valid": False,
            "error": "CVV requis"
        }

    # Vérifier que ce sont uniquement des chiffres
    if not cvv_str.isdigit():
        return {
            "is_valid": False,
            "error": "Le CVV ne doit contenir que des chiffres"
        }

    # Déterminer la longueur attendue
    # American Express: 4 chiffres (CID)
    # Autres cartes: 3 chiffres (CVV/CVC)
    if card_type == "amex":
        expected_length = 4
    else:
        # Par défaut, accepter 3 ou 4 chiffres si le type n'est pas spécifié
        if card_type:
            expected_length = 3
        else:
            # Sans type de carte, accepter 3 ou 4 chiffres
            if len(cvv_str) not in (3, 4):
                return {
                    "is_valid": False,
                    "error": "Le CVV doit contenir 3 ou 4 chiffres"
                }
            return {"is_valid": True}

    # Vérifier la longueur
    if len(cvv_str) != expected_length:
        return {
            "is_valid": False,
            "error": f"Le CVV doit contenir {expected_length} chiffres"
        }

    return {"is_valid": True}
