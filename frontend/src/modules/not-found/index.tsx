/**
 * AZALSCORE - Page 404 Not Found
 * Page d'erreur pour routes invalides
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function NotFoundPage() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        backgroundColor: '#f9fafb',
        padding: '2rem',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '6rem', marginBottom: '1rem' }}>🔍</div>

      <h1
        style={{
          fontSize: '3rem',
          fontWeight: 'bold',
          color: '#111827',
          marginBottom: '1rem',
        }}
      >
        404
      </h1>

      <h2
        style={{
          fontSize: '1.5rem',
          fontWeight: '600',
          color: '#374151',
          marginBottom: '1rem',
        }}
      >
        Page Non Trouvée
      </h2>

      <p
        style={{
          fontSize: '1.125rem',
          color: '#6b7280',
          marginBottom: '0.5rem',
          maxWidth: '600px',
        }}
      >
        La page que vous recherchez n'existe pas ou a été déplacée.
      </p>

      <p
        style={{
          fontSize: '0.875rem',
          color: '#9ca3af',
          marginBottom: '2rem',
          fontFamily: 'monospace',
        }}
      >
        Chemin demandé : {location.pathname}
      </p>

      <div
        style={{
          display: 'flex',
          gap: '1rem',
          flexWrap: 'wrap',
          justifyContent: 'center',
        }}
      >
        <button
          onClick={() => navigate(-1)}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#6b7280',
            color: 'white',
            border: 'none',
            borderRadius: '0.375rem',
            fontSize: '1rem',
            fontWeight: '500',
            cursor: 'pointer',
          }}
        >
          ← Retour
        </button>

        <button
          onClick={() => navigate('/')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '0.375rem',
            fontSize: '1rem',
            fontWeight: '500',
            cursor: 'pointer',
          }}
        >
          🏠 Accueil
        </button>
      </div>

      <div
        style={{
          marginTop: '3rem',
          padding: '1.5rem',
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          maxWidth: '600px',
        }}
      >
        <h3
          style={{
            fontSize: '1.125rem',
            fontWeight: '600',
            marginBottom: '1rem',
          }}
        >
          Suggestions
        </h3>
        <ul
          style={{
            listStyle: 'none',
            padding: 0,
            textAlign: 'left',
            color: '#374151',
          }}
        >
          <li style={{ marginBottom: '0.5rem' }}>
            ✓ Vérifiez l'orthographe de l'URL
          </li>
          <li style={{ marginBottom: '0.5rem' }}>
            ✓ Retournez à la page précédente
          </li>
          <li style={{ marginBottom: '0.5rem' }}>
            ✓ Consultez le menu de navigation
          </li>
          <li>✓ Contactez le support si le problème persiste</li>
        </ul>
      </div>

      <div
        style={{
          marginTop: '2rem',
          fontSize: '0.875rem',
          color: '#9ca3af',
        }}
      >
        AZALSCORE ERP • Version 1.0.0
      </div>
    </div>
  );
}
