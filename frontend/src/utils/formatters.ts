/**
 * AZALSCORE - Fonctions de formatage centralisees
 * Source unique pour tous les modules.
 * Remplace les fonctions formatDate/formatCurrency/formatDateTime
 * precedemment dupliquees dans chaque module/types.ts.
 */

// ============================================================
// DATE / HEURE
// ============================================================

/**
 * Formate une date au format fr-FR (ex: 27/01/2026)
 */
export const formatDate = (date?: string | null): string => {
  if (!date) return '-';
  return new Date(date).toLocaleDateString('fr-FR');
};

/**
 * Formate une date + heure au format fr-FR (ex: 27/01/2026 14:30)
 */
export const formatDateTime = (date?: string | null): string => {
  if (!date) return '-';
  return new Date(date).toLocaleString('fr-FR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};

/**
 * Formate une heure au format fr-FR (ex: 14:30)
 */
export const formatTime = (date?: string | null): string => {
  if (!date) return '-';
  return new Date(date).toLocaleTimeString('fr-FR', {
    hour: '2-digit',
    minute: '2-digit',
  });
};

// ============================================================
// MONNAIE / NOMBRES
// ============================================================

/**
 * Formate un montant en devise (ex: 1 234,56 EUR)
 */
export const formatCurrency = (amount?: number | null, currency = 'EUR'): string => {
  if (amount === undefined || amount === null) return '-';
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

/**
 * Formate un pourcentage (ex: 85.3%)
 */
export const formatPercent = (value?: number | null, decimals = 1): string => {
  if (value === undefined || value === null) return '-';
  return `${value.toFixed(decimals)}%`;
};

/**
 * Formate des heures (ex: 7.5h)
 */
export const formatHours = (hours?: number | null): string => {
  if (hours === undefined || hours === null) return '-';
  return `${hours.toFixed(1)}h`;
};

/**
 * Formate une duree en heures vers un affichage lisible
 * (ex: 45 min, 2.5 h, 3 j 2.0 h)
 */
export const formatDuration = (hours?: number): string => {
  if (!hours) return '-';
  if (hours < 1) return `${Math.round(hours * 60)} min`;
  if (hours < 24) return `${hours.toFixed(1)} h`;
  const days = Math.floor(hours / 8);
  const remainingHours = hours % 8;
  return remainingHours > 0 ? `${days} j ${remainingHours.toFixed(1)} h` : `${days} j`;
};

// ============================================================
// TEXTE / IDENTIFIANTS
// ============================================================

/**
 * Formate un IBAN avec espaces tous les 4 caracteres
 */
export const formatIBAN = (iban?: string | null): string => {
  if (!iban) return '-';
  return iban.replace(/(.{4})/g, '$1 ').trim();
};

/**
 * Masque un IBAN (affiche debut et fin uniquement)
 */
export const maskIBAN = (iban?: string | null): string => {
  if (!iban) return '-';
  if (iban.length <= 8) return iban;
  return `${iban.slice(0, 4)} **** **** ${iban.slice(-4)}`;
};

/**
 * Formate une taille de fichier en octets vers un format lisible
 * (ex: 1.5 Ko, 2.3 Mo, 1.0 Go)
 */
export const formatFileSize = (bytes?: number | null): string => {
  if (bytes === undefined || bytes === null || bytes === 0) return '0 o';

  const units = ['o', 'Ko', 'Mo', 'Go', 'To'];
  const k = 1024;
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${units[i]}`;
};
