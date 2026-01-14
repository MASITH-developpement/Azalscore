/**
 * AZALSCORE - Composant Logo Officiel
 *
 * Logo AZALSCORE avec triangle gradient et cercles.
 * Conforme à la charte graphique enterprise.
 *
 * @usage
 * <AzalscoreLogo size="md" />
 * <AzalscoreLogo size={64} variant="icon" />
 */

import React from 'react';

// ============================================================
// TYPES
// ============================================================

type LogoSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' | number;
type LogoVariant = 'full' | 'icon' | 'horizontal';

interface AzalscoreLogoProps {
  /** Taille du logo: xs(16), sm(24), md(32), lg(48), xl(64), 2xl(96) ou nombre en pixels */
  size?: LogoSize;
  /** Variante d'affichage */
  variant?: LogoVariant;
  /** Classe CSS additionnelle */
  className?: string;
  /** Texte alternatif pour accessibilité */
  alt?: string;
  /** Mode sombre (inverse les couleurs des arcs) */
  darkMode?: boolean;
}

// ============================================================
// SIZE MAPPING
// ============================================================

const SIZE_MAP: Record<Exclude<LogoSize, number>, number> = {
  xs: 16,
  sm: 24,
  md: 32,
  lg: 48,
  xl: 64,
  '2xl': 96,
};

const getSize = (size: LogoSize): number => {
  if (typeof size === 'number') return size;
  return SIZE_MAP[size];
};

// ============================================================
// LOGO ICON (Triangle + Circles)
// ============================================================

const LogoIcon: React.FC<{ size: number; darkMode?: boolean }> = ({ size, darkMode = false }) => {
  const id = React.useId();
  const gradientId = `azals-gradient-${id}`;
  const arcColor = darkMode ? '#ffffff' : '#ffffff';
  const ringColor = darkMode ? 'rgba(255,255,255,0.3)' : 'rgba(107,114,128,0.3)';
  const dotColor = darkMode ? 'rgba(255,255,255,0.6)' : 'rgba(107,114,128,0.5)';

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-hidden="true"
    >
      <defs>
        {/* Gradient principal: cyan vers violet */}
        <linearGradient id={gradientId} x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor="#2DD4BF" />
          <stop offset="50%" stopColor="#3B82F6" />
          <stop offset="100%" stopColor="#8B5CF6" />
        </linearGradient>
      </defs>

      {/* Cercle extérieur partiel (ring) */}
      <circle
        cx="50"
        cy="50"
        r="44"
        stroke={ringColor}
        strokeWidth="1.5"
        fill="none"
        strokeDasharray="200 80"
        transform="rotate(-45 50 50)"
      />

      {/* Arc gauche (croissant) */}
      <path
        d="M 25 50 A 25 25 0 0 1 50 25 A 20 20 0 0 0 25 50"
        fill={arcColor}
        opacity="0.95"
      />

      {/* Arc droit (croissant) */}
      <path
        d="M 75 50 A 25 25 0 0 1 50 75 A 20 20 0 0 0 75 50"
        fill={arcColor}
        opacity="0.95"
      />

      {/* Triangle central avec gradient */}
      <path
        d="M 50 20 L 75 70 L 25 70 Z"
        fill={`url(#${gradientId})`}
      />

      {/* Points décoratifs */}
      <circle cx="15" cy="35" r="2" fill={dotColor} />
      <circle cx="85" cy="65" r="2" fill={dotColor} />
      <circle cx="20" cy="75" r="1.5" fill={dotColor} />
      <circle cx="80" cy="25" r="1.5" fill={dotColor} />
      <circle cx="50" cy="8" r="2" fill="#2DD4BF" opacity="0.8" />
      <circle cx="12" cy="55" r="1" fill="#2DD4BF" opacity="0.6" />
      <circle cx="88" cy="45" r="1" fill="#8B5CF6" opacity="0.6" />
    </svg>
  );
};

// ============================================================
// LOGO TEXT
// ============================================================

const LogoText: React.FC<{ size: number; darkMode?: boolean }> = ({ size, darkMode = false }) => {
  const fontSize = Math.max(size * 0.45, 12);
  const textColor = darkMode ? '#ffffff' : '#1e40af';

  return (
    <span
      style={{
        fontSize: `${fontSize}px`,
        fontWeight: 700,
        letterSpacing: '-0.02em',
        color: textColor,
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
      }}
    >
      AZALSCORE
    </span>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const AzalscoreLogo: React.FC<AzalscoreLogoProps> = ({
  size = 'md',
  variant = 'full',
  className = '',
  alt = 'AZALSCORE',
  darkMode = false,
}) => {
  const pixelSize = getSize(size);

  // Icon only
  if (variant === 'icon') {
    return (
      <span
        className={`azals-logo azals-logo--icon ${className}`}
        role="img"
        aria-label={alt}
        style={{ display: 'inline-flex', alignItems: 'center' }}
      >
        <LogoIcon size={pixelSize} darkMode={darkMode} />
      </span>
    );
  }

  // Horizontal layout (icon + text side by side)
  if (variant === 'horizontal') {
    return (
      <span
        className={`azals-logo azals-logo--horizontal ${className}`}
        role="img"
        aria-label={alt}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: `${pixelSize * 0.25}px`,
        }}
      >
        <LogoIcon size={pixelSize} darkMode={darkMode} />
        <LogoText size={pixelSize} darkMode={darkMode} />
      </span>
    );
  }

  // Full layout (icon + text vertical)
  return (
    <span
      className={`azals-logo azals-logo--full ${className}`}
      role="img"
      aria-label={alt}
      style={{
        display: 'inline-flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: `${pixelSize * 0.15}px`,
      }}
    >
      <LogoIcon size={pixelSize} darkMode={darkMode} />
      <LogoText size={pixelSize} darkMode={darkMode} />
    </span>
  );
};

// ============================================================
// EXPORTS
// ============================================================

export default AzalscoreLogo;
export type { AzalscoreLogoProps, LogoSize, LogoVariant };
