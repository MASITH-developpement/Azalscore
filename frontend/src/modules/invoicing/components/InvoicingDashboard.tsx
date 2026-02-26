/**
 * AZALSCORE Module - Invoicing - InvoicingDashboard
 * Tableau de bord de facturation
 */

import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { FileText, ArrowRight } from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { useDocuments } from '../hooks';

const formatCurrency = (amount: number, currency = 'EUR'): string => {
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency }).format(amount);
};

const InvoicingDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { data: quotes } = useDocuments('QUOTE', 1, 5, { status: 'DRAFT' });
  const { data: invoices } = useDocuments('INVOICE', 1, 5, { status: 'DRAFT' });

  return (
    <PageWrapper title="Facturation">
      <Grid cols={2} gap="lg">
        <Card className="azals-dashboard-card" onClick={() => navigate('/invoicing/quotes')}>
          <div className="azals-dashboard-card__icon azals-dashboard-card__icon--blue">
            <FileText size={32} />
          </div>
          <div className="azals-dashboard-card__content">
            <h3>Devis</h3>
            <p className="text-muted">
              {quotes?.total || 0} devis en brouillon
            </p>
          </div>
          <ArrowRight size={20} className="azals-dashboard-card__arrow" />
        </Card>

        <Card className="azals-dashboard-card" onClick={() => navigate('/invoicing/invoices')}>
          <div className="azals-dashboard-card__icon azals-dashboard-card__icon--green">
            <FileText size={32} />
          </div>
          <div className="azals-dashboard-card__content">
            <h3>Factures</h3>
            <p className="text-muted">
              {invoices?.total || 0} factures en brouillon
            </p>
          </div>
          <ArrowRight size={20} className="azals-dashboard-card__arrow" />
        </Card>
      </Grid>

      <Grid cols={2} gap="lg" className="mt-6">
        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3>Derniers devis brouillons</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/invoicing/quotes')}
            >
              Voir tout
            </Button>
          </div>
          {quotes?.items && quotes.items.length > 0 ? (
            <ul className="azals-simple-list">
              {quotes.items.slice(0, 5).map((doc) => (
                <li key={doc.id}>
                  <Link to={`/invoicing/quotes/${doc.id}`}>
                    <span>{doc.number}</span>
                    <span className="text-muted">{doc.customer_name}</span>
                    <span>{formatCurrency(doc.total, doc.currency)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted text-center py-4">Aucun devis en brouillon</p>
          )}
        </Card>

        <Card>
          <div className="flex justify-between items-center mb-4">
            <h3>Dernieres factures brouillons</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate('/invoicing/invoices')}
            >
              Voir tout
            </Button>
          </div>
          {invoices?.items && invoices.items.length > 0 ? (
            <ul className="azals-simple-list">
              {invoices.items.slice(0, 5).map((doc) => (
                <li key={doc.id}>
                  <Link to={`/invoicing/invoices/${doc.id}`}>
                    <span>{doc.number}</span>
                    <span className="text-muted">{doc.customer_name}</span>
                    <span>{formatCurrency(doc.total, doc.currency)}</span>
                  </Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-muted text-center py-4">Aucune facture en brouillon</p>
          )}
        </Card>
      </Grid>
    </PageWrapper>
  );
};

export default InvoicingDashboard;
