/**
 * AZALSCORE Module - Subscriptions - Documents Tab
 * Onglet documents lies a l'abonnement
 */

import React from 'react';
import {
  FileText, Download, Mail, Printer, ExternalLink, Receipt
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';
import type { TabContentProps } from '@ui/standards';
import type { Subscription } from '../types';
import { formatCurrency, formatDate, getPaidInvoicesCount } from '../types';

/**
 * SubscriptionDocumentsTab - Documents
 */
export const SubscriptionDocumentsTab: React.FC<TabContentProps<Subscription>> = ({ data: subscription }) => {
  const paidInvoicesCount = getPaidInvoicesCount(subscription);

  const handleDownloadContract = () => {
    console.log('Download contract for subscription:', subscription.id);
  };

  const handleSendWelcome = () => {
    console.log('Send welcome email for subscription:', subscription.id);
  };

  const handleExportInvoices = () => {
    console.log('Export all invoices for subscription:', subscription.id);
  };

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Contrat d'abonnement */}
        <Card title="Contrat d'abonnement" icon={<FileText size={18} />}>
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <FileText size={48} className="text-primary mx-auto mb-3" />
              <div className="font-medium">Contrat - {subscription.plan_name}</div>
              <div className="text-sm text-muted mt-1">
                Effectif depuis le {formatDate(subscription.start_date)}
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="secondary"
                leftIcon={<Download size={16} />}
                onClick={handleDownloadContract}
                className="flex-1"
              >
                Telecharger PDF
              </Button>
              <Button
                variant="secondary"
                leftIcon={<Printer size={16} />}
                className="flex-1"
              >
                Imprimer
              </Button>
            </div>
          </div>
        </Card>

        {/* Factures */}
        <Card title="Archive des factures" icon={<Receipt size={18} />}>
          <div className="space-y-4">
            <div className="p-4 bg-gray-50 rounded-lg text-center">
              <Receipt size={48} className="text-muted mx-auto mb-3" />
              <div className="font-medium">{paidInvoicesCount} facture{paidInvoicesCount > 1 ? 's' : ''}</div>
              <div className="text-sm text-muted mt-1">
                Archive complete des factures
              </div>
            </div>
            <Button
              variant="secondary"
              leftIcon={<Download size={16} />}
              onClick={handleExportInvoices}
              className="w-full"
              disabled={paidInvoicesCount === 0}
            >
              Exporter toutes les factures (ZIP)
            </Button>
          </div>
        </Card>

        {/* Communications */}
        <Card title="Communications" icon={<Mail size={18} />}>
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <div className="font-medium">Email de bienvenue</div>
                <div className="text-sm text-muted">Envoyer au client</div>
              </div>
              <Button variant="ghost" size="sm" leftIcon={<Mail size={14} />} onClick={handleSendWelcome}>
                Envoyer
              </Button>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <div className="font-medium">Rappel de paiement</div>
                <div className="text-sm text-muted">Si facture impayee</div>
              </div>
              <Button variant="ghost" size="sm" leftIcon={<Mail size={14} />}>
                Envoyer
              </Button>
            </div>
            <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
              <div>
                <div className="font-medium">Confirmation de renouvellement</div>
                <div className="text-sm text-muted">Apres chaque cycle</div>
              </div>
              <Button variant="ghost" size="sm" leftIcon={<Mail size={14} />}>
                Envoyer
              </Button>
            </div>
          </div>
        </Card>

        {/* Liens utiles */}
        <Card title="Liens utiles" icon={<ExternalLink size={18} />} className="azals-std-field--secondary">
          <div className="space-y-2">
            <a href="#" className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded text-primary">
              <ExternalLink size={14} />
              Portail client
            </a>
            <a href="#" className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded text-primary">
              <ExternalLink size={14} />
              Gestion des preferences
            </a>
            <a href="#" className="flex items-center gap-2 p-2 hover:bg-gray-50 rounded text-primary">
              <ExternalLink size={14} />
              Centre d'aide
            </a>
          </div>
        </Card>
      </Grid>
    </div>
  );
};

export default SubscriptionDocumentsTab;
