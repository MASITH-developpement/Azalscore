/**
 * AZALSCORE - Page 403 (Accès interdit)
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Home, ArrowLeft, ShieldX } from 'lucide-react';
import { Button } from '@ui/actions';
import { AzalscoreLogo } from '@/components/Logo';

const ForbiddenPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="azals-error-page">
      <div className="azals-error-page__content">
        <div className="azals-error-page__logo">
          <AzalscoreLogo size="lg" variant="icon" alt="AZALSCORE" />
        </div>
        <div className="azals-error-page__icon azals-error-page__icon--warning">
          <ShieldX size={48} />
        </div>
        <h1 className="azals-error-page__code">403</h1>
        <h2 className="azals-error-page__title">Accès interdit</h2>
        <p className="azals-error-page__message">
          Vous n'avez pas les autorisations nécessaires pour accéder à cette ressource.
          Contactez votre administrateur si vous pensez qu'il s'agit d'une erreur.
        </p>
        <div className="azals-error-page__actions">
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

export default ForbiddenPage;
