/**
 * AZALSCORE UI Engine - Hooks Re-exports
 * Point d'entrée pour tous les hooks UI
 */

export {
  useUIMode,
  initUIMode,
  getCurrentUIMode,
  setUIMode,
  type UIMode,
} from './useUIMode';

export { useFocusTrap, type FocusTrapOptions } from './useFocusTrap';

export { useQueryState, type QueryState, type UseQueryStateOptions, type UseQueryStateResult } from './useQueryState';

export { useAuthenticatedQuery, type AuthenticatedQueryOptions } from './useAuthenticatedQuery';
