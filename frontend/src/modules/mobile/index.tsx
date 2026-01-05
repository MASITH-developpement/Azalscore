/**
 * AZALSCORE Module - Mobile PWA
 * Configuration et fonctionnalités mobiles spécifiques
 */

import React from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { Smartphone, Bell, Wifi, Settings, Download, QrCode } from 'lucide-react';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import { useUIStore } from '@ui/states';

export const MobileDashboard: React.FC = () => {
  const navigate = useNavigate();
  const isMobile = useUIStore((state) => state.isMobile);

  return (
    <PageWrapper title="Application Mobile" subtitle="Configuration PWA et fonctionnalités mobiles">
      <section className="azals-section">
        <Card title="Statut de l'application">
          <div className="azals-mobile__status">
            <div className="azals-mobile__status-item">
              <Smartphone size={24} />
              <div>
                <strong>Mode d'affichage</strong>
                <span>{isMobile ? 'Mobile' : 'Desktop'}</span>
              </div>
            </div>
            <div className="azals-mobile__status-item">
              <Wifi size={24} />
              <div>
                <strong>Mode hors-ligne</strong>
                <span>Service Worker actif</span>
              </div>
            </div>
          </div>
        </Card>
      </section>

      <section className="azals-section">
        <Grid cols={3} gap="md">
          <Card title="Installation" actions={<Button variant="ghost" size="sm">Installer</Button>}>
            <Download size={32} className="azals-text--primary" />
            <p>Installer l'application sur votre appareil</p>
          </Card>
          <Card title="Notifications" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/mobile/notifications')}>Configurer</Button>}>
            <Bell size={32} className="azals-text--primary" />
            <p>Gérer les notifications push</p>
          </Card>
          <Card title="QR Code" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/mobile/qr')}>Scanner</Button>}>
            <QrCode size={32} className="azals-text--primary" />
            <p>Scanner des codes QR</p>
          </Card>
        </Grid>
      </section>

      <section className="azals-section">
        <Card title="Fonctionnalités mobiles">
          <ul className="azals-mobile__features">
            <li>
              <span className="azals-badge azals-badge--green">Actif</span>
              Accès hors-ligne aux données récentes
            </li>
            <li>
              <span className="azals-badge azals-badge--green">Actif</span>
              Notifications push
            </li>
            <li>
              <span className="azals-badge azals-badge--green">Actif</span>
              Tap-to-Pay (NFC)
            </li>
            <li>
              <span className="azals-badge azals-badge--green">Actif</span>
              Scanner de documents
            </li>
            <li>
              <span className="azals-badge azals-badge--green">Actif</span>
              Géolocalisation interventions
            </li>
          </ul>
        </Card>
      </section>
    </PageWrapper>
  );
};

export const MobileRoutes: React.FC = () => (
  <Routes>
    <Route index element={<MobileDashboard />} />
  </Routes>
);

export default MobileRoutes;
