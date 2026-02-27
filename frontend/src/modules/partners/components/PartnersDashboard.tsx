/**
 * AZALSCORE Module - Partners - PartnersDashboard
 * Dashboard principal du module partenaires
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Building, Contact as ContactIcon } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';

export const PartnersDashboard: React.FC = () => {
  const navigate = useNavigate();

  return (
    <PageWrapper title="Partenaires">
      <Grid cols={3} gap="md">
        <Card
          title="Clients"
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/partners/clients')}>
              Gérer
            </Button>
          }
        >
          <Users size={32} className="azals-text--primary" />
          <p>Gérer vos clients et prospects</p>
        </Card>

        <Card
          title="Fournisseurs"
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/partners/suppliers')}>
              Gérer
            </Button>
          }
        >
          <Building size={32} className="azals-text--primary" />
          <p>Gérer vos fournisseurs</p>
        </Card>

        <Card
          title="Contacts"
          actions={
            <Button variant="ghost" size="sm" onClick={() => navigate('/partners/contacts')}>
              Gérer
            </Button>
          }
        >
          <ContactIcon size={32} className="azals-text--primary" />
          <p>Carnet d'adresses</p>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

export default PartnersDashboard;
