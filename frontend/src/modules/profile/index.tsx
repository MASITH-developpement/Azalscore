/**
 * AZALSCORE - Module Profil Utilisateur
 * Gestion du profil utilisateur
 */

import React, { useState } from 'react';
import { MainLayout } from '@/ui-engine/layouts/MainLayout';

export default function ProfileModule() {
  const [user, setUser] = useState({
    name: 'Utilisateur',
    email: 'user@azalscore.com',
    role: 'Admin',
    avatar: '👤',
  });

  const [editing, setEditing] = useState(false);

  return (
    <MainLayout title="Mon Profil">
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Header Profil */}
        <div
          style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginBottom: '1.5rem',
            textAlign: 'center',
          }}
        >
          <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>{user.avatar}</div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            {user.name}
          </h1>
          <p style={{ color: '#6b7280', marginBottom: '0.5rem' }}>{user.email}</p>
          <span
            style={{
              display: 'inline-block',
              padding: '0.25rem 0.75rem',
              backgroundColor: '#dbeafe',
              color: '#1e40af',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
              fontWeight: '500',
            }}
          >
            {user.role}
          </span>
        </div>

        {/* Informations Personnelles */}
        <div
          style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            marginBottom: '1.5rem',
          }}
        >
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.5rem',
            }}
          >
            <h2 style={{ fontSize: '1.25rem', fontWeight: '600' }}>
              Informations Personnelles
            </h2>
            <button
              onClick={() => setEditing(!editing)}
              style={{
                padding: '0.5rem 1rem',
                backgroundColor: editing ? '#e5e7eb' : '#3b82f6',
                color: editing ? '#374151' : 'white',
                border: 'none',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontWeight: '500',
              }}
            >
              {editing ? 'Annuler' : 'Modifier'}
            </button>
          </div>

          <div style={{ display: 'grid', gap: '1rem' }}>
            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                Nom complet
              </label>
              {editing ? (
                <input
                  type="text"
                  value={user.name}
                  onChange={(e) => setUser({ ...user, name: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem',
                  }}
                />
              ) : (
                <p style={{ color: '#374151' }}>{user.name}</p>
              )}
            </div>

            <div>
              <label style={{ display: 'block', fontSize: '0.875rem', fontWeight: '500', marginBottom: '0.25rem' }}>
                Email
              </label>
              {editing ? (
                <input
                  type="email"
                  value={user.email}
                  onChange={(e) => setUser({ ...user, email: e.target.value })}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    border: '1px solid #d1d5db',
                    borderRadius: '0.375rem',
                  }}
                />
              ) : (
                <p style={{ color: '#374151' }}>{user.email}</p>
              )}
            </div>

            {editing && (
              <button
                onClick={() => setEditing(false)}
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
                Enregistrer les modifications
              </button>
            )}
          </div>
        </div>

        {/* Sécurité */}
        <div
          style={{
            backgroundColor: 'white',
            padding: '2rem',
            borderRadius: '0.5rem',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          }}
        >
          <h2 style={{ fontSize: '1.25rem', fontWeight: '600', marginBottom: '1.5rem' }}>
            Sécurité
          </h2>

          <div style={{ display: 'grid', gap: '1rem' }}>
            <button
              style={{
                padding: '0.75rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: '500',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              🔑 Changer le mot de passe
            </button>

            <button
              style={{
                padding: '0.75rem',
                backgroundColor: '#8b5cf6',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: '500',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              🔐 Configurer l'authentification à deux facteurs
            </button>

            <button
              style={{
                padding: '0.75rem',
                backgroundColor: '#f59e0b',
                color: 'white',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: '500',
                cursor: 'pointer',
                textAlign: 'left',
              }}
            >
              📱 Gérer les sessions actives
            </button>
          </div>
        </div>
      </div>
    </MainLayout>
  );
}
