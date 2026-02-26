/**
 * AZALSCORE - Module Paramètres
 * Configuration et préférences utilisateur avec persistance API
 */

import React, { useState, useEffect } from 'react';
import { Palette, Globe, Bell, Settings, Save, RotateCcw, Trash2, Check, Loader2, Upload, X, Image } from 'lucide-react';
import { api } from '@/core/api-client';
import { MainLayout } from '@/ui-engine/layouts/MainLayout';

// Types
type AccentColor = 'orange' | 'blue' | 'violet' | 'emerald' | 'rose';
type LogoIcon = 'text' | 'letter-a' | 'cube' | 'spark' | 'shield' | 'hexagon';

interface UserPreferences {
  theme_mode: 'LIGHT' | 'DARK' | 'SYSTEM';
  ui_style: 'CLASSIC' | 'MODERN' | 'GLASS';
  accent_color: AccentColor;
  logo_icon: LogoIcon;
  custom_logo: string | null; // Base64 ou URL du logo personnalisé
  language: string;
  toolbar_dense: boolean;
  desktop_notifications: boolean;
  sound_enabled: boolean;
}

const DEFAULT_PREFERENCES: UserPreferences = {
  theme_mode: 'SYSTEM',
  ui_style: 'CLASSIC',
  accent_color: 'orange',
  logo_icon: 'text',
  custom_logo: null,
  language: 'fr',
  toolbar_dense: false,
  desktop_notifications: false,
  sound_enabled: true,
};

// Icônes du logo
const LOGO_ICONS: Record<LogoIcon, { name: string; icon: React.ReactNode }> = {
  'text': {
    name: 'Texte',
    icon: <span style={{ fontWeight: 800, fontSize: '16px' }}>AZ</span>
  },
  'letter-a': {
    name: 'Lettre A',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2L2 22h20L12 2z" fill="none"/>
        <path d="M7 16h10"/>
      </svg>
    )
  },
  'cube': {
    name: 'Cube',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
        <line x1="12" y1="22.08" x2="12" y2="12"/>
      </svg>
    )
  },
  'spark': {
    name: 'Étincelle',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
      </svg>
    )
  },
  'shield': {
    name: 'Bouclier',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        <path d="m9 12 2 2 4-4"/>
      </svg>
    )
  },
  'hexagon': {
    name: 'Hexagone',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
      </svg>
    )
  }
};

// Palettes de couleurs
const COLOR_PALETTES: Record<AccentColor, {
  name: string;
  primary: string;
  gradient: string;
  light: string;
  50: string;
  100: string;
  200: string;
  300: string;
  400: string;
  500: string;
  600: string;
  700: string;
  800: string;
  900: string;
}> = {
  orange: {
    name: 'Orange',
    primary: '#f97316',
    gradient: 'linear-gradient(135deg, #ea580c 0%, #f97316 50%, #fbbf24 100%)',
    light: '#fff7ed',
    50: '#fff7ed', 100: '#ffedd5', 200: '#fed7aa', 300: '#fdba74',
    400: '#fb923c', 500: '#f97316', 600: '#ea580c', 700: '#c2410c',
    800: '#9a3412', 900: '#7c2d12',
  },
  blue: {
    name: 'Bleu',
    primary: '#3b82f6',
    gradient: 'linear-gradient(135deg, #1d4ed8 0%, #3b82f6 50%, #60a5fa 100%)',
    light: '#eff6ff',
    50: '#eff6ff', 100: '#dbeafe', 200: '#bfdbfe', 300: '#93c5fd',
    400: '#60a5fa', 500: '#3b82f6', 600: '#2563eb', 700: '#1d4ed8',
    800: '#1e40af', 900: '#1e3a8a',
  },
  violet: {
    name: 'Violet',
    primary: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #7c3aed 0%, #8b5cf6 50%, #a78bfa 100%)',
    light: '#f5f3ff',
    50: '#f5f3ff', 100: '#ede9fe', 200: '#ddd6fe', 300: '#c4b5fd',
    400: '#a78bfa', 500: '#8b5cf6', 600: '#7c3aed', 700: '#6d28d9',
    800: '#5b21b6', 900: '#4c1d95',
  },
  emerald: {
    name: 'Vert',
    primary: '#10b981',
    gradient: 'linear-gradient(135deg, #059669 0%, #10b981 50%, #34d399 100%)',
    light: '#ecfdf5',
    50: '#ecfdf5', 100: '#d1fae5', 200: '#a7f3d0', 300: '#6ee7b7',
    400: '#34d399', 500: '#10b981', 600: '#059669', 700: '#047857',
    800: '#065f46', 900: '#064e3b',
  },
  rose: {
    name: 'Rose',
    primary: '#f43f5e',
    gradient: 'linear-gradient(135deg, #e11d48 0%, #f43f5e 50%, #fb7185 100%)',
    light: '#fff1f2',
    50: '#fff1f2', 100: '#ffe4e6', 200: '#fecdd3', 300: '#fda4af',
    400: '#fb7185', 500: '#f43f5e', 600: '#e11d48', 700: '#be123c',
    800: '#9f1239', 900: '#881337',
  },
};

// Applique les styles globalement
const applyPreferences = (prefs: UserPreferences) => {
  const root = document.documentElement;

  // Theme mode
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
  const isDark = prefs.theme_mode === 'DARK' || (prefs.theme_mode === 'SYSTEM' && prefersDark);
  root.setAttribute('data-theme', isDark ? 'dark' : 'light');

  // UI Style
  root.setAttribute('data-ui-style', prefs.ui_style.toLowerCase());

  // Accent color - Apply CSS variables
  const palette = COLOR_PALETTES[prefs.accent_color] || COLOR_PALETTES.orange;
  root.style.setProperty('--azals-brand-50', palette[50]);
  root.style.setProperty('--azals-brand-100', palette[100]);
  root.style.setProperty('--azals-brand-200', palette[200]);
  root.style.setProperty('--azals-brand-300', palette[300]);
  root.style.setProperty('--azals-brand-400', palette[400]);
  root.style.setProperty('--azals-brand-500', palette[500]);
  root.style.setProperty('--azals-brand-600', palette[600]);
  root.style.setProperty('--azals-brand-700', palette[700]);
  root.style.setProperty('--azals-brand-800', palette[800]);
  root.style.setProperty('--azals-brand-900', palette[900]);
  root.style.setProperty('--azals-gradient-brand', palette.gradient);
  root.style.setProperty('--azals-gradient-hero', palette.gradient);
  root.setAttribute('data-accent', prefs.accent_color);

  // Logo icon
  root.setAttribute('data-logo-icon', prefs.logo_icon || 'text');

  // Custom logo
  if (prefs.custom_logo) {
    root.setAttribute('data-custom-logo', prefs.custom_logo);
  } else {
    root.removeAttribute('data-custom-logo');
  }

  // Compact view
  if (prefs.toolbar_dense) {
    root.classList.add('azals-compact');
  } else {
    root.classList.remove('azals-compact');
  }

  // Persist to localStorage for initial load
  localStorage.setItem('azals_preferences', JSON.stringify(prefs));
};

// Load preferences from localStorage (for initial render before API)
const loadLocalPreferences = (): UserPreferences => {
  try {
    const stored = localStorage.getItem('azals_preferences');
    if (stored) {
      return { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) };
    }
  } catch {
    // ignore
  }
  return DEFAULT_PREFERENCES;
};

export default function SettingsModule() {
  const [settings, setSettings] = useState<UserPreferences>(loadLocalPreferences);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load preferences from API
  useEffect(() => {
    const loadPreferences = async () => {
      try {
        const response = await api.get<UserPreferences>('/web/preferences');
        if (response.data) {
          const prefs = {
            theme_mode: response.data.theme_mode || 'SYSTEM',
            ui_style: response.data.ui_style || 'CLASSIC',
            accent_color: (response.data.accent_color as AccentColor) || 'orange',
            logo_icon: (response.data.logo_icon as LogoIcon) || 'text',
            custom_logo: response.data.custom_logo || null,
            language: response.data.language || 'fr',
            toolbar_dense: response.data.toolbar_dense || false,
            desktop_notifications: response.data.desktop_notifications || false,
            sound_enabled: response.data.sound_enabled ?? true,
          };
          setSettings(prefs);
          applyPreferences(prefs);
        }
      } catch (err) {
        console.warn('Could not load preferences from API, using local storage');
      } finally {
        setLoading(false);
      }
    };
    loadPreferences();
  }, []);

  // Apply preferences when they change
  useEffect(() => {
    applyPreferences(settings);
  }, [settings]);

  const handleToggle = (key: keyof UserPreferences) => {
    setSettings(prev => ({
      ...prev,
      [key]: !prev[key],
    }));
    setSaved(false);
  };

  const handleSelect = (key: keyof UserPreferences, value: string) => {
    setSettings(prev => ({
      ...prev,
      [key]: value,
    }));
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.put('/web/preferences', settings);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError('Erreur lors de la sauvegarde des paramètres');
      console.error('Failed to save preferences:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setSettings(DEFAULT_PREFERENCES);
    applyPreferences(DEFAULT_PREFERENCES);
    setSaved(false);
  };

  const UI_STYLES = [
    { value: 'CLASSIC', label: 'Classique', desc: 'Interface traditionnelle et épurée' },
    { value: 'MODERN', label: 'Moderne', desc: 'Ombres douces et animations fluides' },
    { value: 'GLASS', label: 'Glass', desc: 'Effet verre dépoli et transparence' },
  ];

  const THEMES = [
    { value: 'LIGHT', label: 'Clair' },
    { value: 'DARK', label: 'Sombre' },
    { value: 'SYSTEM', label: 'Automatique' },
  ];

  return (
    <MainLayout title="Paramètres">
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Apparence */}
        <div className="azals-card" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <h2 className="azals-card__title" style={{ marginBottom: 'var(--azals-spacing-lg)', display: 'flex', alignItems: 'center', gap: 'var(--azals-spacing-sm)' }}>
              <Palette size={20} /> Apparence
            </h2>

            {/* Thème */}
            <div className="azals-form-field" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              <label htmlFor="settings-theme">Thème</label>
              <select
                id="settings-theme"
                className="azals-select"
                value={settings.theme_mode}
                onChange={(e) => handleSelect('theme_mode', e.target.value)}
              >
                {THEMES.map(t => (
                  <option key={t.value} value={t.value}>{t.label}</option>
                ))}
              </select>
            </div>

            {/* Style visuel */}
            <div className="azals-form-field" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              <span className="azals-form-label">Style visuel</span>
              <div style={{ display: 'grid', gap: 'var(--azals-spacing-sm)', marginTop: 'var(--azals-spacing-sm)' }}>
                {UI_STYLES.map(style => (
                  <label
                    key={style.value}
                    className={`azals-style-option ${settings.ui_style === style.value ? 'azals-style-option--active' : ''}`}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 'var(--azals-spacing-md)',
                      padding: 'var(--azals-spacing-md)',
                      border: `2px solid ${settings.ui_style === style.value ? 'var(--azals-primary)' : 'var(--azals-border)'}`,
                      borderRadius: 'var(--azals-radius-lg)',
                      cursor: 'pointer',
                      background: settings.ui_style === style.value ? 'var(--azals-primary-50)' : 'transparent',
                      transition: 'all 0.2s ease',
                    }}
                  >
                    <input
                      type="radio"
                      name="ui_style"
                      value={style.value}
                      checked={settings.ui_style === style.value}
                      onChange={(e) => handleSelect('ui_style', e.target.value)}
                      style={{ display: 'none' }}
                    />
                    <div style={{
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      border: `2px solid ${settings.ui_style === style.value ? 'var(--azals-primary)' : 'var(--azals-gray-400)'}`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: settings.ui_style === style.value ? 'var(--azals-primary)' : 'transparent',
                      flexShrink: 0,
                    }}>
                      {settings.ui_style === style.value && <Check size={12} color="white" />}
                    </div>
                    <div>
                      <div style={{ fontWeight: 500 }}>{style.label}</div>
                      <div style={{ fontSize: 'var(--azals-font-size-sm)', color: 'var(--azals-text-secondary)' }}>
                        {style.desc}
                      </div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* Couleur d'accent */}
            <div className="azals-form-field" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              <span className="azals-form-label">Couleur d'accent</span>
              <div style={{
                display: 'flex',
                gap: 'var(--azals-spacing-md)',
                marginTop: 'var(--azals-spacing-sm)',
                flexWrap: 'wrap'
              }}>
                {(Object.keys(COLOR_PALETTES) as AccentColor[]).map(colorKey => {
                  const color = COLOR_PALETTES[colorKey];
                  const isSelected = settings.accent_color === colorKey;
                  return (
                    <button
                      key={colorKey}
                      type="button"
                      onClick={() => handleSelect('accent_color', colorKey)}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '12px 16px',
                        border: isSelected ? `2px solid ${color.primary}` : '2px solid transparent',
                        borderRadius: '12px',
                        background: isSelected ? color.light : '#f9fafb',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        minWidth: '80px',
                      }}
                    >
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        background: color.gradient,
                        boxShadow: isSelected ? `0 4px 12px ${color.primary}40` : 'none',
                        transition: 'all 0.2s ease',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                      }}>
                        {isSelected && <Check size={20} color="white" />}
                      </div>
                      <span style={{
                        fontSize: '13px',
                        fontWeight: isSelected ? 600 : 500,
                        color: isSelected ? color[700] : '#6b7280'
                      }}>
                        {color.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Icône du logo */}
            <div className="azals-form-field" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              <span className="azals-form-label">Icône du logo</span>
              <div style={{
                display: 'flex',
                gap: 'var(--azals-spacing-md)',
                marginTop: 'var(--azals-spacing-sm)',
                flexWrap: 'wrap'
              }}>
                {(Object.keys(LOGO_ICONS) as LogoIcon[]).map(iconKey => {
                  const iconData = LOGO_ICONS[iconKey];
                  const isSelected = settings.logo_icon === iconKey;
                  const palette = COLOR_PALETTES[settings.accent_color];
                  return (
                    <button
                      key={iconKey}
                      type="button"
                      onClick={() => handleSelect('logo_icon', iconKey)}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '8px',
                        padding: '12px 14px',
                        border: isSelected ? `2px solid ${palette.primary}` : '2px solid #e5e7eb',
                        borderRadius: '12px',
                        background: isSelected ? palette.light : '#f9fafb',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        minWidth: '70px',
                      }}
                    >
                      <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '10px',
                        background: isSelected ? palette.gradient : '#e5e7eb',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: isSelected ? 'white' : '#6b7280',
                        transition: 'all 0.2s ease',
                      }}>
                        {iconData.icon}
                      </div>
                      <span style={{
                        fontSize: '12px',
                        fontWeight: isSelected ? 600 : 500,
                        color: isSelected ? palette[700] : '#6b7280'
                      }}>
                        {iconData.name}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Logo personnalisé */}
            <div className="azals-form-field" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              <span className="azals-form-label">Logo personnalisé</span>
              <p style={{ fontSize: '13px', color: '#6b7280', marginTop: '4px', marginBottom: '12px' }}>
                Téléchargez votre propre logo (PNG, JPG, SVG - max 2MB)
              </p>

              {settings.custom_logo ? (
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '16px',
                  padding: '16px',
                  background: '#f9fafb',
                  borderRadius: '12px',
                  border: '1px solid #e5e7eb'
                }}>
                  <img
                    src={settings.custom_logo}
                    alt="Logo personnalisé"
                    style={{
                      height: '48px',
                      width: 'auto',
                      maxWidth: '200px',
                      objectFit: 'contain',
                      borderRadius: '8px',
                      background: 'white',
                      padding: '4px'
                    }}
                  />
                  <div style={{ flex: 1 }}>
                    <p style={{ fontWeight: 500, color: '#374151', marginBottom: '4px' }}>Logo actuel</p>
                    <p style={{ fontSize: '12px', color: '#9ca3af' }}>Cliquez sur le bouton pour changer</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      setSettings(prev => ({ ...prev, custom_logo: null }));
                      setSaved(false);
                    }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '36px',
                      height: '36px',
                      borderRadius: '8px',
                      border: 'none',
                      background: '#fee2e2',
                      color: '#dc2626',
                      cursor: 'pointer',
                      transition: 'all 0.2s'
                    }}
                    title="Supprimer le logo"
                  >
                    <X size={18} />
                  </button>
                </div>
              ) : (
                <label style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  padding: '32px 24px',
                  border: '2px dashed #d1d5db',
                  borderRadius: '12px',
                  background: '#f9fafb',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}>
                  <input
                    type="file"
                    accept="image/png,image/jpeg,image/svg+xml,image/webp"
                    style={{ display: 'none' }}
                    onChange={(e) => {
                      const file = e.target.files?.[0];
                      if (file) {
                        if (file.size > 2 * 1024 * 1024) {
                          setError('Le fichier est trop volumineux (max 2MB)');
                          return;
                        }
                        const reader = new FileReader();
                        reader.onload = (event) => {
                          const base64 = event.target?.result as string;
                          setSettings(prev => ({ ...prev, custom_logo: base64 }));
                          setSaved(false);
                        };
                        reader.readAsDataURL(file);
                      }
                    }}
                  />
                  <div style={{
                    width: '56px',
                    height: '56px',
                    borderRadius: '12px',
                    background: 'linear-gradient(135deg, #e5e7eb 0%, #d1d5db 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: '12px',
                    color: '#6b7280'
                  }}>
                    <Image size={28} />
                  </div>
                  <span style={{ fontWeight: 600, color: '#374151', marginBottom: '4px' }}>
                    Cliquez pour télécharger
                  </span>
                  <span style={{ fontSize: '12px', color: '#9ca3af' }}>
                    ou glissez-déposez votre fichier
                  </span>
                </label>
              )}
            </div>

            {/* Vue compacte */}
            <div>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: 'var(--azals-spacing-sm)' }}>
                <input
                  type="checkbox"
                  className="azals-checkbox"
                  checked={settings.toolbar_dense}
                  onChange={() => handleToggle('toolbar_dense')}
                />
                <span>Vue compacte</span>
              </label>
            </div>
          </div>
        </div>

        {/* Langue et Région */}
        <div className="azals-card" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <h2 className="azals-card__title" style={{ marginBottom: 'var(--azals-spacing-lg)', display: 'flex', alignItems: 'center', gap: 'var(--azals-spacing-sm)' }}>
              <Globe size={20} /> Langue et Région
            </h2>

            <div className="azals-form-field">
              <label htmlFor="settings-language">Langue</label>
              <select
                id="settings-language"
                className="azals-select"
                value={settings.language}
                onChange={(e) => handleSelect('language', e.target.value)}
              >
                <option value="fr">Français</option>
                <option value="en">English</option>
                <option value="es">Español</option>
              </select>
            </div>
          </div>
        </div>

        {/* Notifications */}
        <div className="azals-card" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <h2 className="azals-card__title" style={{ marginBottom: 'var(--azals-spacing-lg)', display: 'flex', alignItems: 'center', gap: 'var(--azals-spacing-sm)' }}>
              <Bell size={20} /> Notifications
            </h2>

            <div style={{ display: 'grid', gap: 'var(--azals-spacing-md)' }}>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: 'var(--azals-spacing-sm)' }}>
                <input
                  type="checkbox"
                  className="azals-checkbox"
                  checked={settings.desktop_notifications}
                  onChange={() => handleToggle('desktop_notifications')}
                />
                <div>
                  <div className="font-medium">Notifications push</div>
                  <div className="text-muted" style={{ fontSize: 'var(--azals-font-size-sm)' }}>
                    Recevoir des notifications dans le navigateur
                  </div>
                </div>
              </label>

              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: 'var(--azals-spacing-sm)' }}>
                <input
                  type="checkbox"
                  className="azals-checkbox"
                  checked={settings.sound_enabled}
                  onChange={() => handleToggle('sound_enabled')}
                />
                <div>
                  <div className="font-medium">Sons</div>
                  <div className="text-muted" style={{ fontSize: 'var(--azals-font-size-sm)' }}>
                    Jouer des sons pour les notifications
                  </div>
                </div>
              </label>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="azals-card" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <h2 className="azals-card__title" style={{ marginBottom: 'var(--azals-spacing-lg)', display: 'flex', alignItems: 'center', gap: 'var(--azals-spacing-sm)' }}>
              <Settings size={20} /> Actions
            </h2>

            {error && (
              <div style={{
                padding: 'var(--azals-spacing-md)',
                background: 'var(--azals-red-light)',
                color: 'var(--azals-danger)',
                borderRadius: 'var(--azals-radius-md)',
                marginBottom: 'var(--azals-spacing-md)'
              }}>
                {error}
              </div>
            )}

            <div style={{ display: 'grid', gap: 'var(--azals-spacing-md)' }}>
              <button
                className={`azals-btn ${saved ? 'azals-btn--success' : 'azals-btn--primary'}`}
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? (
                  <><Loader2 size={16} className="animate-spin" /> Enregistrement...</>
                ) : saved ? (
                  <><Check size={16} /> Paramètres enregistrés</>
                ) : (
                  <><Save size={16} /> Enregistrer les paramètres</>
                )}
              </button>

              <button className="azals-btn azals-btn--ghost" onClick={handleReset}>
                <RotateCcw size={16} /> Réinitialiser aux valeurs par défaut
              </button>

              <button
                className="azals-btn azals-btn--danger"
                onClick={() => {
                  if (confirm('Êtes-vous sûr de vouloir supprimer votre compte ? Cette action est irréversible.')) {
                    window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'deleteAccount' } }));
                  }
                }}
              >
                <Trash2 size={16} /> Supprimer le compte
              </button>
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <div className="text-muted text-center" style={{ fontSize: 'var(--azals-font-size-sm)', padding: 'var(--azals-spacing-md)' }}>
          <p>Version AZALSCORE 1.0.0</p>
          <p>Dernière mise à jour: 2026-01-23</p>
        </div>
      </div>
    </MainLayout>
  );
}
