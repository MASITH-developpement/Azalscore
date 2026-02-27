/**
 * AZALSCORE Module - Audit - Placeholder Page
 * Page placeholder pour les pages en cours de developpement
 */

import React from 'react';
import { PageWrapper, Card } from '@ui/layout';

export interface PlaceholderPageProps {
  title: string;
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({ title }) => (
  <PageWrapper title={title}>
    <Card>
      <p className="azals-text--muted">Cette page est en cours de developpement.</p>
    </Card>
  </PageWrapper>
);

export default PlaceholderPage;
