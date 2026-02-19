/**
 * AZALSCORE - Module Paramètres
 * Configuration et préférences de l'application
 */

import React, { useState } from 'react';
import { Palette, Globe, Bell, Settings, Save, RotateCcw, Trash2 } from 'lucide-react';
import { MainLayout } from '@/ui-engine/layouts/MainLayout';

export default function SettingsModule() {
  const [settings, setSettings] = useState({
    theme: 'light',
    language: 'fr',
    notifications: true,
    emailAlerts: true,
    compactView: false,
  });

  const handleToggle = (key: keyof typeof settings) => {
    setSettings({
      ...settings,
      [key]: !settings[key],
    });
  };

  const handleSelect = (key: keyof typeof settings, value: string) => {
    setSettings({
      ...settings,
      [key]: value,
    });
  };

  return (
    <MainLayout title="Paramètres">
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Apparence */}
        <div className="azals-card" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <h2 className="azals-card__title" style={{ marginBottom: 'var(--azals-spacing-lg)', display: 'flex', alignItems: 'center', gap: 'var(--azals-spacing-sm)' }}>
              <Palette size={20} /> Apparence
            </h2>

            <div className="azals-form-field" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              <label>Thème</label>
              <select
                className="azals-select"
                value={settings.theme}
                onChange={(e) => handleSelect('theme', e.target.value)}
              >
                <option value="light">Clair</option>
                <option value="dark">Sombre</option>
                <option value="auto">Automatique</option>
              </select>
            </div>

            <div>
              <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', gap: 'var(--azals-spacing-sm)' }}>
                <input
                  type="checkbox"
                  className="azals-checkbox"
                  checked={settings.compactView}
                  onChange={() => handleToggle('compactView')}
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
              <label>Langue</label>
              <select
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
                  checked={settings.notifications}
                  onChange={() => handleToggle('notifications')}
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
                  checked={settings.emailAlerts}
                  onChange={() => handleToggle('emailAlerts')}
                />
                <div>
                  <div className="font-medium">Alertes email</div>
                  <div className="text-muted" style={{ fontSize: 'var(--azals-font-size-sm)' }}>
                    Recevoir des emails pour les événements importants
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

            <div style={{ display: 'grid', gap: 'var(--azals-spacing-md)' }}>
              <button className="azals-btn azals-btn--success" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'saveSettings' } })); }}>
                <Save size={16} /> Enregistrer les paramètres
              </button>

              <button className="azals-btn azals-btn--ghost" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'resetSettings' } })); }}>
                <RotateCcw size={16} /> Réinitialiser aux valeurs par défaut
              </button>

              <button className="azals-btn azals-btn--danger" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'deleteAccount' } })); }}>
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
