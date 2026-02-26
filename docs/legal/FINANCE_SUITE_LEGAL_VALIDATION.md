# AZALS - Validation Juridique Finance Suite (#28)

**Statut:** EN COURS DE DOCUMENTATION
**Responsable:** Direction / Juridique
**Date création:** 2026-02-17

---

## Vue d'ensemble

Ce document détaille les exigences légales et réglementaires pour le module Finance Suite d'AZALSCORE, destiné au marché français.

---

## 1. Conformité Comptable France

### 1.1 FEC - Fichier des Écritures Comptables

**Référence:** Article L47 A-I du LPF (Livre des Procédures Fiscales)

| Exigence | Implémentation | Statut |
|----------|----------------|--------|
| Format XML conforme | `app/modules/country_packs/france/fec_generator.py` | ✅ Implémenté |
| 18 champs obligatoires | Tous les champs présents | ✅ Vérifié |
| Export sur demande | Endpoint `/v1/france/fec/generate` | ✅ Implémenté |
| Intégrité données | Hash SHA-256 inclus | ✅ Implémenté |
| Période clôturée | Vérification avant export | ✅ Implémenté |

**Champs FEC obligatoires vérifiés:**
- [x] JournalCode
- [x] JournalLib
- [x] EcritureNum
- [x] EcritureDate
- [x] CompteNum
- [x] CompteLib
- [x] CompAuxNum
- [x] CompAuxLib
- [x] PieceRef
- [x] PieceDate
- [x] EcritureLib
- [x] Debit
- [x] Credit
- [x] EcritureLet
- [x] DateLet
- [x] ValidDate
- [x] Montantdevise
- [x] Idevise

**Action requise:** ⬜ Faire valider le format FEC par un expert-comptable

### 1.2 PCG - Plan Comptable Général

**Référence:** Règlement ANC 2014-03

| Exigence | Implémentation | Statut |
|----------|----------------|--------|
| Plan comptable standard | `app/modules/accounting/pcg_france.py` | ✅ Implémenté |
| Classes 1-7 définies | Toutes les classes | ✅ Vérifié |
| Comptes auxiliaires | Clients/Fournisseurs | ✅ Implémenté |
| Journaux obligatoires | AC, VE, BA, OD | ✅ Implémenté |

**Action requise:** ⬜ Valider la nomenclature PCG avec expert-comptable

---

## 2. Conformité TVA

### 2.1 Déclarations TVA

**Références:**
- Article 287 CGI
- BOI-TVA-DECLA

| Exigence | Implémentation | Statut |
|----------|----------------|--------|
| CA3 mensuelle/trimestrielle | `app/modules/country_packs/france/tva_declarations.py` | ✅ Implémenté |
| CA12 annuelle simplifiée | Même module | ✅ Implémenté |
| Calcul automatique TVA | Service TVA | ✅ Implémenté |
| Taux TVA France | 20%, 10%, 5.5%, 2.1% | ✅ Configurés |
| Export EDI-TVA | `app/modules/country_packs/france/edi_tva.py` | ✅ Implémenté |

### 2.2 Exigences Anti-Fraude TVA

**Référence:** Directive UE 2006/112/CE

| Exigence | Implémentation | Statut |
|----------|----------------|--------|
| Numéro TVA intra-communautaire | Validation VIES | ✅ Implémenté |
| Autoliquidation | Détection automatique | ✅ Implémenté |
| DEB/DES | Non requis (seuil) | ⬜ À implémenter si besoin |

---

## 3. Conformité NF525 (si module POS activé)

**Référence:**
- Article 286 CGI
- BOI-TVA-DECLA-30-10-30
- Norme NF Z42-013

| Exigence | Implémentation | Statut |
|----------|----------------|--------|
| Inaltérabilité | `app/modules/pos/nf525_compliance.py` | ✅ Implémenté |
| Sécurisation (signature) | Chaîne SHA-256 | ✅ Implémenté |
| Conservation 6 ans | Archivage automatique | ✅ Implémenté |
| Archivage périodique | Export sécurisé | ✅ Implémenté |
| Grand Total perpétuel | Totaux cumulatifs | ✅ Implémenté |
| Ticket Z obligatoire | Rapport Z quotidien | ✅ Implémenté |
| Certificat NF525 | **À OBTENIR** | ⬜ OBLIGATOIRE |

**Actions requises:**
1. ⬜ Sélectionner organisme certificateur (AFNOR, LNE, Infocert)
2. ⬜ Soumettre dossier de certification
3. ⬜ Passer l'audit de certification
4. ⬜ Obtenir le certificat NF525
5. ⬜ Afficher numéro de certificat dans l'application

**ATTENTION:** La commercialisation d'un logiciel de caisse sans certificat NF525 est passible d'une amende de 7 500€ par logiciel vendu.

---

## 4. Conformité RGPD

**Référence:** Règlement UE 2016/679

| Exigence | Implémentation | Statut |
|----------|----------------|--------|
| Registre des traitements | `app/modules/compliance/rgpd_audit.py` | ✅ Implémenté |
| Droit d'accès (Art. 15) | API `/v1/rgpd/data-access` | ✅ Implémenté |
| Droit de rectification (Art. 16) | API standard CRUD | ✅ Implémenté |
| Droit à l'effacement (Art. 17) | API `/v1/rgpd/erasure` | ✅ Implémenté |
| Droit à la portabilité (Art. 20) | Export JSON/CSV | ✅ Implémenté |
| Privacy by Design (Art. 25) | Architecture multi-tenant | ✅ Implémenté |
| Chiffrement (Art. 32) | AES-256, TLS 1.3 | ✅ Implémenté |
| DPO désigné (Art. 37) | **À DÉSIGNER** | ⬜ Si applicable |
| DPIA réalisée (Art. 35) | **À RÉALISER** | ⬜ Recommandé |

**Actions requises:**
1. ⬜ Désigner un DPO (si >250 salariés ou données sensibles)
2. ⬜ Réaliser une DPIA (Analyse d'Impact)
3. ⬜ Mettre à jour le registre des traitements
4. ⬜ Valider les durées de conservation

---

## 5. Conformité DSN (si module RH activé)

**Référence:** Décret n°2016-611

| Exigence | Implémentation | Statut |
|----------|----------------|--------|
| Format DSN-NEODES | `app/modules/country_packs/france/dsn_generator.py` | ✅ Implémenté |
| Blocs obligatoires | S10-S90 | ✅ Implémenté |
| Envoi net-entreprises | API intégrée | ✅ Implémenté |
| Certificat entreprise | **Configuration client** | ⬜ Par tenant |

---

## 6. Archivage Légal

**Références:**
- Article L123-22 Code de Commerce (10 ans)
- Article L102 B LPF (6 ans pour pièces fiscales)

| Exigence | Implémentation | Statut |
|----------|----------------|--------|
| Conservation 10 ans | Politique de rétention | ✅ Configuré |
| Intégrité garantie | Signature + Hash | ✅ Implémenté |
| Horodatage | Timestamp serveur | ✅ Implémenté |
| Non-répudiation | Audit trail complet | ✅ Implémenté |

**Recommandation:** Envisager certification NF Z42-013 pour l'archivage électronique.

---

## 7. Conditions Générales de Vente

### 7.1 Mentions Obligatoires

| Mention | Fichier | Statut |
|---------|---------|--------|
| Identité vendeur | `legal/mentions.html` | ✅ Présent |
| Coordonnées | `legal/mentions.html` | ✅ Présent |
| Prix TTC | `legal/cgv.html` | ⬜ À vérifier |
| Modalités de paiement | `legal/cgv.html` | ⬜ À vérifier |
| Droit de rétractation | `legal/cgv.html` | ⬜ À vérifier (B2B: non applicable) |
| Garantie légale | `legal/cgv.html` | ⬜ À vérifier |
| Médiation | `legal/cgv.html` | ⬜ À ajouter |

**Actions requises:**
1. ⬜ Faire relire CGV par avocat spécialisé
2. ⬜ Ajouter clause de médiation (obligatoire B2C)
3. ⬜ Valider les tarifs affichés

---

## 8. Checklist Validation Finale

### Avant Mise en Production

| Élément | Responsable | Statut |
|---------|-------------|--------|
| FEC validé par expert-comptable | Comptable | ⬜ |
| PCG validé | Comptable | ⬜ |
| Déclarations TVA testées | Comptable | ⬜ |
| NF525 certifié (si POS) | Direction | ⬜ |
| RGPD DPIA réalisée | DPO/Juridique | ⬜ |
| CGV validées par avocat | Juridique | ⬜ |
| Politique confidentialité validée | Juridique | ⬜ |
| Assurance RC Pro souscrite | Direction | ⬜ |

### Documents à Conserver

- [ ] Attestation expert-comptable sur conformité FEC
- [ ] Certificat NF525 (si applicable)
- [ ] DPIA signée
- [ ] Contrats sous-traitants (DPA)
- [ ] Registre des traitements à jour
- [ ] Attestation RC Pro

---

## 9. Contacts et Ressources

### Organismes de Référence

| Organisme | Contact | Objet |
|-----------|---------|-------|
| AFNOR Certification | certification@afnor.org | NF525 |
| LNE | certification@lne.fr | NF525 |
| CNIL | cnil.fr | RGPD |
| DGFIP | impots.gouv.fr | FEC, TVA |
| Net-Entreprises | net-entreprises.fr | DSN |

### Experts Recommandés

- Expert-comptable: [À compléter]
- Avocat RGPD: [À compléter]
- Avocat droit des affaires: [À compléter]

---

## 10. Calendrier Recommandé

| Étape | Délai | Priorité |
|-------|-------|----------|
| Validation FEC/PCG | 2 semaines | HAUTE |
| Certification NF525 | 2-3 mois | CRITIQUE (si POS) |
| DPIA RGPD | 1 mois | MOYENNE |
| Validation CGV | 2 semaines | HAUTE |
| Assurance RC Pro | 1 semaine | HAUTE |

---

*Document de suivi - Tâche #28 Phase 0*
*Dernière mise à jour: 2026-02-17*
