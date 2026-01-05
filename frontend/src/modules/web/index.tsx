/**
 * AZALSCORE Module - Site Web
 * Pages, Blog, SEO
 */

import React from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { FileText, BookOpen, Search, Settings } from 'lucide-react';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';

export const WebDashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageWrapper title="Site Web" subtitle="Gestion du site MASITH">
      <section className="azals-section">
        <Grid cols={3} gap="md">
          <Card title="Pages" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/web/pages')}>Gérer</Button>}>
            <FileText size={32} className="azals-text--primary" />
            <p>Gestion des pages du site</p>
          </Card>
          <Card title="Blog" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/web/blog')}>Gérer</Button>}>
            <BookOpen size={32} className="azals-text--primary" />
            <p>Articles et publications</p>
          </Card>
          <Card title="SEO" actions={<Button variant="ghost" size="sm" onClick={() => navigate('/web/seo')}>Configurer</Button>}>
            <Search size={32} className="azals-text--primary" />
            <p>Référencement et métadonnées</p>
          </Card>
        </Grid>
      </section>
    </PageWrapper>
  );
};

export const WebRoutes: React.FC = () => (
  <Routes>
    <Route index element={<WebDashboard />} />
  </Routes>
);

export default WebRoutes;
