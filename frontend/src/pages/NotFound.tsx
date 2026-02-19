/**
 * AZALSCORE - Page 404
 */

import React from 'react';
import { Home, ArrowLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@ui/actions';

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="azals-not-found">
      <div className="azals-not-found__content">
        <h1 className="azals-not-found__code">404</h1>
        <h2 className="azals-not-found__title">Page non trouvée</h2>
        <p className="azals-not-found__message">
          La page que vous recherchez n'existe pas ou a été déplacée.
        </p>
        <div className="azals-not-found__actions">
          <Button variant="ghost" onClick={() => navigate(-1)} leftIcon={<ArrowLeft size={16} />}>
            Retour
          </Button>
          <Button variant="primary" onClick={() => navigate('/cockpit')} leftIcon={<Home size={16} />}>
            Accueil
          </Button>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
