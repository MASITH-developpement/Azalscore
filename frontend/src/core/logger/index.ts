/**
 * AZALSCORE - Logger Sécurisé
 *
 * P0 SÉCURITÉ: Remplace console.log/warn/error pour éviter les fuites de données en production.
 *
 * Fonctionnalités:
 * - Désactivé en production (sauf erreurs critiques)
 * - Masque les données sensibles (tokens, passwords, emails)
 * - Format structuré pour debugging
 * - Support des groupes et timers
 *
 * Usage:
 * import { logger } from '@core/logger';
 * logger.info('Message', { data });
 * logger.warn('Warning', { context });
 * logger.error('Error', error);
 */

const IS_PRODUCTION = import.meta.env.PROD || import.meta.env.VITE_APP_ENV === 'production';
const IS_DEBUG = import.meta.env.VITE_DEBUG === 'true';

// Patterns de données sensibles à masquer
const SENSITIVE_PATTERNS = [
  /password/i,
  /token/i,
  /secret/i,
  /api_key/i,
  /apikey/i,
  /authorization/i,
  /credential/i,
  /bearer/i,
];

const SENSITIVE_VALUE_PATTERNS = [
  /^eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_]+\.[A-Za-z0-9-_]*$/, // JWT
  /^[A-Za-z0-9+/]{40,}={0,2}$/, // Base64 long strings
];

/**
 * Masque les valeurs sensibles dans un objet
 */
function sanitize(data: unknown, depth = 0): unknown {
  if (depth > 10) return '[MAX_DEPTH]';

  if (data === null || data === undefined) return data;

  if (typeof data === 'string') {
    // Masquer les tokens JWT et autres valeurs sensibles
    for (const pattern of SENSITIVE_VALUE_PATTERNS) {
      if (pattern.test(data)) {
        return '[REDACTED]';
      }
    }
    // Masquer les emails partiellement
    if (data.includes('@') && data.includes('.')) {
      const [local, domain] = data.split('@');
      if (local && domain) {
        return `${local[0]}***@${domain}`;
      }
    }
    return data;
  }

  if (typeof data !== 'object') return data;

  if (Array.isArray(data)) {
    return data.map(item => sanitize(item, depth + 1));
  }

  const sanitized: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
    // Masquer les clés sensibles
    const isSensitiveKey = SENSITIVE_PATTERNS.some(pattern => pattern.test(key));
    if (isSensitiveKey) {
      sanitized[key] = '[REDACTED]';
    } else {
      sanitized[key] = sanitize(value, depth + 1);
    }
  }
  return sanitized;
}

/**
 * Formate le timestamp
 */
function timestamp(): string {
  return new Date().toISOString();
}

/**
 * Formate le message avec contexte
 */
function formatMessage(level: string, message: string, ...args: unknown[]): string {
  const sanitizedArgs = args.map(arg => sanitize(arg));
  const argsStr = sanitizedArgs.length > 0
    ? ' ' + sanitizedArgs.map(a => JSON.stringify(a)).join(' ')
    : '';
  return `[${timestamp()}] [${level}] ${message}${argsStr}`;
}

type LogLevel = 'debug' | 'info' | 'warn' | 'error';

interface Logger {
  debug: (message: string, ...args: unknown[]) => void;
  info: (message: string, ...args: unknown[]) => void;
  warn: (message: string, ...args: unknown[]) => void;
  error: (message: string, ...args: unknown[]) => void;
  group: (label: string) => void;
  groupEnd: () => void;
  time: (label: string) => void;
  timeEnd: (label: string) => void;
}

/**
 * Logger de production - minimaliste, sécurisé
 */
const productionLogger: Logger = {
  debug: () => {}, // Désactivé en prod
  info: () => {},  // Désactivé en prod
  warn: (message: string, ...args: unknown[]) => {
    // Warnings autorisés en prod mais sanitisés
    if (IS_DEBUG) {
      console.warn(formatMessage('WARN', message, ...args));
    }
  },
  error: (message: string, ...args: unknown[]) => {
    // Erreurs toujours loggées mais sanitisées
    console.error(formatMessage('ERROR', message, ...sanitize(args) as unknown[]));
  },
  group: () => {},
  groupEnd: () => {},
  time: () => {},
  timeEnd: () => {},
};

/**
 * Logger de développement - complet
 */
const developmentLogger: Logger = {
  debug: (message: string, ...args: unknown[]) => {
    console.debug(formatMessage('DEBUG', message), ...args);
  },
  info: (message: string, ...args: unknown[]) => {
    console.info(formatMessage('INFO', message), ...args);
  },
  warn: (message: string, ...args: unknown[]) => {
    console.warn(formatMessage('WARN', message), ...args);
  },
  error: (message: string, ...args: unknown[]) => {
    console.error(formatMessage('ERROR', message), ...args);
  },
  group: (label: string) => console.group(label),
  groupEnd: () => console.groupEnd(),
  time: (label: string) => console.time(label),
  timeEnd: (label: string) => console.timeEnd(label),
};

/**
 * Logger exporté - choisit automatiquement le mode
 */
export const logger: Logger = IS_PRODUCTION ? productionLogger : developmentLogger;

/**
 * Crée un logger avec préfixe pour un module spécifique
 */
export function createLogger(moduleName: string): Logger {
  const prefix = `[${moduleName}]`;
  return {
    debug: (message: string, ...args: unknown[]) => logger.debug(`${prefix} ${message}`, ...args),
    info: (message: string, ...args: unknown[]) => logger.info(`${prefix} ${message}`, ...args),
    warn: (message: string, ...args: unknown[]) => logger.warn(`${prefix} ${message}`, ...args),
    error: (message: string, ...args: unknown[]) => logger.error(`${prefix} ${message}`, ...args),
    group: (label: string) => logger.group(`${prefix} ${label}`),
    groupEnd: () => logger.groupEnd(),
    time: (label: string) => logger.time(`${prefix} ${label}`),
    timeEnd: (label: string) => logger.timeEnd(`${prefix} ${label}`),
  };
}

export default logger;
