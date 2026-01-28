/**
 * AZALSCORE Module - INTERVENTIONS - Financial Tab
 * Onglet financier de l'intervention (facturation)
 */

import React from 'react';
import {
  Euro, FileText, CheckCircle2, AlertTriangle, Clock,
  CreditCard, Receipt
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Intervention } from '../types';
import { formatCurrency, formatDate, formatDuration } from '@/utils/formatters';

/**
 * InterventionFinancialTab - Facturation de l'intervention
 */
export const InterventionFinancialTab: React.FC<TabContentProps<Intervention>> = ({ data: intervention }) => {
  const isFacturable = intervention.facturable !== false;
  const isFactured = !!intervention.facture_id;
  const montantHT = intervention.montant_ht || 0;
  const montantTTC = intervention.montant_ttc || montantHT * 1.2; // Estimation TVA 20%

  // Calcul coût estimé basé sur la durée
  const tauxHoraireEstime = 65; // EUR/h
  const coutEstime = intervention.duree_reelle_minutes
    ? (intervention.duree_reelle_minutes / 60) * tauxHoraireEstime
    : intervention.duree_prevue_minutes
      ? (intervention.duree_prevue_minutes / 60) * tauxHoraireEstime
      : 0;

  return (
    <div className="azals-std-tab-content">
      {/* Alerte non facturable */}
      {!isFacturable && (
        <div className="azals-alert azals-alert--info mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Intervention non facturable</strong>
            <p>Cette intervention n'est pas marquée comme facturable au client.</p>
          </div>
        </div>
      )}

      {/* Statut facturation */}
      <Card title="État de facturation" icon={<Receipt size={18} />} className="mb-4">
        <div className="azals-facturation-status">
          {isFactured ? (
            <div className="azals-facturation-status__card azals-facturation-status__card--success">
              <CheckCircle2 size={32} className="text-success" />
              <div>
                <h4 className="font-medium">Facturée</h4>
                <p className="text-sm text-muted">
                  Facture {intervention.facture_reference}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('azals:navigate', {
                    detail: { view: 'factures', params: { id: intervention.facture_id } }
                  }));
                }}
              >
                Voir la facture
              </Button>
            </div>
          ) : intervention.statut === 'TERMINEE' && isFacturable ? (
            <div className="azals-facturation-status__card azals-facturation-status__card--warning">
              <Clock size={32} className="text-warning" />
              <div>
                <h4 className="font-medium">À facturer</h4>
                <p className="text-sm text-muted">
                  L'intervention est terminée et peut être facturée.
                </p>
              </div>
              <Button
                variant="secondary"
                size="sm"
                leftIcon={<FileText size={14} />}
                onClick={() => {
                  window.dispatchEvent(new CustomEvent('azals:navigate', {
                    detail: { view: 'factures', params: { action: 'create', intervention_id: intervention.id } }
                  }));
                }}
              >
                Créer la facture
              </Button>
            </div>
          ) : (
            <div className="azals-facturation-status__card">
              <AlertTriangle size={32} className="text-muted" />
              <div>
                <h4 className="font-medium text-muted">
                  {isFacturable ? 'En attente' : 'Non facturable'}
                </h4>
                <p className="text-sm text-muted">
                  {isFacturable
                    ? 'L\'intervention doit être terminée avant de pouvoir être facturée.'
                    : 'Cette intervention n\'est pas facturable.'}
                </p>
              </div>
            </div>
          )}
        </div>
      </Card>

      <Grid cols={2} gap="lg">
        {/* Montants */}
        <Card title="Montants" icon={<Euro size={18} />}>
          <table className="azals-table azals-table--simple">
            <tbody>
              <tr>
                <td>Montant HT</td>
                <td className="text-right font-medium">{formatCurrency(montantHT)}</td>
              </tr>
              <tr>
                <td>TVA (20%)</td>
                <td className="text-right">{formatCurrency(montantTTC - montantHT)}</td>
              </tr>
              <tr className="azals-table__total">
                <td className="font-medium">Montant TTC</td>
                <td className="text-right font-medium">{formatCurrency(montantTTC)}</td>
              </tr>
            </tbody>
          </table>
        </Card>

        {/* Coût estimé */}
        <Card title="Coût estimé" icon={<CreditCard size={18} />}>
          <table className="azals-table azals-table--simple">
            <tbody>
              <tr>
                <td>Durée</td>
                <td className="text-right">
                  {formatDuration(intervention.duree_reelle_minutes || intervention.duree_prevue_minutes)}
                </td>
              </tr>
              <tr>
                <td>Taux horaire estimé</td>
                <td className="text-right">{formatCurrency(tauxHoraireEstime)}/h</td>
              </tr>
              <tr className="azals-table__total">
                <td className="font-medium">Coût estimé</td>
                <td className="text-right font-medium">{formatCurrency(coutEstime)}</td>
              </tr>
            </tbody>
          </table>

          {/* Marge estimée */}
          {montantHT > 0 && (
            <div className="mt-4 pt-4 border-t">
              <div className="flex justify-between items-center">
                <span className="text-muted">Marge estimée</span>
                <span className={`font-medium ${montantHT - coutEstime > 0 ? 'text-success' : 'text-danger'}`}>
                  {formatCurrency(montantHT - coutEstime)} ({Math.round(((montantHT - coutEstime) / montantHT) * 100)}%)
                </span>
              </div>
            </div>
          )}
        </Card>
      </Grid>

      {/* Détail facturation (ERP only) */}
      <Card title="Détail facturation" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
        <dl className="azals-dl">
          <div className="azals-dl__row">
            <dt>Facturable</dt>
            <dd>
              <span className={`azals-badge azals-badge--${isFacturable ? 'green' : 'gray'}`}>
                {isFacturable ? 'Oui' : 'Non'}
              </span>
            </dd>
          </div>
          <div className="azals-dl__row">
            <dt>Facture liée</dt>
            <dd>
              {intervention.facture_reference ? (
                <button
                  className="azals-link"
                  onClick={() => {
                    window.dispatchEvent(new CustomEvent('azals:navigate', {
                      detail: { view: 'factures', params: { id: intervention.facture_id } }
                    }));
                  }}
                >
                  {intervention.facture_reference}
                </button>
              ) : (
                '-'
              )}
            </dd>
          </div>
          {intervention.affaire_reference && (
            <div className="azals-dl__row">
              <dt>Affaire</dt>
              <dd>
                <button
                  className="azals-link"
                  onClick={() => {
                    window.dispatchEvent(new CustomEvent('azals:navigate', {
                      detail: { view: 'affaires', params: { id: intervention.affaire_id } }
                    }));
                  }}
                >
                  {intervention.affaire_reference}
                </button>
              </dd>
            </div>
          )}
        </dl>
      </Card>
    </div>
  );
};

export default InterventionFinancialTab;
