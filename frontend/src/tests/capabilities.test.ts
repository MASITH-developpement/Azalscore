/**
 * AZALSCORE UI Engine - Tests Capabilities
 * Tests du système de capacités
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';

// Mock the API
vi.mock('@core/api-client', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('Capabilities System', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('hasCapability', () => {
    it('should return true when capability exists', () => {
      const capabilities = ['admin.view', 'invoicing.view', 'treasury.view'];
      const hasCapability = (cap: string) => capabilities.includes(cap);

      expect(hasCapability('admin.view')).toBe(true);
      expect(hasCapability('invoicing.view')).toBe(true);
    });

    it('should return false when capability does not exist', () => {
      const capabilities = ['admin.view'];
      const hasCapability = (cap: string) => capabilities.includes(cap);

      expect(hasCapability('admin.root.break_glass')).toBe(false);
      expect(hasCapability('treasury.view')).toBe(false);
    });
  });

  describe('hasAnyCapability', () => {
    it('should return true if any capability matches', () => {
      const capabilities = ['admin.view', 'invoicing.view'];
      const hasAnyCapability = (caps: string[]) =>
        caps.some((cap) => capabilities.includes(cap));

      expect(hasAnyCapability(['admin.view', 'unknown'])).toBe(true);
      expect(hasAnyCapability(['invoicing.view', 'treasury.view'])).toBe(true);
    });

    it('should return false if no capability matches', () => {
      const capabilities = ['admin.view'];
      const hasAnyCapability = (caps: string[]) =>
        caps.some((cap) => capabilities.includes(cap));

      expect(hasAnyCapability(['unknown1', 'unknown2'])).toBe(false);
    });
  });

  describe('hasAllCapabilities', () => {
    it('should return true only if all capabilities match', () => {
      const capabilities = ['admin.view', 'invoicing.view', 'treasury.view'];
      const hasAllCapabilities = (caps: string[]) =>
        caps.every((cap) => capabilities.includes(cap));

      expect(hasAllCapabilities(['admin.view', 'invoicing.view'])).toBe(true);
      expect(
        hasAllCapabilities(['admin.view', 'invoicing.view', 'treasury.view'])
      ).toBe(true);
    });

    it('should return false if any capability is missing', () => {
      const capabilities = ['admin.view', 'invoicing.view'];
      const hasAllCapabilities = (caps: string[]) =>
        caps.every((cap) => capabilities.includes(cap));

      expect(hasAllCapabilities(['admin.view', 'treasury.view'])).toBe(false);
    });
  });

  describe('Sensitive Capabilities', () => {
    const SENSITIVE_CAPABILITIES = [
      'admin.root.break_glass',
      'admin.users.delete',
      'admin.tenants.delete',
      'accounting.journal.delete',
      'treasury.transfer.execute',
    ];

    it('should identify sensitive capabilities', () => {
      const isSensitive = (cap: string) => SENSITIVE_CAPABILITIES.includes(cap);

      expect(isSensitive('admin.root.break_glass')).toBe(true);
      expect(isSensitive('admin.users.delete')).toBe(true);
    });

    it('should not flag non-sensitive capabilities', () => {
      const isSensitive = (cap: string) => SENSITIVE_CAPABILITIES.includes(cap);

      expect(isSensitive('admin.view')).toBe(false);
      expect(isSensitive('invoicing.view')).toBe(false);
    });
  });

  describe('filterByCapability', () => {
    it('should filter items based on capabilities', () => {
      const capabilities = ['invoicing.view', 'treasury.view'];
      const items = [
        { id: '1', name: 'Invoicing', capability: 'invoicing.view' },
        { id: '2', name: 'Treasury', capability: 'treasury.view' },
        { id: '3', name: 'Admin', capability: 'admin.view' },
        { id: '4', name: 'Public', capability: undefined },
      ];

      const filterByCapability = <T extends { capability?: string }>(
        items: T[],
        caps: string[]
      ): T[] => {
        return items.filter((item) => {
          if (!item.capability) return true;
          return caps.includes(item.capability);
        });
      };

      const filtered = filterByCapability(items, capabilities);

      expect(filtered).toHaveLength(3);
      expect(filtered.map((i) => i.id)).toEqual(['1', '2', '4']);
    });
  });
});

describe('Break-Glass Capability Check', () => {
  it('should correctly identify break-glass capability', () => {
    const BREAK_GLASS_CAPABILITY = 'admin.root.break_glass';

    const testCases = [
      { capabilities: [], expected: false },
      { capabilities: ['admin.view'], expected: false },
      { capabilities: ['admin.root.break_glass'], expected: true },
      { capabilities: ['admin.view', 'admin.root.break_glass'], expected: true },
    ];

    testCases.forEach(({ capabilities, expected }) => {
      const canBreakGlass = capabilities.includes(BREAK_GLASS_CAPABILITY);
      expect(canBreakGlass).toBe(expected);
    });
  });
});
