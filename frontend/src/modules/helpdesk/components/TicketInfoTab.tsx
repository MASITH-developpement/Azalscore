/**
 * AZALSCORE Module - Helpdesk - Ticket Info Tab
 * Onglet informations generales du ticket
 */

import React from 'react';
import {
  User, Mail, Phone, Building, Tag, Clock,
  Calendar, Target, AlertTriangle, CheckCircle
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Ticket } from '../types';
import { formatDate, formatDateTime } from '@/utils/formatters';
import {
  PRIORITY_CONFIG, STATUS_CONFIG, SOURCE_CONFIG,
  isTicketOverdue, isSlaDueSoon, getTimeUntilSla,
  getTicketAge, getFirstResponseTime, getResolutionTime
} from '../types';

/**
 * TicketInfoTab - Informations generales du ticket
 */
export const TicketInfoTab: React.FC<TabContentProps<Ticket>> = ({ data: ticket }) => {
  const priorityConfig = PRIORITY_CONFIG[ticket.priority];
  const statusConfig = STATUS_CONFIG[ticket.status];
  const sourceConfig = SOURCE_CONFIG[ticket.source];
  const isOverdue = isTicketOverdue(ticket);
  const slaDueSoon = isSlaDueSoon(ticket);
  const timeUntilSla = getTimeUntilSla(ticket);

  return (
    <div className="azals-std-tab-content">
      {/* Alertes SLA */}
      {isOverdue && (
        <div className="azals-alert azals-alert--danger mb-4">
          <AlertTriangle size={18} />
          <span>SLA depasse - Ce ticket necessite une attention immediate.</span>
        </div>
      )}
      {slaDueSoon && !isOverdue && (
        <div className="azals-alert azals-alert--warning mb-4">
          <Clock size={18} />
          <span>SLA proche - Temps restant: {timeUntilSla}</span>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Sujet et description */}
        <Card title="Details du ticket" icon={<Tag size={18} />}>
          <dl className="azals-dl">
            <dt>Numero</dt>
            <dd className="font-mono font-medium">{ticket.number}</dd>

            <dt>Sujet</dt>
            <dd className="font-medium">{ticket.subject}</dd>

            <dt>Description</dt>
            <dd className="whitespace-pre-wrap">{ticket.description}</dd>

            <dt>Categorie</dt>
            <dd>{ticket.category_name || '-'}</dd>

            <dt>Source</dt>
            <dd>
              <span className="azals-badge azals-badge--gray">
                {sourceConfig.label}
              </span>
            </dd>

            {ticket.tags && ticket.tags.length > 0 && (
              <>
                <dt>Tags</dt>
                <dd>
                  <div className="flex flex-wrap gap-1">
                    {ticket.tags.map((tag, i) => (
                      <span key={i} className="azals-badge azals-badge--blue azals-badge--sm">
                        {tag}
                      </span>
                    ))}
                  </div>
                </dd>
              </>
            )}
          </dl>
        </Card>

        {/* Client et contact */}
        <Card title="Client" icon={<User size={18} />}>
          <dl className="azals-dl">
            <dt>Nom</dt>
            <dd>
              {ticket.customer_name ? (
                <span className="flex items-center gap-2">
                  <Building size={16} className="text-primary" />
                  {ticket.customer_name}
                </span>
              ) : (
                <span className="text-muted">Non renseigne</span>
              )}
            </dd>

            <dt>Email</dt>
            <dd>
              {ticket.customer_email ? (
                <span className="flex items-center gap-2">
                  <Mail size={16} className="text-muted" />
                  <a href={`mailto:${ticket.customer_email}`} className="text-primary hover:underline">
                    {ticket.customer_email}
                  </a>
                </span>
              ) : (
                <span className="text-muted">-</span>
              )}
            </dd>

            <dt>Contact</dt>
            <dd>{ticket.contact_name || '-'}</dd>
          </dl>
        </Card>

        {/* Statut et priorite */}
        <Card title="Statut" icon={<Target size={18} />}>
          <dl className="azals-dl">
            <dt>Statut actuel</dt>
            <dd>
              <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                {statusConfig.label}
              </span>
              <p className="text-sm text-muted mt-1">{statusConfig.description}</p>
            </dd>

            <dt>Priorite</dt>
            <dd>
              <span className={`azals-badge azals-badge--${priorityConfig.color}`}>
                {priorityConfig.label}
              </span>
              <p className="text-sm text-muted mt-1">{priorityConfig.description}</p>
            </dd>

            <dt>Assigne a</dt>
            <dd>
              {ticket.assigned_to_name ? (
                <span className="flex items-center gap-2">
                  <User size={16} className="text-primary" />
                  {ticket.assigned_to_name}
                </span>
              ) : (
                <span className="text-muted">Non assigne</span>
              )}
            </dd>
          </dl>
        </Card>

        {/* Dates et SLA */}
        <Card title="Dates" icon={<Calendar size={18} />}>
          <dl className="azals-dl">
            <dt>Cree le</dt>
            <dd>{formatDateTime(ticket.created_at)}</dd>

            <dt>Age du ticket</dt>
            <dd>{getTicketAge(ticket)}</dd>

            {ticket.sla_due_date && (
              <>
                <dt>Echeance SLA</dt>
                <dd className={isOverdue ? 'text-danger font-medium' : slaDueSoon ? 'text-warning' : ''}>
                  {formatDateTime(ticket.sla_due_date)}
                  {timeUntilSla && (
                    <span className="text-sm ml-2">({timeUntilSla})</span>
                  )}
                </dd>
              </>
            )}

            {ticket.first_response_at && (
              <>
                <dt>1ere reponse</dt>
                <dd>
                  {formatDateTime(ticket.first_response_at)}
                  <span className="text-sm text-muted ml-2">
                    (apres {getFirstResponseTime(ticket)})
                  </span>
                </dd>
              </>
            )}

            {ticket.resolved_at && (
              <>
                <dt>Resolu le</dt>
                <dd>
                  <span className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-success" />
                    {formatDateTime(ticket.resolved_at)}
                  </span>
                  <span className="text-sm text-muted ml-6">
                    (en {getResolutionTime(ticket)})
                  </span>
                </dd>
              </>
            )}

            {ticket.closed_at && (
              <>
                <dt>Ferme le</dt>
                <dd>{formatDateTime(ticket.closed_at)}</dd>
              </>
            )}
          </dl>
        </Card>
      </Grid>

      {/* Satisfaction (ERP only) */}
      {(ticket.satisfaction_rating !== undefined || ticket.status === 'CLOSED') && (
        <Card
          title="Satisfaction client"
          icon={<Target size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          {ticket.satisfaction_rating !== undefined ? (
            <div className="flex items-center gap-4">
              <div className="flex">
                {[1, 2, 3, 4, 5].map((star) => (
                  <span
                    key={star}
                    className={`text-2xl ${star <= (ticket.satisfaction_rating || 0) ? 'text-yellow-400' : 'text-gray-300'}`}
                  >
                    ★
                  </span>
                ))}
              </div>
              <span className="font-medium">{ticket.satisfaction_rating}/5</span>
              {ticket.satisfaction_comment && (
                <p className="text-muted">&quot;{ticket.satisfaction_comment}&quot;</p>
              )}
            </div>
          ) : (
            <p className="text-muted">En attente d'evaluation</p>
          )}
        </Card>
      )}
    </div>
  );
};

export default TicketInfoTab;
