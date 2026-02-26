/**
 * AZALSCORE Module - Purchases - Dashboard
 * =========================================
 */

import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, ShoppingCart, FileText } from 'lucide-react';
import { Button } from '@ui/actions';
import { KPICard } from '@ui/dashboards';
import { PageWrapper, Card, Grid } from '@ui/layout';
import type { DashboardKPI } from '@/types';
import { usePurchaseSummary } from '../hooks';

// ============================================================================
// Helpers
// ============================================================================

const formatCurrency = (value: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency,
  }).format(value);
};

// ============================================================================
// Component
// ============================================================================

export const PurchasesDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: summary, isLoading } = usePurchaseSummary();

  const kpis: DashboardKPI[] = summary
    ? [
        {
          id: 'suppliers',
          label: 'Fournisseurs actifs',
          value: summary.active_suppliers,
        },
        {
          id: 'pending',
          label: 'Commandes en cours',
          value: summary.pending_orders,
        },
        {
          id: 'value',
          label: 'Valeur en attente',
          value: formatCurrency(summary.pending_value),
        },
        {
          id: 'invoices',
          label: 'Factures a traiter',
          value: summary.pending_invoices,
        },
      ]
    : [];

  return (
    <PageWrapper
      title="Achats"
      subtitle="Gestion des fournisseurs et des achats"
    >
      {isLoading ? (
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Chargement...</p>
        </div>
      ) : (
        <>
          <section className="azals-section">
            <Grid cols={4} gap="md">
              {kpis.map((kpi) => (
                <KPICard key={kpi.id} kpi={kpi} />
              ))}
            </Grid>
          </section>

          <section className="azals-section">
            <Grid cols={3} gap="md">
              <Card
                title="Fournisseurs"
                actions={
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => navigate('/purchases/suppliers')}
                  >
                    Gerer
                  </Button>
                }
              >
                <div className="azals-card__icon-section">
                  <Users size={32} className="azals-text--primary" />
                  <p>Carnet fournisseurs</p>
                </div>
              </Card>

              <Card
                title="Commandes"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/purchases/orders')}>
                    Gerer
                  </Button>
                }
              >
                <div className="azals-card__icon-section">
                  <ShoppingCart size={32} className="azals-text--primary" />
                  <p>Commandes fournisseurs</p>
                </div>
              </Card>

              <Card
                title="Factures"
                actions={
                  <Button variant="ghost" size="sm" onClick={() => navigate('/purchases/invoices')}>
                    Gerer
                  </Button>
                }
              >
                <div className="azals-card__icon-section">
                  <FileText size={32} className="azals-text--primary" />
                  <p>Factures fournisseurs</p>
                </div>
              </Card>
            </Grid>
          </section>
        </>
      )}
    </PageWrapper>
  );
};

export default PurchasesDashboard;
