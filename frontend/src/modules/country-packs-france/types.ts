/**
 * AZALSCORE - Country Packs France Types
 * ========================================
 * Re-export des types depuis api.ts
 */

export type {
  // PCG
  PCGAccount,
  PCGAccountCreate,
  PCGAccountUpdate,
  // TVA
  FRVATRate,
  VATDeclaration,
  VATDeclarationCreate,
  // FEC
  FECExport,
  FECGenerateRequest,
  FECValidationResult,
  // DSN
  DSNDeclaration,
  DSNEmployeeData,
  DSNGenerateRequest,
  // RGPD
  RGPDConsent,
  RGPDConsentCreate,
  RGPDRequest,
  RGPDRequestCreate,
  RGPDProcessing,
  RGPDProcessingCreate,
  RGPDBreach,
  RGPDBreachCreate,
  // Contrats
  FRContract,
  FRContractCreate,
  // Stats
  FrancePackStats,
} from './api';
