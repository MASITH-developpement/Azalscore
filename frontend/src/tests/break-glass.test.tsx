/**
 * AZALSCORE UI Engine - Tests Break-Glass
 *
 * Tests obligatoires:
 * - Test UI sans capacité break-glass → écran invisible
 * - Test avec capacité → flux complet accessible
 * - Test annulation à chaque niveau
 * - Test absence de logs UI persistants
 * - Test mobile (break-glass inaccessible si non admin root)
 * - Test résilience API indisponible
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useCapabilitiesStore } from '@core/capabilities';
import BreakGlassPage from '@modules/break-glass';

// Mock capabilities state
let mockCanBreakGlass = false;

// Mock stores
vi.mock('@core/capabilities', () => ({
  useCapabilitiesStore: vi.fn(),
  useCanBreakGlass: () => mockCanBreakGlass,
  CapabilityGuard: ({ children, capability }: { children: React.ReactNode; capability?: string }) => {
    if (capability === 'admin.root.break_glass' && !mockCanBreakGlass) {
      return null;
    }
    return <>{children}</>;
  },
}));

vi.mock('@core/audit-ui', () => ({
  trackBreakGlassEvent: vi.fn(),
}));

vi.mock('@core/api-client', () => ({
  api: {
    post: vi.fn(),
    get: vi.fn(),
  },
}));

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

const renderWithProviders = (ui: React.ReactElement) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{ui}</BrowserRouter>
    </QueryClientProvider>
  );
};

describe('Break-Glass Module', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCanBreakGlass = false;
    // Clear sessionStorage
    sessionStorage.clear();
    localStorage.clear();
  });

  afterEach(() => {
    vi.resetAllMocks();
  });

  describe('Visibility Tests', () => {
    it('should NOT render when user lacks admin.root.break_glass capability', () => {
      mockCanBreakGlass = false;

      const { container } = renderWithProviders(<BreakGlassPage />);

      // Should render nothing or redirect
      expect(container.innerHTML).toBe('');
    });

    it('should render when user HAS admin.root.break_glass capability', () => {
      mockCanBreakGlass = true;

      renderWithProviders(<BreakGlassPage />);

      // Should show Level 1 content
      expect(screen.getByText('Break-Glass Souverain')).toBeInTheDocument();
      expect(screen.getByText(/AVERTISSEMENT CRITIQUE/i)).toBeInTheDocument();
    });
  });

  describe('Flow Tests', () => {
    beforeEach(() => {
      mockCanBreakGlass = true;
    });

    it('should show Level 1 intention screen with warning', () => {
      renderWithProviders(<BreakGlassPage />);

      expect(screen.getByText('Break-Glass Souverain')).toBeInTheDocument();
      expect(screen.getByText(/AVERTISSEMENT CRITIQUE/i)).toBeInTheDocument();
      expect(screen.getByText('Déclencher une procédure Break-Glass')).toBeInTheDocument();
    });

    it('should show cancel button on Level 1', () => {
      renderWithProviders(<BreakGlassPage />);

      expect(screen.getByText('Annuler et quitter')).toBeInTheDocument();
    });

    it('should have proceed button on Level 1', () => {
      renderWithProviders(<BreakGlassPage />);

      const proceedButton = screen.getByText('Déclencher une procédure Break-Glass');
      expect(proceedButton).toBeInTheDocument();
      expect(proceedButton).not.toBeDisabled();
    });
  });

  describe('No Persistent Logs Tests', () => {
    beforeEach(() => {
      mockCanBreakGlass = true;
    });

    it('should NOT store anything in localStorage', () => {
      renderWithProviders(<BreakGlassPage />);

      // Verify no break-glass related data in localStorage
      const localStorageKeys = Object.keys(localStorage);
      const breakGlassKeys = localStorageKeys.filter(
        (key) => key.includes('break') || key.includes('glass')
      );
      expect(breakGlassKeys).toHaveLength(0);
    });

    it('should NOT store anything in sessionStorage', () => {
      renderWithProviders(<BreakGlassPage />);

      // Verify no break-glass related data in sessionStorage
      const sessionStorageKeys = Object.keys(sessionStorage);
      const breakGlassKeys = sessionStorageKeys.filter(
        (key) => key.includes('break') || key.includes('glass')
      );
      expect(breakGlassKeys).toHaveLength(0);
    });
  });

  describe('Mobile Tests', () => {
    it('should follow same capability rules on mobile', () => {
      // Mock mobile viewport
      Object.defineProperty(window, 'innerWidth', { value: 375, writable: true });

      mockCanBreakGlass = false;

      const { container } = renderWithProviders(<BreakGlassPage />);

      // Should not render on mobile without capability
      expect(container.innerHTML).toBe('');
    });
  });

  describe('API Resilience Tests', () => {
    it('should handle API errors gracefully', async () => {
      mockCanBreakGlass = true;

      // Mock API to fail
      const { api } = await import('@core/api-client');
      vi.mocked(api.post).mockRejectedValue(new Error('Network error'));

      renderWithProviders(<BreakGlassPage />);

      // Component should still render without crashing
      expect(screen.getByText('Break-Glass Souverain')).toBeInTheDocument();
    });
  });
});

describe('Capability Guard for Break-Glass', () => {
  beforeEach(() => {
    mockCanBreakGlass = false;
  });

  it('should hide break-glass from regular admin users', () => {
    const { container } = renderWithProviders(<BreakGlassPage />);

    // Break-glass should be completely hidden
    expect(container.querySelector('.azals-break-glass')).toBeNull();
  });
});
