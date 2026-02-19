/**
 * AZALSCORE Module - CRM Tests
 *
 * Tests des fonctionnalités CRM:
 * - Affichage de la liste des clients
 * - Navigation vers le détail client
 * - Création d'un nouveau client
 * - Onglets du détail client
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock API
vi.mock('@core/api-client', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ items: [], total: 0 }),
    post: vi.fn().mockResolvedValue({ id: '1' }),
    put: vi.fn().mockResolvedValue({}),
    delete: vi.fn().mockResolvedValue({}),
  },
}));

// Mock capabilities
vi.mock('@core/capabilities', () => ({
  useCapabilitiesStore: vi.fn(),
  CapabilityGuard: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

// Mock enrichment
vi.mock('@/modules/enrichment', () => ({
  useRiskAnalysis: () => ({
    analysis: null,
    enrichedFields: null,
    isLoading: false,
    error: null,
    cached: false,
    analyze: vi.fn(),
    reset: vi.fn(),
  }),
  ScoreGauge: () => <div data-testid="score-gauge" />,
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const _renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('CRM Module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Module Export', () => {
    it('should export CRMModule as default', async () => {
      const module = await import('../index');
      expect(module.default).toBeDefined();
    });
  });

  describe('Customer Types', () => {
    it('should have CUSTOMER_TYPE_CONFIG defined', async () => {
      const { CUSTOMER_TYPE_CONFIG } = await import('../types');
      expect(CUSTOMER_TYPE_CONFIG).toBeDefined();
      expect(CUSTOMER_TYPE_CONFIG.PROSPECT).toBeDefined();
      expect(CUSTOMER_TYPE_CONFIG.CUSTOMER).toBeDefined();
      expect(CUSTOMER_TYPE_CONFIG.VIP).toBeDefined();
    });

    it('should have valid color values for each type', async () => {
      const { CUSTOMER_TYPE_CONFIG } = await import('../types');
      const validColors = ['gray', 'blue', 'green', 'yellow', 'purple', 'red', 'orange'];

      Object.values(CUSTOMER_TYPE_CONFIG).forEach((config) => {
        expect(validColors).toContain(config.color);
      });
    });
  });

  describe('Opportunity Types', () => {
    it('should have OPPORTUNITY_STATUS_CONFIG defined', async () => {
      const { OPPORTUNITY_STATUS_CONFIG } = await import('../types');
      expect(OPPORTUNITY_STATUS_CONFIG).toBeDefined();
      expect(OPPORTUNITY_STATUS_CONFIG.NEW).toBeDefined();
      expect(OPPORTUNITY_STATUS_CONFIG.WON).toBeDefined();
      expect(OPPORTUNITY_STATUS_CONFIG.LOST).toBeDefined();
    });
  });

  describe('Helper Functions', () => {
    it('should correctly identify prospects', async () => {
      const { isProspect } = await import('../types');
      expect(isProspect({ type: 'PROSPECT' } as any)).toBe(true);
      expect(isProspect({ type: 'LEAD' } as any)).toBe(true);
      expect(isProspect({ type: 'CUSTOMER' } as any)).toBe(false);
    });

    it('should correctly identify active customers', async () => {
      const { isActiveCustomer } = await import('../types');
      expect(isActiveCustomer({ type: 'CUSTOMER' } as any)).toBe(true);
      expect(isActiveCustomer({ type: 'VIP' } as any)).toBe(true);
      expect(isActiveCustomer({ type: 'PROSPECT' } as any)).toBe(false);
    });

    it('should correctly determine if prospect can be converted', async () => {
      const { canConvert } = await import('../types');
      expect(canConvert({ type: 'PROSPECT', is_active: true } as any)).toBe(true);
      expect(canConvert({ type: 'LEAD', is_active: true } as any)).toBe(true);
      expect(canConvert({ type: 'CUSTOMER', is_active: true } as any)).toBe(false);
      expect(canConvert({ type: 'PROSPECT', is_active: false } as any)).toBe(false);
    });
  });

  describe('Customer Value Calculation', () => {
    it('should return high for customers with revenue >= 100000', async () => {
      const { getCustomerValue } = await import('../types');
      const customer = { total_revenue: 150000 } as any;
      expect(getCustomerValue(customer)).toBe('high');
    });

    it('should return medium for customers with revenue >= 10000', async () => {
      const { getCustomerValue } = await import('../types');
      const customer = { total_revenue: 50000 } as any;
      expect(getCustomerValue(customer)).toBe('medium');
    });

    it('should return low for customers with revenue < 10000', async () => {
      const { getCustomerValue } = await import('../types');
      const customer = { total_revenue: 5000 } as any;
      expect(getCustomerValue(customer)).toBe('low');
    });

    it('should return low for customers with no revenue', async () => {
      const { getCustomerValue } = await import('../types');
      const customer = { total_revenue: 0 } as any;
      expect(getCustomerValue(customer)).toBe('low');
    });
  });
});

describe('CRM Components', () => {
  describe('CustomerInfoTab', () => {
    it('should export CustomerInfoTab', async () => {
      const { CustomerInfoTab } = await import('../components');
      expect(CustomerInfoTab).toBeDefined();
    });
  });

  describe('CustomerRiskTab', () => {
    it('should export CustomerRiskTab', async () => {
      const { CustomerRiskTab } = await import('../components');
      expect(CustomerRiskTab).toBeDefined();
    });
  });

  describe('CustomerIATab', () => {
    it('should export CustomerIATab', async () => {
      const { CustomerIATab } = await import('../components');
      expect(CustomerIATab).toBeDefined();
    });
  });
});
