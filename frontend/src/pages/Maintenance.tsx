/**
 * AZALSCORE - Page de Maintenance
 */

import React from 'react';
import { Wrench } from 'lucide-react';
import { AzalscoreLogo } from '@/components/Logo';

const MaintenancePage: React.FC = () => {
  return (
    <div className="azals-maintenance">
      <div className="azals-maintenance__content">
        <div className="azals-maintenance__logo">
          <AzalscoreLogo size="xl" variant="full" alt="AZALSCORE" />
        </div>
        <div className="azals-maintenance__icon">
          <Wrench size={48} />
        </div>
        <h1 className="azals-maintenance__title">Maintenance en cours</h1>
        <p className="azals-maintenance__message">
          AZALSCORE est actuellement en maintenance pour améliorer votre expérience.
          Nous serons de retour très bientôt.
        </p>
        <div className="azals-maintenance__status">
          <p>Durée estimée : quelques minutes</p>
          <p className="azals-maintenance__contact">
            Contact : <a href="mailto:support@azalscore.com">support@azalscore.com</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default MaintenancePage;
