/**
 * AZALSCORE - Récents & Favoris
 * Gestion des éléments récemment consultés et des favoris
 */

export interface RecentItem {
  id: string;
  type: 'client' | 'document' | 'article';
  title: string;
  subtitle?: string;
  timestamp: number;
}

export interface FavoriteItem {
  id: string;
  type: 'client' | 'document' | 'article';
  title: string;
  subtitle?: string;
}

const RECENTS_KEY = 'azalscore_recents';
const FAVORITES_KEY = 'azalscore_favorites';
const MAX_RECENTS = 10;

// ============================================================
// RECENTS
// ============================================================

export const getRecents = (): RecentItem[] => {
  try {
    const stored = localStorage.getItem(RECENTS_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

export const addRecent = (item: Omit<RecentItem, 'timestamp'>): void => {
  const recents = getRecents();

  // Remove if already exists
  const filtered = recents.filter(r => !(r.id === item.id && r.type === item.type));

  // Add to beginning with timestamp
  const newRecents = [
    { ...item, timestamp: Date.now() },
    ...filtered
  ].slice(0, MAX_RECENTS);

  localStorage.setItem(RECENTS_KEY, JSON.stringify(newRecents));
};

export const clearRecents = (): void => {
  localStorage.removeItem(RECENTS_KEY);
};

// ============================================================
// FAVORITES
// ============================================================

export const getFavorites = (): FavoriteItem[] => {
  try {
    const stored = localStorage.getItem(FAVORITES_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch {
    return [];
  }
};

export const addFavorite = (item: FavoriteItem): void => {
  const favorites = getFavorites();

  // Check if already exists
  if (favorites.some(f => f.id === item.id && f.type === item.type)) {
    return;
  }

  favorites.unshift(item);
  localStorage.setItem(FAVORITES_KEY, JSON.stringify(favorites));
};

export const removeFavorite = (id: string, type: string): void => {
  const favorites = getFavorites();
  const filtered = favorites.filter(f => !(f.id === id && f.type === type));
  localStorage.setItem(FAVORITES_KEY, JSON.stringify(filtered));
};

export const isFavorite = (id: string, type: string): boolean => {
  const favorites = getFavorites();
  return favorites.some(f => f.id === id && f.type === type);
};

export const toggleFavorite = (item: FavoriteItem): boolean => {
  if (isFavorite(item.id, item.type)) {
    removeFavorite(item.id, item.type);
    return false;
  } else {
    addFavorite(item);
    return true;
  }
};
