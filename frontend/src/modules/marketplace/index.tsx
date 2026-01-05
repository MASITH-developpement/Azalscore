/**
 * AZALSCORE Module - Marketplace
 * Gestion de la place de marché
 */

import React from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { Store, Users, Package, BarChart3 } from 'lucide-react';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';

export const MarketplaceDashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageWrapper title="Marketplace" subtitle="Place de marché multi-vendeurs">
      <section className="azals-section">
        <Grid cols={3} gap="md">
          <Card title="Vendeurs" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/marketplace/sellers')}>Gérer</Button>}>
            <Users size={32} className="azals-text--primary" />
            <p>Gestion des vendeurs partenaires</p>
          </Card>
          <Card title="Catalogue" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/marketplace/catalog')}>Voir</Button>}>
            <Package size={32} className="azals-text--primary" />
            <p>Catalogue unifié marketplace</p>
          </Card>
          <Card title="Statistiques" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/marketplace/stats')}>Voir</Button>}>
            <BarChart3 size={32} className="azals-text--primary" />
            <p>Performance et analytics</p>
          </Card>
        </Grid>
      </section>
    </PageWrapper>
  );
};

export const MarketplaceRoutes: React.FC = () => (
  <Routes>
    <Route index element={<MarketplaceDashboard />} />
  </Routes>
);

export default MarketplaceRoutes;
