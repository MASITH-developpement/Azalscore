/**
 * AZALSCORE - Module Template - Tab 2
 */

import React from 'react';

export const Tab2View: React.FC = () => {
  return (
    <div style={{ padding: '1rem' }}>
      <h2>Vue 2</h2>
      <p>Contenu de la deuxième vue du module.</p>

      {/* Exemple de liste */}
      <div
        style={{
          backgroundColor: 'white',
          padding: '1.5rem',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          marginTop: '1rem',
        }}
      >
        <h3>Liste</h3>
        <ul>
          <li>Élément 1</li>
          <li>Élément 2</li>
          <li>Élément 3</li>
        </ul>
      </div>
    </div>
  );
};
