/**
 * AZALSCORE - Trial Registration Types
 * Types TypeScript pour le flux d'inscription essai gratuit
 */

// Country and language options
export const COUNTRY_OPTIONS = [
  { value: 'FR', label: 'France' },
  { value: 'BE', label: 'Belgique' },
  { value: 'CH', label: 'Suisse' },
  { value: 'LU', label: 'Luxembourg' },
  { value: 'MC', label: 'Monaco' },
  { value: 'CA', label: 'Canada' },
] as const;

export const LANGUAGE_OPTIONS = [
  { value: 'fr', label: 'Francais' },
] as const;

export const REVENUE_RANGE_OPTIONS = [
  { value: '0-50k', label: '0 - 50 000 EUR' },
  { value: '50k-100k', label: '50 000 - 100 000 EUR' },
  { value: '100k-250k', label: '100 000 - 250 000 EUR' },
  { value: '250k-500k', label: '250 000 - 500 000 EUR' },
  { value: '500k-1m', label: '500 000 - 1 000 000 EUR' },
  { value: '1m-5m', label: '1 000 000 - 5 000 000 EUR' },
  { value: '5m+', label: 'Plus de 5 000 000 EUR' },
] as const;

// Step definitions
export type TrialStep =
  | 'personal'      // Step 1: Personal info
  | 'company'       // Step 2: Company info
  | 'pricing'       // Step 3: Pricing reminder
  | 'validation'    // Step 4: CGV/CGU + CAPTCHA
  | 'email'         // Step 5: Email verification
  | 'payment'       // Step 6: Stripe payment
  | 'success';      // Step 7: Success

export const TRIAL_STEPS: TrialStep[] = [
  'personal',
  'company',
  'pricing',
  'validation',
  'email',
  'payment',
  'success',
];

export const STEP_TITLES: Record<TrialStep, string> = {
  personal: 'Informations personnelles',
  company: 'Votre entreprise',
  pricing: 'Votre essai gratuit',
  validation: 'Validation',
  email: 'Verification email',
  payment: 'Paiement',
  success: 'Bienvenue !',
};

// Form data types
export interface PersonalInfo {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  mobile: string;
}

export interface CompanyInfo {
  companyName: string;
  addressLine1: string;
  addressLine2: string;
  postalCode: string;
  city: string;
  country: string;
  language: string;
  activity: string;
  revenueRange: string;
  maxUsers: number;
  siret: string;
}

export interface ValidationInfo {
  cgvAccepted: boolean;
  cguAccepted: boolean;
  captchaToken: string;
}

// Combined form state
export interface TrialFormData {
  personal: PersonalInfo;
  company: CompanyInfo;
  validation: ValidationInfo;
}

// API Request/Response types
export interface TrialRegistrationRequest {
  first_name: string;
  last_name: string;
  email: string;
  phone: string | null;
  mobile: string | null;
  company_name: string;
  address_line1: string;
  address_line2: string | null;
  postal_code: string;
  city: string;
  country: string;
  language: string;
  activity: string | null;
  revenue_range: string | null;
  max_users: number;
  siret: string | null;
  cgv_accepted: boolean;
  cgu_accepted: boolean;
  captcha_token: string;
}

export interface TrialRegistrationResponse {
  registration_id: string;
  email: string;
  email_sent: boolean;
  expires_at: string;
  message: string;
}

export interface TrialEmailVerificationResponse {
  verified: boolean;
  registration_id: string;
  message: string;
}

export interface TrialPaymentSetupResponse {
  client_secret: string;
  setup_intent_id: string;
  publishable_key: string;
  customer_id: string;
}

export interface TrialCompleteResponse {
  success: boolean;
  tenant_id: string;
  tenant_name: string;
  admin_email: string;
  temporary_password: string;
  login_url: string;
  trial_ends_at: string;
  message: string;
}

export interface TrialPricingPlan {
  name: string;
  code: string;
  monthly_price: number;
  yearly_price: number;
  currency: string;
  max_users: number;
  max_storage_gb: number;
  features: string[];
  is_popular: boolean;
}

export interface TrialPricingResponse {
  trial_days: number;
  plans: TrialPricingPlan[];
  currency: string;
  vat_included: boolean;
  message: string;
}

export interface TrialRegistrationStatus {
  registration_id: string;
  status: string;
  email: string;
  email_verified: boolean;
  captcha_verified: boolean;
  payment_setup_complete: boolean;
  expires_at: string;
  is_expired: boolean;
}

// Initial form state
export const initialFormData: TrialFormData = {
  personal: {
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    mobile: '',
  },
  company: {
    companyName: '',
    addressLine1: '',
    addressLine2: '',
    postalCode: '',
    city: '',
    country: 'FR',
    language: 'fr',
    activity: '',
    revenueRange: '',
    maxUsers: 5,
    siret: '',
  },
  validation: {
    cgvAccepted: false,
    cguAccepted: false,
    captchaToken: '',
  },
};
