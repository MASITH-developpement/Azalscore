/**
 * AZALSCORE Module - Country Packs France - React Query Hooks
 * API hooks pour PCG, TVA, FEC, DSN, RGPD
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@core/api-client';
import { serializeFilters } from '@core/query-keys';
import type {
  FrancePackStats, PCGAccount, FRVATRate, VATDeclaration,
  FECExport, DSNDeclaration, RGPDConsent, RGPDRequest, RGPDBreach,
  FECGenerateRequest
} from './types';

// ============================================================================
// QUERY KEYS FACTORY
// ============================================================================

export const franceKeys = {
  all: ['france'] as const,
  stats: () => [...franceKeys.all, 'stats'] as const,
  pcg: (filters?: { pcg_class?: string; active_only?: boolean }) =>
    [...franceKeys.all, 'pcg', serializeFilters(filters)] as const,
  vatRates: (activeOnly: boolean) => [...franceKeys.all, 'vat-rates', activeOnly] as const,
  vatDeclarations: (filters?: { status?: string }) =>
    [...franceKeys.all, 'vat-declarations', serializeFilters(filters)] as const,
  fec: (filters?: { status?: string; fiscal_year?: number }) =>
    [...franceKeys.all, 'fec', serializeFilters(filters)] as const,
  dsn: (filters?: { status?: string }) =>
    [...franceKeys.all, 'dsn', serializeFilters(filters)] as const,
  rgpd: () => [...franceKeys.all, 'rgpd'] as const,
  rgpdConsents: () => [...franceKeys.rgpd(), 'consents'] as const,
  rgpdRequests: (filters?: { type?: string; status?: string }) =>
    [...franceKeys.rgpd(), 'requests', serializeFilters(filters)] as const,
  rgpdBreaches: () => [...franceKeys.rgpd(), 'breaches'] as const,
};

// ============================================================================
// STATS
// ============================================================================

export const useFrancePackStats = () => {
  return useQuery({
    queryKey: franceKeys.stats(),
    queryFn: async () => {
      const response = await api.get<FrancePackStats>('/country-packs/france/stats');
      return response.data;
    }
  });
};

// ============================================================================
// PCG
// ============================================================================

export const usePCGAccounts = (filters?: { pcg_class?: string; active_only?: boolean }) => {
  return useQuery({
    queryKey: franceKeys.pcg(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.pcg_class) params.append('pcg_class', filters.pcg_class);
      if (filters?.active_only !== undefined) params.append('active_only', String(filters.active_only));
      const queryString = params.toString();
      const response = await api.get<PCGAccount[]>(
        `/country-packs/france/pcg/accounts${queryString ? `?${queryString}` : ''}`
      );
      return response.data;
    }
  });
};

// ============================================================================
// TVA
// ============================================================================

export const useVATRates = (active_only: boolean = true) => {
  return useQuery({
    queryKey: franceKeys.vatRates(active_only),
    queryFn: async () => {
      const response = await api.get<FRVATRate[]>(
        `/country-packs/france/tva/rates?active_only=${active_only}`
      );
      return response.data;
    }
  });
};

export const useVATDeclarations = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: franceKeys.vatDeclarations(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<VATDeclaration[]>(
        `/country-packs/france/tva/declarations${queryString ? `?${queryString}` : ''}`
      );
      return response.data;
    }
  });
};

export const useCalculateVATDeclaration = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (declarationId: number) => {
      return api.post(`/country-packs/france/tva/declarations/${declarationId}/calculate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: franceKeys.vatDeclarations() });
    }
  });
};

// ============================================================================
// FEC
// ============================================================================

export const useFECExports = (filters?: { status?: string; fiscal_year?: number }) => {
  return useQuery({
    queryKey: franceKeys.fec(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      if (filters?.fiscal_year) params.append('fiscal_year', String(filters.fiscal_year));
      const queryString = params.toString();
      const response = await api.get<FECExport[]>(
        `/country-packs/france/fec${queryString ? `?${queryString}` : ''}`
      );
      return response.data;
    }
  });
};

export const useGenerateFEC = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (data: FECGenerateRequest) => {
      return api.post('/country-packs/france/fec/generate', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: franceKeys.fec() });
      queryClient.invalidateQueries({ queryKey: franceKeys.stats() });
    }
  });
};

export const useValidateFEC = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (fecId: number) => {
      return api.post(`/country-packs/france/fec/${fecId}/validate`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: franceKeys.fec() });
    }
  });
};

// ============================================================================
// DSN
// ============================================================================

export const useDSNDeclarations = (filters?: { status?: string }) => {
  return useQuery({
    queryKey: franceKeys.dsn(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<DSNDeclaration[]>(
        `/country-packs/france/dsn${queryString ? `?${queryString}` : ''}`
      );
      return response.data;
    }
  });
};

export const useSubmitDSN = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dsnId: number) => {
      return api.post(`/country-packs/france/dsn/${dsnId}/submit`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: franceKeys.dsn() });
      queryClient.invalidateQueries({ queryKey: franceKeys.stats() });
    }
  });
};

// ============================================================================
// RGPD
// ============================================================================

export const useRGPDConsents = () => {
  return useQuery({
    queryKey: franceKeys.rgpdConsents(),
    queryFn: async () => {
      const response = await api.get<RGPDConsent[]>('/country-packs/france/rgpd/consents');
      return response.data;
    }
  });
};

export const useRGPDRequests = (filters?: { type?: string; status?: string }) => {
  return useQuery({
    queryKey: franceKeys.rgpdRequests(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.status) params.append('status', filters.status);
      const queryString = params.toString();
      const response = await api.get<RGPDRequest[]>(
        `/country-packs/france/rgpd/requests${queryString ? `?${queryString}` : ''}`
      );
      return response.data;
    }
  });
};

export const useRGPDBreaches = () => {
  return useQuery({
    queryKey: franceKeys.rgpdBreaches(),
    queryFn: async () => {
      const response = await api.get<RGPDBreach[]>('/country-packs/france/rgpd/breaches');
      return response.data;
    }
  });
};

export const useProcessRGPDRequest = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ requestId, response, data_exported, data_deleted }: {
      requestId: string;
      response?: string;
      data_exported?: boolean;
      data_deleted?: boolean;
    }) => {
      return api.post(`/country-packs/france/rgpd/requests/${requestId}/process`, {
        response,
        data_exported,
        data_deleted
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: franceKeys.rgpd() });
      queryClient.invalidateQueries({ queryKey: franceKeys.stats() });
    }
  });
};
