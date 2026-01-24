/**
 * AZALSCORE - Module Paramètres
 * Configuration et préférences de l'application
 */

import React, { useState } from 'react';
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
        <div
          style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginBottom: '1.5rem',
          }}
        >
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem' }}>
            🎨 Apparence
          </h2>

          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
              Thème
            </label>
            <select
              value={settings.theme}
              onChange={(e) => handleSelect('theme', e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '1rem',
              }}
            >
              <option value="light">Clair</option>
              <option value="dark">Sombre</option>
              <option value="auto">Automatique</option>
            </select>
          </div>

          <div>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={settings.compactView}
                onChange={() => handleToggle('compactView')}
                style={{ marginRight: '0.5rem', width: '1.25rem', height: '1.25rem' }}
              />
              <span>Vue compacte</span>
            </label>
          </div>
        </div>

        {/* Langue et Région */}
        <div
          style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginBottom: '1.5rem',
          }}
        >
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem' }}>
            🌍 Langue et Région
          </h2>

          <div>
            <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.5rem' }}>
              Langue
            </label>
            <select
              value={settings.language}
              onChange={(e) => handleSelect('language', e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                border: '1px solid #d1d5db',
                borderRadius: '0.375rem',
                fontSize: '1rem',
              }}
            >
              <option value="fr">Français</option>
              <option value="en">English</option>
              <option value="es">Español</option>
            </select>
          </div>
        </div>

        {/* Notifications */}
        <div
          style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginBottom: '1.5rem',
          }}
        >
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem' }}>
            🔔 Notifications
          </h2>

          <div style={{ display: 'grid', gap: '1rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={settings.notifications}
                onChange={() => handleToggle('notifications')}
                style={{ marginRight: '0.5rem', width: '1.25rem', height: '1.25rem' }}
              />
              <div>
                <div style={{ fontWeight: '500' }}>Notifications push</div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  Recevoir des notifications dans le navigateur
                </div>
              </div>
            </label>

            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={settings.emailAlerts}
                onChange={() => handleToggle('emailAlerts')}
                style={{ marginRight: '0.5rem', width: '1.25rem', height: '1.25rem' }}
              />
              <div>
                <div style={{ fontWeight: '500' }}>Alertes email</div>
                <div style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                  Recevoir des emails pour les événements importants
                </div>
              </div>
            </label>
          </div>
        </div>

        {/* Actions */}
        <div
          style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}
        >
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem' }}>
            ⚙️ Actions
          </h2>

          <div style={{ display: 'grid', gap: '1rem' }}>
            <button
              style={{
                padding: '0.75rem',
                backgroundColor: '#10b981',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: '500',
                cursor: 'pointer',
              }}
            >
              💾 Enregistrer les paramètres
            </button>

            <button
              style={{
                padding: '0.75rem',
                backgroundColor: '#6b7280',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: '500',
                cursor: 'pointer',
              }}
            >
              🔄 Réinitialiser aux valeurs par défaut
            </button>

            <button
              style={{
                padding: '0.75rem',
                backgroundColor: '#ef4444',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: '500',
                cursor: 'pointer',
              }}
            >
              🗑️ Supprimer le compte
            </button>
          </div>
        </div>

        {/* Footer Info */}
        <div
          style={{
            marginTop: '1.5rem',
            padding: '1rem',
            textAlign: 'center',
            color: '#9ca3af',
            fontSize: '0.875rem',
          }}
        >
          <p>Version AZALSCORE 1.0.0</p>
          <p>Dernière mise à jour: 2026-01-23</p>
        </div>
      </div>
    </MainLayout>
  );
}
