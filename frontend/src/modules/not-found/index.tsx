/**
 * AZALSCORE - Page 404 Not Found
 * Page d'erreur elegante pour routes invalides
 */

import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

export default function NotFoundPage() {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="azals-not-found">
      <div>
        <div className="azals-not-found__code">404</div>

        <h2 className="azals-not-found__title">Page non trouvee</h2>

        <p className="azals-not-found__message">
          La page <code style={{ fontSize: '0.875rem', background: 'var(--azals-gray-100)', padding: '2px 6px', borderRadius: '4px' }}>{location.pathname}</code> n'existe pas ou a ete deplacee.
        </p>

        <div className="azals-not-found__actions">
          <button
            onClick={() => navigate(-1)}
            className="azals-btn azals-btn--secondary"
          >
            Retour
          </button>

          <button
            onClick={() => navigate('/cockpit')}
            className="azals-btn azals-btn--primary"
          >
            Tableau de bord
          </button>
        </div>
      </div>
    </div>
  );
}
