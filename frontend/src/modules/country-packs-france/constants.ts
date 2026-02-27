/**
 * AZALSCORE - Country Packs France Constants
 * ==========================================
 * Constantes pour le module France
 */

// Classes du Plan Comptable General
export const PCG_CLASSES = [
  { value: '1', label: 'Classe 1 - Comptes de capitaux' },
  { value: '2', label: 'Classe 2 - Comptes d\'immobilisations' },
  { value: '3', label: 'Classe 3 - Comptes de stocks' },
  { value: '4', label: 'Classe 4 - Comptes de tiers' },
  { value: '5', label: 'Classe 5 - Comptes financiers' },
  { value: '6', label: 'Classe 6 - Comptes de charges' },
  { value: '7', label: 'Classe 7 - Comptes de produits' },
  { value: '8', label: 'Classe 8 - Comptes speciaux' },
] as const;

// Statuts de declaration TVA
export const VAT_DECLARATION_STATUS = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'PENDING', label: 'En attente', color: 'blue' },
  { value: 'SUBMITTED', label: 'Soumise', color: 'green' },
  { value: 'VALIDATED', label: 'Validee', color: 'green' },
  { value: 'REJECTED', label: 'Rejetee', color: 'red' },
  { value: 'PAID', label: 'Payee', color: 'green' },
] as const;

// Statuts de declaration DSN
export const DSN_STATUS = [
  { value: 'DRAFT', label: 'Brouillon', color: 'gray' },
  { value: 'GENERATED', label: 'Generee', color: 'blue' },
  { value: 'SUBMITTED', label: 'Soumise', color: 'green' },
  { value: 'ACCEPTED', label: 'Acceptee', color: 'green' },
  { value: 'REJECTED', label: 'Rejetee', color: 'red' },
] as const;

// Types de requetes RGPD
export const RGPD_REQUEST_TYPES = [
  { value: 'ACCESS', label: 'Acces aux donnees' },
  { value: 'RECTIFICATION', label: 'Rectification' },
  { value: 'ERASURE', label: 'Effacement' },
  { value: 'PORTABILITY', label: 'Portabilite' },
  { value: 'RESTRICTION', label: 'Limitation du traitement' },
  { value: 'OBJECTION', label: 'Opposition' },
] as const;

// Statuts de requetes RGPD
export const RGPD_REQUEST_STATUS = [
  { value: 'PENDING', label: 'En attente', color: 'blue' },
  { value: 'PROCESSING', label: 'En cours', color: 'orange' },
  { value: 'COMPLETED', label: 'Traitee', color: 'green' },
  { value: 'REJECTED', label: 'Rejetee', color: 'red' },
] as const;

// Bases legales RGPD
export const RGPD_LEGAL_BASIS = [
  { value: 'CONSENT', label: 'Consentement' },
  { value: 'CONTRACT', label: 'Execution d\'un contrat' },
  { value: 'LEGAL_OBLIGATION', label: 'Obligation legale' },
  { value: 'VITAL_INTERESTS', label: 'Interets vitaux' },
  { value: 'PUBLIC_INTEREST', label: 'Interet public' },
  { value: 'LEGITIMATE_INTERESTS', label: 'Interets legitimes' },
] as const;

// Statuts FEC
export const FEC_STATUS = [
  { value: 'GENERATED', label: 'Genere', color: 'blue' },
  { value: 'VALIDATED', label: 'Valide', color: 'green' },
  { value: 'EXPORTED', label: 'Exporte', color: 'purple' },
] as const;

// Severite des violations de donnees
export const BREACH_SEVERITY = [
  { value: 'LOW', label: 'Faible', color: 'gray' },
  { value: 'MEDIUM', label: 'Moyenne', color: 'orange' },
  { value: 'HIGH', label: 'Elevee', color: 'red' },
  { value: 'CRITICAL', label: 'Critique', color: 'purple' },
] as const;
