/**
 * AZALSCORE - Shared Documents Component - LinkedDocumentItem
 * ===========================================================
 * Composant partagé pour afficher un document lié à une entité.
 * Réutilisable dans tous les onglets documents de l'application.
 */

import React from 'react';
import {
  FileText, ExternalLink, Download, Unlink, Eye,
  Clock, Link2
} from 'lucide-react';
import { Button } from '@ui/actions';
import { formatDate } from '@/utils/formatters';

/**
 * Types de liens de document
 */
export type LinkType = 'attachment' | 'reference' | 'related' | 'parent' | 'child';

/**
 * Interface d'un document lié
 */
export interface LinkedDocumentData {
  id: string;
  document_id: string;
  document_name: string;
  document_type?: string;
  document_url?: string;
  link_type: LinkType;
  linked_at: string;
  linked_by?: string;
  notes?: string;
  entity_type?: string;
  entity_id?: string;
  entity_name?: string;
}

/**
 * Props du composant LinkedDocumentItem
 */
export interface LinkedDocumentItemProps {
  link: LinkedDocumentData;
  onView?: (link: LinkedDocumentData) => void;
  onDownload?: (link: LinkedDocumentData) => void;
  onUnlink?: (link: LinkedDocumentData) => void;
  onNavigate?: (link: LinkedDocumentData) => void;
  showLinkType?: boolean;
  showEntity?: boolean;
  className?: string;
}

/**
 * Configuration des types de lien
 */
const LINK_TYPE_CONFIG: Record<LinkType, { label: string; color: string }> = {
  attachment: { label: 'Pièce jointe', color: 'blue' },
  reference: { label: 'Référence', color: 'purple' },
  related: { label: 'Document lié', color: 'green' },
  parent: { label: 'Document parent', color: 'orange' },
  child: { label: 'Document enfant', color: 'cyan' },
};

/**
 * LinkedDocumentItem - Composant d'affichage d'un document lié
 */
export const LinkedDocumentItem: React.FC<LinkedDocumentItemProps> = ({
  link,
  onView,
  onDownload,
  onUnlink,
  onNavigate,
  showLinkType = true,
  showEntity = false,
  className = '',
}) => {
  const linkConfig = LINK_TYPE_CONFIG[link.link_type] || LINK_TYPE_CONFIG.related;

  return (
    <div className={`azals-linked-document ${className}`}>
      <div className="azals-linked-document__icon">
        <FileText size={18} className="text-muted" />
      </div>

      <div className="azals-linked-document__content">
        <div className="azals-linked-document__header">
          <span className="azals-linked-document__name font-medium">
            {link.document_name}
          </span>
          {showLinkType && (
            <span className={`azals-badge azals-badge--${linkConfig.color} azals-badge--sm`}>
              <Link2 size={10} className="mr-1" />
              {linkConfig.label}
            </span>
          )}
        </div>

        {link.notes && (
          <p className="azals-linked-document__notes text-sm text-muted">
            {link.notes}
          </p>
        )}

        <div className="azals-linked-document__meta text-xs text-muted">
          <span>
            <Clock size={10} className="mr-1" />
            {formatDate(link.linked_at)}
          </span>
          {link.linked_by && (
            <span>par {link.linked_by}</span>
          )}
          {showEntity && link.entity_name && (
            <span className="text-primary">
              → {link.entity_name}
            </span>
          )}
        </div>
      </div>

      <div className="azals-linked-document__actions">
        {onView && (
          <span title="Aperçu">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onView(link)}
            >
              <Eye size={14} />
            </Button>
          </span>
        )}
        {onDownload && (
          <span title="Télécharger">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onDownload(link)}
            >
              <Download size={14} />
            </Button>
          </span>
        )}
        {onNavigate && link.entity_id && (
          <span title="Ouvrir l'entité liée">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onNavigate(link)}
            >
              <ExternalLink size={14} />
            </Button>
          </span>
        )}
        {onUnlink && (
          <span title="Délier">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onUnlink(link)}
              className="text-danger"
            >
              <Unlink size={14} />
            </Button>
          </span>
        )}
      </div>
    </div>
  );
};

/**
 * Composant pour afficher une liste de documents liés
 */
export interface LinkedDocumentListProps {
  links: LinkedDocumentData[];
  onView?: (link: LinkedDocumentData) => void;
  onDownload?: (link: LinkedDocumentData) => void;
  onUnlink?: (link: LinkedDocumentData) => void;
  onNavigate?: (link: LinkedDocumentData) => void;
  onAdd?: () => void;
  showLinkType?: boolean;
  showEntity?: boolean;
  emptyMessage?: string;
  className?: string;
}

export const LinkedDocumentList: React.FC<LinkedDocumentListProps> = ({
  links,
  onView,
  onDownload,
  onUnlink,
  onNavigate,
  onAdd,
  showLinkType = true,
  showEntity = false,
  emptyMessage = 'Aucun document lié',
  className = '',
}) => {
  if (links.length === 0) {
    return (
      <div className={`azals-empty azals-empty--sm ${className}`}>
        <Link2 size={32} className="text-muted" />
        <p className="text-muted">{emptyMessage}</p>
        {onAdd && (
          <Button
            variant="secondary"
            size="sm"
            leftIcon={<Link2 size={14} />}
            onClick={onAdd}
            className="mt-2"
          >
            Lier un document
          </Button>
        )}
      </div>
    );
  }

  return (
    <div className={`azals-linked-documents ${className}`}>
      {links.map((link) => (
        <LinkedDocumentItem
          key={link.id}
          link={link}
          onView={onView}
          onDownload={onDownload}
          onUnlink={onUnlink}
          onNavigate={onNavigate}
          showLinkType={showLinkType}
          showEntity={showEntity}
        />
      ))}
    </div>
  );
};

export default LinkedDocumentItem;
