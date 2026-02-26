/**
 * AZALSCORE Module - Helpdesk - Ticket Knowledge Tab
 * Onglet articles de base de connaissances lies au ticket
 */

import React from 'react';
import {
  BookOpen, Search, ExternalLink, ThumbsUp, Eye, Tag
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { Ticket } from '../types';
import type { TabContentProps } from '@ui/standards';

/**
 * TicketKnowledgeTab - Articles de base de connaissances
 */
export const TicketKnowledgeTab: React.FC<TabContentProps<Ticket>> = ({ data: ticket }) => {
  // Articles suggeres bases sur la categorie et les mots-cles du ticket
  const suggestedArticles = getSuggestedArticles(ticket);

  return (
    <div className="azals-std-tab-content">
      {/* Recherche */}
      <Card className="mb-4">
        <div className="flex gap-4 items-center">
          <div className="flex-1 relative">
            <Search size={18} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
            <input
              type="text"
              className="azals-input pl-10"
              placeholder="Rechercher dans la base de connaissances..."
            />
          </div>
          <Button variant="secondary" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'searchKnowledge', ticketId: ticket.id } })); }}>Rechercher</Button>
        </div>
      </Card>

      {/* Articles suggeres */}
      <Card title="Articles suggeres" icon={<BookOpen size={18} />}>
        {suggestedArticles.length > 0 ? (
          <div className="azals-knowledge-list">
            {suggestedArticles.map((article) => (
              <ArticleItem key={article.id} article={article} />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <BookOpen size={32} className="text-muted" />
            <p className="text-muted">Aucun article suggere</p>
            <p className="text-sm text-muted mt-1">
              Les suggestions apparaissent en fonction de la categorie et du contenu du ticket.
            </p>
          </div>
        )}
      </Card>

      {/* Actions rapides (ERP only) */}
      <Card
        title="Actions"
        icon={<BookOpen size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <Grid cols={2} gap="md">
          <Button variant="ghost" leftIcon={<BookOpen size={16} />} className="justify-start" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'createArticleFromTicket', ticketId: ticket.id } })); }}>
            Creer un article depuis ce ticket
          </Button>
          <Button variant="ghost" leftIcon={<ExternalLink size={16} />} className="justify-start" onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'sendArticleToClient', ticketId: ticket.id } })); }}>
            Envoyer un article au client
          </Button>
        </Grid>
      </Card>
    </div>
  );
};

/**
 * Composant article
 */
interface ArticleItemProps {
  article: {
    id: string;
    title: string;
    summary: string;
    category_name?: string;
    views: number;
    helpful_count: number;
    tags: string[];
  };
}

const ArticleItem: React.FC<ArticleItemProps> = ({ article }) => {
  return (
    <div className="azals-knowledge-item">
      <div className="azals-knowledge-item__header">
        <h4 className="azals-knowledge-item__title">
          <button
            onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view: 'helpdesk', params: { articleId: article.id } } }))}
            className="text-primary hover:underline text-left"
          >
            {article.title}
          </button>
        </h4>
        <button className="azals-btn-icon" title="Ouvrir" onClick={() => window.dispatchEvent(new CustomEvent('azals:navigate', { detail: { view: 'helpdesk', params: { articleId: article.id } } }))}>
          <ExternalLink size={14} />
        </button>
      </div>
      <p className="azals-knowledge-item__summary text-muted text-sm">
        {article.summary}
      </p>
      <div className="azals-knowledge-item__meta">
        {article.category_name && (
          <span className="azals-badge azals-badge--gray azals-badge--sm">
            {article.category_name}
          </span>
        )}
        <span className="flex items-center gap-1 text-muted text-sm">
          <Eye size={12} />
          {article.views} vues
        </span>
        <span className="flex items-center gap-1 text-muted text-sm">
          <ThumbsUp size={12} />
          {article.helpful_count} utiles
        </span>
      </div>
      {article.tags.length > 0 && (
        <div className="azals-knowledge-item__tags mt-2">
          {article.tags.slice(0, 3).map((tag, i) => (
            <span key={i} className="azals-badge azals-badge--blue azals-badge--sm">
              <Tag size={10} className="mr-1" />
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

/**
 * Obtenir les articles suggeres (simulation)
 */
function getSuggestedArticles(ticket: Ticket) {
  // Dans une implementation reelle, cela viendrait de l'API
  // Ici, on simule des articles bases sur la categorie
  if (!ticket.category_name) return [];

  return [
    {
      id: '1',
      title: `Guide: Resolution des problemes ${ticket.category_name}`,
      summary: `Ce guide vous aide a resoudre les problemes courants lies a ${ticket.category_name?.toLowerCase()}.`,
      category_name: ticket.category_name,
      views: 234,
      helpful_count: 45,
      tags: ['guide', 'resolution', ticket.category_name?.toLowerCase() || ''],
    },
    {
      id: '2',
      title: 'FAQ - Questions frequentes',
      summary: 'Reponses aux questions les plus frequemment posees par nos clients.',
      category_name: 'General',
      views: 1234,
      helpful_count: 189,
      tags: ['faq', 'aide'],
    },
  ];
}

export default TicketKnowledgeTab;
