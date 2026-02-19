/**
 * AZALSCORE Module - FACTURES - Info Tab
 * Onglet informations générales de la facture
 */

import React, { useEffect } from 'react';
import {
  Building2, MapPin, FileText, Calendar, User, CreditCard,
  Hash, AlertTriangle, Shield, ShieldCheck, ShieldAlert, ShieldX
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import { useRiskAnalysis, useInternalScore } from '@/modules/enrichment';
import { formatDate, formatCurrency } from '@/utils/formatters';
import {
  STATUS_CONFIG, TYPE_CONFIG,
  PAYMENT_METHODS, isOverdue, getDaysUntilDue
} from '../types';
import type { Facture } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * Compact Risk Badge Component
 */
const CompactRiskBadge: React.FC<{ identifier?: string; customerId?: string }> = ({ identifier, customerId }) => {
  const { analysis, isLoading: riskLoading, analyze: analyzeRisk } = useRiskAnalysis();
  const { score: internalScore, isLoading: scoreLoading, analyze: analyzeScore } = useInternalScore();

  useEffect(() => {
    if (identifier && identifier.length >= 9) {
      analyzeRisk(identifier);
    }
  }, [identifier, analyzeRisk]);

  useEffect(() => {
    if (customerId) {
      analyzeScore(customerId);
    }
  }, [customerId, analyzeScore]);

  const isLoading = riskLoading || scoreLoading;

  if (isLoading) {
    return <span className="text-xs text-gray-400">Chargement...</span>;
  }

  // Prioritize external risk if available
  if (analysis) {
    const IconComponent = analysis.level === 'low' ? ShieldCheck :
                          analysis.level === 'medium' ? Shield :
                          analysis.level === 'elevated' ? ShieldAlert : ShieldX;
    const colorClass = analysis.level === 'low' ? 'text-green-600' :
                       analysis.level === 'medium' ? 'text-yellow-600' :
                       analysis.level === 'elevated' ? 'text-orange-600' : 'text-red-600';

    return (
      <div className={`flex items-center gap-1 ${colorClass}`}>
        <IconComponent size={14} />
        <span className="text-xs font-medium">{analysis.score}/100</span>
      </div>
    );
  }

  // Fallback to internal score
  if (internalScore) {
    const colorClass = internalScore.score >= 80 ? 'text-green-600' :
                       internalScore.score >= 60 ? 'text-yellow-600' :
                       internalScore.score >= 40 ? 'text-orange-600' : 'text-red-600';

    return (
      <div className={`flex items-center gap-1 ${colorClass}`}>
        <Shield size={14} />
        <span className="text-xs font-medium">{internalScore.score}/100</span>
      </div>
    );
  }

  return null;
};

/**
 * FactureInfoTab - Informations générales de la facture
 */
export const FactureInfoTab: React.FC<TabContentProps<Facture>> = ({ data: facture }) => {
  const daysUntilDue = getDaysUntilDue(facture.due_date);
  const isFactureOverdue = isOverdue(facture);

  return (
    <div className="azals-std-tab-content">
      {/* Alerte échéance */}
      {isFactureOverdue && (
        <div className="azals-alert azals-alert--danger mb-4">
          <AlertTriangle size={20} />
          <div>
            <strong>Facture en retard</strong>
            <p>L'échéance est dépassée de {Math.abs(daysUntilDue!)} jours.</p>
          </div>
        </div>
      )}

      {/* Document source */}
      {facture.parent_number && (
        <div className="azals-alert azals-alert--info mb-4">
          <FileText size={20} />
          <div>
            <strong>Document source</strong>
            <p className="text-muted">
              {facture.parent_type === 'ORDER' ? 'Commande' : 'Intervention'}: {facture.parent_number}
            </p>
          </div>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Informations client */}
        <Card title="Client" icon={<Building2 size={18} />}>
          <dl className="azals-dl">
            <dt><Building2 size={14} /> Raison sociale</dt>
            <dd className="flex items-center justify-between">
              <strong>{facture.customer_name}</strong>
              <CompactRiskBadge
                identifier={facture.customer_siret || facture.customer_siren}
                customerId={facture.customer_id}
              />
            </dd>

            {facture.customer_code && (
              <>
                <dt className="azals-std-field--secondary"><Hash size={14} /> Code client</dt>
                <dd className="azals-std-field--secondary">{facture.customer_code}</dd>
              </>
            )}

            {(facture.customer_siret || facture.customer_siren) && (
              <>
                <dt className="azals-std-field--secondary"><Hash size={14} /> SIRET/SIREN</dt>
                <dd className="azals-std-field--secondary font-mono">
                  {facture.customer_siret || facture.customer_siren}
                </dd>
              </>
            )}

            {facture.billing_address && (
              <>
                <dt><MapPin size={14} /> Adresse de facturation</dt>
                <dd>
                  {facture.billing_address.line1 && <div>{facture.billing_address.line1}</div>}
                  {facture.billing_address.line2 && <div>{facture.billing_address.line2}</div>}
                  <div>
                    {facture.billing_address.postal_code} {facture.billing_address.city}
                  </div>
                  {facture.billing_address.country && <div>{facture.billing_address.country}</div>}
                </dd>
              </>
            )}
          </dl>
        </Card>

        {/* Informations paiement */}
        <Card title="Paiement" icon={<CreditCard size={18} />}>
          <dl className="azals-dl">
            <dt><Calendar size={14} /> Date d'échéance</dt>
            <dd className={isFactureOverdue ? 'text-danger' : ''}>
              {facture.due_date ? (
                <>
                  {isFactureOverdue && <AlertTriangle size={14} className="mr-1" />}
                  {formatDate(facture.due_date)}
                  {daysUntilDue !== null && !isFactureOverdue && daysUntilDue <= 7 && (
                    <span className="text-warning ml-2">({daysUntilDue} jours)</span>
                  )}
                </>
              ) : (
                <span className="text-muted">Non définie</span>
              )}
            </dd>

            <dt>Conditions de paiement</dt>
            <dd>{facture.payment_terms || 'Net 30 jours'}</dd>

            {facture.payment_method && (
              <>
                <dt>Mode de paiement</dt>
                <dd>{PAYMENT_METHODS[facture.payment_method].label}</dd>
              </>
            )}

            {facture.type === 'INVOICE' && (
              <>
                <dt>Montant payé</dt>
                <dd className={facture.paid_amount > 0 ? 'text-success' : ''}>
                  {formatCurrency(facture.paid_amount, facture.currency)}
                </dd>

                <dt>Reste à payer</dt>
                <dd className={facture.remaining_amount > 0 ? 'text-warning' : 'text-success'}>
                  {formatCurrency(facture.remaining_amount, facture.currency)}
                </dd>
              </>
            )}
          </dl>
        </Card>
      </Grid>

      {/* Informations document */}
      <Card title="Informations document" icon={<FileText size={18} />} className="mt-4">
        <Grid cols={4} gap="md">
          <div className="azals-info-block">
            <span className="azals-info-block__label">Type</span>
            <span className={`azals-badge azals-badge--${TYPE_CONFIG[facture.type].color} azals-badge--outline`}>
              {TYPE_CONFIG[facture.type].label}
            </span>
          </div>

          <div className="azals-info-block">
            <span className="azals-info-block__label">Date d'émission</span>
            <span className="azals-info-block__value">{formatDate(facture.date)}</span>
          </div>

          <div className="azals-info-block">
            <span className="azals-info-block__label">Référence client</span>
            <span className="azals-info-block__value">{facture.reference || '-'}</span>
          </div>

          <div className="azals-info-block">
            <span className="azals-info-block__label">Statut</span>
            {(() => {
              const config = STATUS_CONFIG[facture.status] || { label: facture.status, color: 'gray', icon: null };
              return (
                <span className={`azals-badge azals-badge--${config.color}`}>
                  {config.icon}
                  <span className="ml-1">{config.label}</span>
                </span>
              );
            })()}
          </div>
        </Grid>
      </Card>

      {/* Notes */}
      {(facture.notes || facture.internal_notes || facture.terms) && (
        <Card title="Notes et conditions" icon={<FileText size={18} />} className="mt-4">
          <Grid cols={2} gap="md">
            {facture.notes && (
              <div className="azals-note-block">
                <h4>Notes</h4>
                <p>{facture.notes}</p>
              </div>
            )}

            {facture.terms && (
              <div className="azals-note-block">
                <h4>Conditions</h4>
                <p>{facture.terms}</p>
              </div>
            )}

            {facture.internal_notes && (
              <div className="azals-note-block azals-std-field--secondary">
                <h4>Notes internes</h4>
                <p className="text-muted">{facture.internal_notes}</p>
              </div>
            )}
          </Grid>
        </Card>
      )}

      {/* Métadonnées (ERP only) */}
      <Card
        title="Métadonnées"
        icon={<User size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={4} gap="md">
          <div className="azals-info-block">
            <span className="azals-info-block__label">Créé par</span>
            <span className="azals-info-block__value">{facture.created_by || 'Système'}</span>
          </div>

          <div className="azals-info-block">
            <span className="azals-info-block__label">Créé le</span>
            <span className="azals-info-block__value">{formatDate(facture.created_at)}</span>
          </div>

          {facture.validated_by && (
            <div className="azals-info-block">
              <span className="azals-info-block__label">Validé par</span>
              <span className="azals-info-block__value">{facture.validated_by}</span>
            </div>
          )}

          {facture.validated_at && (
            <div className="azals-info-block">
              <span className="azals-info-block__label">Validé le</span>
              <span className="azals-info-block__value">{formatDate(facture.validated_at)}</span>
            </div>
          )}

          {facture.sent_at && (
            <div className="azals-info-block">
              <span className="azals-info-block__label">Envoyé le</span>
              <span className="azals-info-block__value">{formatDate(facture.sent_at)}</span>
            </div>
          )}

          {facture.paid_at && (
            <div className="azals-info-block">
              <span className="azals-info-block__label">Payé le</span>
              <span className="azals-info-block__value">{formatDate(facture.paid_at)}</span>
            </div>
          )}
        </Grid>
      </Card>
    </div>
  );
};

export default FactureInfoTab;
