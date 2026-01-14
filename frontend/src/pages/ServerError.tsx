/**
 * AZALSCORE - Page 500 (Erreur serveur)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, RefreshCw, ServerCrash } from 'lucide-react';
import { Button } from '@ui/actions';
import { AzalscoreLogo } from '@/components/Logo';

const ServerErrorPage: React.FC = () => {
  const navigate = useNavigate();

  const handleRefresh = () => {
    window.location.reload();
  };

  return (
    <div className="azals-error-page">
      <div className="azals-error-page__content">
        <div className="azals-error-page__logo">
          <AzalscoreLogo size="lg" variant="icon" alt="AZALSCORE" />
        </div>
        <div className="azals-error-page__icon azals-error-page__icon--danger">
          <ServerCrash size={48} />
        </div>
        <h1 className="azals-error-page__code">500</h1>
        <h2 className="azals-error-page__title">Erreur serveur</h2>
        <p className="azals-error-page__message">
          Une erreur inattendue s'est produite. Nos équipes ont été notifiées.
          Veuillez réessayer dans quelques instants.
        </p>
        <div className="azals-error-page__actions">
          <Button variant="ghost" onClick={handleRefresh} leftIcon={<RefreshCw size={16} />}>
            Réessayer
          </Button>
          <Button variant="primary" onClick={() => navigate('/cockpit')} leftIcon={<Home size={16} />}>
            Accueil
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ServerErrorPage;
