/**
 * AZALSCORE UI Engine - useFocusTrap Hook
 * Traps keyboard focus within a container element (WCAG 2.4.3).
 *
 * When enabled the hook:
 *   - Queries all focusable elements inside the container
 *   - Wraps Tab / Shift+Tab focus within those elements
 *   - Calls onEscape when the Escape key is pressed
 *   - Saves and restores the previously focused element on mount/unmount
 */

import { useEffect, useRef, type RefObject } from 'react';

// ============================================================
// TYPES
// ============================================================

export interface FocusTrapOptions {
  /** Whether the focus trap is currently active */
  enabled: boolean;
  /** Optional callback invoked when Escape is pressed */
  onEscape?: () => void;
}

// ============================================================
// FOCUSABLE ELEMENT SELECTOR
// ============================================================

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(', ');

// ============================================================
// HOOK
// ============================================================

/**
 * Traps keyboard focus inside the referenced container while enabled.
 *
 * @param containerRef - React ref pointing to the trap container element
 * @param options      - { enabled, onEscape }
 */
export function useFocusTrap(
  containerRef: RefObject<HTMLElement | null>,
  options: FocusTrapOptions,
): void {
  const { enabled, onEscape } = options;

  // Keep a stable reference to the element that was focused before the trap activated.
  const previouslyFocusedRef = useRef<Element | null>(null);

  // Use ref for onEscape to avoid re-running effect on every render
  const onEscapeRef = useRef(onEscape);
  onEscapeRef.current = onEscape;

  // Track if we've already focused initially
  const hasInitialFocusRef = useRef(false);

  useEffect(() => {
    if (!enabled) {
      hasInitialFocusRef.current = false;
      return;
    }

    const container = containerRef.current;
    if (!container) return;

    // --- Save the currently focused element so we can restore it later ---
    if (!hasInitialFocusRef.current) {
      previouslyFocusedRef.current = document.activeElement;
    }

    // --- Focus the first focusable element inside the container (only once) ---
    const focusFirst = () => {
      if (hasInitialFocusRef.current) return;
      hasInitialFocusRef.current = true;

      const focusable = container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (focusable.length > 0) {
        focusable[0].focus();
      }
    };

    // Small delay to ensure the DOM is fully rendered before focusing
    const initialFocusTimer = requestAnimationFrame(focusFirst);

    // --- Keyboard handler ---
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        if (onEscapeRef.current) {
          onEscapeRef.current();
        }
        return;
      }

      if (event.key !== 'Tab') return;

      const focusableElements = container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR);
      if (focusableElements.length === 0) {
        event.preventDefault();
        return;
      }

      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (event.shiftKey) {
        // Shift+Tab: wrap from first to last
        if (document.activeElement === firstElement) {
          event.preventDefault();
          lastElement.focus();
        }
      } else {
        // Tab: wrap from last to first
        if (document.activeElement === lastElement) {
          event.preventDefault();
          firstElement.focus();
        }
      }
    };

    container.addEventListener('keydown', handleKeyDown);

    // --- Cleanup ---
    return () => {
      cancelAnimationFrame(initialFocusTimer);
      container.removeEventListener('keydown', handleKeyDown);

      // Restore focus to the element that was active before the trap
      const toRestore = previouslyFocusedRef.current;
      if (toRestore && toRestore instanceof HTMLElement) {
        toRestore.focus();
      }
    };
  }, [enabled, containerRef]);
}
