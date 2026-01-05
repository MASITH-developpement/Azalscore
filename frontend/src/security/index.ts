/**
 * AZALSCORE UI Engine - Security Module
 * Sécurité côté client - validation et protection UI
 * La sécurité réelle est côté backend
 */

// ============================================================
// SANITIZATION
// ============================================================

/**
 * Échappe les caractères HTML dangereux
 */
export const escapeHtml = (str: string): string => {
  const htmlEscapes: Record<string, string> = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#x27;',
    '/': '&#x2F;',
  };
  return str.replace(/[&<>"'/]/g, (char) => htmlEscapes[char]);
};

/**
 * Supprime les balises HTML d'une chaîne
 */
export const stripHtml = (str: string): string => {
  return str.replace(/<[^>]*>/g, '');
};

/**
 * Valide et nettoie une URL
 */
export const sanitizeUrl = (url: string): string | null => {
  try {
    const parsed = new URL(url);
    // Autoriser uniquement http et https
    if (!['http:', 'https:'].includes(parsed.protocol)) {
      return null;
    }
    return parsed.toString();
  } catch {
    return null;
  }
};

// ============================================================
// VALIDATION
// ============================================================

/**
 * Valide un email
 */
export const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

/**
 * Valide un mot de passe (règles minimales)
 */
export const isValidPassword = (password: string): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push('Le mot de passe doit contenir au moins 8 caractères');
  }
  if (!/[A-Z]/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins une majuscule');
  }
  if (!/[a-z]/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins une minuscule');
  }
  if (!/[0-9]/.test(password)) {
    errors.push('Le mot de passe doit contenir au moins un chiffre');
  }

  return { valid: errors.length === 0, errors };
};

/**
 * Valide un numéro de téléphone français
 */
export const isValidPhoneNumber = (phone: string): boolean => {
  const phoneRegex = /^(?:(?:\+|00)33|0)\s*[1-9](?:[\s.-]*\d{2}){4}$/;
  return phoneRegex.test(phone);
};

/**
 * Valide un IBAN
 */
export const isValidIBAN = (iban: string): boolean => {
  const ibanRegex = /^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$/;
  return ibanRegex.test(iban.replace(/\s/g, '').toUpperCase());
};

/**
 * Valide un numéro de TVA intracommunautaire
 */
export const isValidVATNumber = (vat: string): boolean => {
  const vatRegex = /^[A-Z]{2}[A-Z0-9]{2,12}$/;
  return vatRegex.test(vat.replace(/\s/g, '').toUpperCase());
};

// ============================================================
// PROTECTION CSRF
// ============================================================

let csrfToken: string | null = null;

export const setCsrfToken = (token: string): void => {
  csrfToken = token;
};

export const getCsrfToken = (): string | null => {
  return csrfToken;
};

// ============================================================
// RATE LIMITING (CLIENT-SIDE)
// ============================================================

interface RateLimitEntry {
  count: number;
  resetTime: number;
}

const rateLimitStore: Map<string, RateLimitEntry> = new Map();

export const checkRateLimit = (key: string, maxRequests: number, windowMs: number): boolean => {
  const now = Date.now();
  const entry = rateLimitStore.get(key);

  if (!entry || now > entry.resetTime) {
    rateLimitStore.set(key, { count: 1, resetTime: now + windowMs });
    return true;
  }

  if (entry.count >= maxRequests) {
    return false;
  }

  entry.count++;
  return true;
};

// ============================================================
// SESSION SECURITY
// ============================================================

/**
 * Vérifie si la session est valide
 */
export const isSessionValid = (): boolean => {
  const token = sessionStorage.getItem('azals_access_token');
  if (!token) return false;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000;
    return Date.now() < exp;
  } catch {
    return false;
  }
};

/**
 * Obtient le temps restant de la session en secondes
 */
export const getSessionTimeRemaining = (): number => {
  const token = sessionStorage.getItem('azals_access_token');
  if (!token) return 0;

  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000;
    return Math.max(0, Math.floor((exp - Date.now()) / 1000));
  } catch {
    return 0;
  }
};

// ============================================================
// CONTENT SECURITY
// ============================================================

/**
 * Vérifie si une chaîne contient des patterns XSS potentiels
 */
export const containsXSSPatterns = (str: string): boolean => {
  const xssPatterns = [
    /<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi,
    /javascript:/gi,
    /on\w+\s*=/gi,
    /data:\s*text\/html/gi,
  ];

  return xssPatterns.some((pattern) => pattern.test(str));
};

/**
 * Vérifie si une chaîne contient des patterns d'injection SQL potentiels
 */
export const containsSQLIPatterns = (str: string): boolean => {
  const sqlPatterns = [
    /(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)/gi,
    /(--)|(\/\*)/g,
    /(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+/gi,
  ];

  return sqlPatterns.some((pattern) => pattern.test(str));
};

// ============================================================
// SECURE STORAGE
// ============================================================

/**
 * Stockage sécurisé en mémoire (pas de persistance)
 */
class SecureMemoryStore {
  private store: Map<string, unknown> = new Map();

  set<T>(key: string, value: T): void {
    this.store.set(key, value);
  }

  get<T>(key: string): T | undefined {
    return this.store.get(key) as T | undefined;
  }

  delete(key: string): void {
    this.store.delete(key);
  }

  clear(): void {
    this.store.clear();
  }
}

export const secureStore = new SecureMemoryStore();

// ============================================================
// EXPORTS
// ============================================================

export default {
  escapeHtml,
  stripHtml,
  sanitizeUrl,
  isValidEmail,
  isValidPassword,
  isValidPhoneNumber,
  isValidIBAN,
  isValidVATNumber,
  setCsrfToken,
  getCsrfToken,
  checkRateLimit,
  isSessionValid,
  getSessionTimeRemaining,
  containsXSSPatterns,
  containsSQLIPatterns,
  secureStore,
};
