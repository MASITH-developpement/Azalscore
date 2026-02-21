/**
 * AZALSCORE - Module Paramètres
 * Configuration et préférences utilisateur avec persistance API
 */

import React, { useState, useEffect } from 'react';
import { Palette, Globe, Bell, Settings, Save, RotateCcw, Trash2, Check, Loader2 } from 'lucide-react';
import { api } from '@/core/api-client';
import { MainLayout } from '@/ui-engine/layouts/MainLayout';

// Types
interface UserPreferences {
  theme_mode: 'LIGHT' | 'DARK' | 'SYSTEM';
  ui_style: 'CLASSIC' | 'MODERN' | 'GLASS';
  language: string;
  toolbar_dense: boolean;
  desktop_notifications: boolean;
  sound_enabled: boolean;
}

const DEFAULT_PREFERENCES: UserPreferences = {
  theme_mode: 'SYSTEM',
  ui_style: 'CLASSIC',
  language: 'fr',
  toolbar_dense: false,
  desktop_notifications: false,
  sound_enabled: true,
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
