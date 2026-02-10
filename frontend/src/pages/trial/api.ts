/**
 * AZALSCORE - Trial Registration API
 * Hooks React Query pour les endpoints d'inscription
 */

import { useMutation, useQuery } from '@tanstack/react-query';
import type {
  TrialRegistrationRequest,
  TrialRegistrationResponse,
  TrialEmailVerificationResponse,
  TrialPaymentSetupResponse,
  TrialCompleteResponse,
  TrialPromoResponse,
  TrialPricingResponse,
  TrialRegistrationStatus,
} from './types';

const API_BASE = '/api/v2/public/trial';

// Helper for API calls
async function apiCall<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Une erreur est survenue' }));
    throw new Error(error.detail || 'Une erreur est survenue');
  }

  return response.json();
}

// Hook: Create registration
export function useCreateRegistration() {
  return useMutation<TrialRegistrationResponse, Error, TrialRegistrationRequest>({
    mutationFn: (data) =>
      apiCall<TrialRegistrationResponse>('/register', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  });
}

// Hook: Verify email
export function useVerifyEmail() {
  return useMutation<TrialEmailVerificationResponse, Error, { token: string }>({
    mutationFn: (data) =>
      apiCall<TrialEmailVerificationResponse>('/verify-email', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  });
}

// Hook: Resend verification email
export function useResendVerificationEmail() {
  return useMutation<{ success: boolean; message: string }, Error, { registration_id: string }>({
    mutationFn: (data) =>
      apiCall<{ success: boolean; message: string }>('/resend-verification', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  });
}

// Hook: Setup payment (Stripe)
export function usePaymentSetup() {
  return useMutation<TrialPaymentSetupResponse, Error, { registration_id: string }>({
    mutationFn: (data) =>
      apiCall<TrialPaymentSetupResponse>('/payment-setup', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  });
}

// Hook: Complete registration
export function useCompleteRegistration() {
  return useMutation<
    TrialCompleteResponse,
    Error,
    { registration_id: string; setup_intent_id: string }
  >({
    mutationFn: (data) =>
      apiCall<TrialCompleteResponse>('/complete', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  });
}

// Hook: Get pricing info
export function usePricing() {
  return useQuery<TrialPricingResponse, Error>({
    queryKey: ['trial', 'pricing'],
    queryFn: () => apiCall<TrialPricingResponse>('/pricing'),
    staleTime: 1000 * 60 * 60, // Cache for 1 hour
  });
}

// Hook: Get registration status
export function useRegistrationStatus(registrationId: string | null) {
  return useQuery<TrialRegistrationStatus, Error>({
    queryKey: ['trial', 'status', registrationId],
    queryFn: () => apiCall<TrialRegistrationStatus>(`/status/${registrationId}`),
    enabled: !!registrationId,
    refetchInterval: 5000, // Poll every 5 seconds
  });
}

// Hook: Apply promo code
export function useApplyPromoCode() {
  return useMutation<
    TrialPromoResponse,
    Error,
    { registration_id: string; promo_code: string }
  >({
    mutationFn: (data) =>
      apiCall<TrialPromoResponse>('/apply-promo', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  });
}
