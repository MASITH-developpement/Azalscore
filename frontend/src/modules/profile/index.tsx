/**
 * AZALSCORE - Module Profil Utilisateur
 * Gestion du profil utilisateur
 */

import React, { useState } from 'react';
import { Key, ShieldCheck, Smartphone, User, Save, Edit, X } from 'lucide-react';
import { MainLayout } from '@/ui-engine/layouts/MainLayout';

export default function ProfileModule() {
  const [user, setUser] = useState({
    name: 'Utilisateur',
    email: 'user@azalscore.com',
    role: 'Admin',
  });

  const [editing, setEditing] = useState(false);

  return (
    <MainLayout title="Mon Profil">
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Header Profil */}
        <div className="azals-card" style={{ textAlign: 'center', marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <div style={{ marginBottom: 'var(--azals-spacing-md)' }}>
              <User size={64} className="text-muted" />
            </div>
            <h1 className="azals-card__title" style={{ fontSize: 'var(--azals-font-size-2xl)' }}>
              {user.name}
            </h1>
            <p className="text-muted" style={{ marginBottom: 'var(--azals-spacing-sm)' }}>
              {user.email}
            </p>
            <span className="azals-badge azals-badge--blue">
              {user.role}
            </span>
          </div>
        </div>

        {/* Informations Personnelles */}
        <div className="azals-card" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <div className="flex justify-between items-center" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              <h2 className="azals-card__title">
                Informations Personnelles
              </h2>
              <button
                className={`azals-btn azals-btn--sm ${editing ? 'azals-btn--ghost' : 'azals-btn--primary'}`}
                onClick={() => setEditing(!editing)}
              >
                {editing ? <><X size={16} /> Annuler</> : <><Edit size={16} /> Modifier</>}
              </button>
            </div>

            <div style={{ display: 'grid', gap: 'var(--azals-spacing-md)' }}>
              <div className="azals-form-field">
                <label htmlFor="profile-name">Nom complet</label>
                {editing ? (
                  <input
                    id="profile-name"
                    type="text"
                    className="azals-input"
                    value={user.name}
                    onChange={(e) => setUser({ ...user, name: e.target.value })}
                  />
                ) : (
                  <p id="profile-name">{user.name}</p>
                )}
              </div>

              <div className="azals-form-field">
                <label htmlFor="profile-email">Email</label>
                {editing ? (
                  <input
                    id="profile-email"
                    type="email"
                    className="azals-input"
                    value={user.email}
                    onChange={(e) => setUser({ ...user, email: e.target.value })}
                  />
                ) : (
                  <p id="profile-email">{user.email}</p>
                )}
              </div>

              {editing && (
                <button
                  className="azals-btn azals-btn--success"
                  onClick={() => setEditing(false)}
                >
                  <Save size={16} /> Enregistrer les modifications
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Sécurité */}
        <div className="azals-card">
          <div className="azals-card__body">
            <h2 className="azals-card__title" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              Sécurité
            </h2>

            <div style={{ display: 'grid', gap: 'var(--azals-spacing-md)' }}>
              <button className="azals-btn azals-btn--primary" style={{ justifyContent: 'flex-start' }} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'changePassword' } })); }}>
                <Key size={16} /> Changer le mot de passe
              </button>

              <button className="azals-btn azals-btn--secondary" style={{ justifyContent: 'flex-start' }} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'configure2FA' } })); }}>
                <ShieldCheck size={16} /> Configurer l'authentification à deux facteurs
              </button>

              <button className="azals-btn azals-btn--secondary" style={{ justifyContent: 'flex-start' }} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'manageSessions' } })); }}>
                <Smartphone size={16} /> Gérer les sessions actives
              </button>
            </div>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
