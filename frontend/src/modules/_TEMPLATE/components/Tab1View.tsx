/**
 * AZALSCORE - Module Template - Tab 1
 */

import React from 'react';

export const Tab1View: React.FC = () => {
  return (
    <div style={{ padding: '1rem' }}>
      <h2>Vue 1</h2>
      <p>Contenu de la première vue du module.</p>

      {/* Exemple de carte */}
      <div
        style={{
          backgroundColor: 'white',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          marginTop: '1rem',
        }}
      >
        <h3>Section</h3>
        <p>Exemple de contenu dans une carte.</p>
      </div>
    </div>
  );
};
