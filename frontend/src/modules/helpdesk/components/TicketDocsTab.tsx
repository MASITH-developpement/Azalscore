/**
 * AZALSCORE Module - Helpdesk - Ticket Docs Tab
 * Onglet documents et pieces jointes du ticket
 */

import React from 'react';
import {
  FileText, Download, Eye, Upload, Trash2,
  File, Image, Paperclip
} from 'lucide-react';
import { Button } from '@ui/actions';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Ticket, TicketAttachment } from '../types';
import { formatDate, formatDateTime } from '@/utils/formatters';

/**
 * TicketDocsTab - Documents du ticket
 */
export const TicketDocsTab: React.FC<TabContentProps<Ticket>> = ({ data: ticket }) => {
  // Collecter toutes les pieces jointes
  const ticketAttachments = ticket.attachments || [];
  const messageAttachments = (ticket.messages || [])
    .flatMap(m => (m.attachments || []).map(a => ({ ...a, from_message: true, message_author: m.author_name })));

  const allAttachments = [...ticketAttachments, ...messageAttachments];

  // Grouper par type
  const images = allAttachments.filter(a => a.mime_type?.startsWith('image/'));
  const documents = allAttachments.filter(a =>
    a.mime_type?.includes('pdf') ||
    a.mime_type?.includes('document') ||
    a.mime_type?.includes('text')
  );
  const others = allAttachments.filter(a =>
    !a.mime_type?.startsWith('image/') &&
    !a.mime_type?.includes('pdf') &&
    !a.mime_type?.includes('document') &&
    !a.mime_type?.includes('text')
  );

  return (
    <div className="azals-std-tab-content">
      {/* Actions */}
      <div className="azals-std-tab-actions mb-4">
        <Button variant="secondary" leftIcon={<Download size={16} />}>
          Telecharger tout
        </Button>
        <Button variant="ghost" leftIcon={<Upload size={16} />}>
          Ajouter un fichier
        </Button>
      </div>

      {allAttachments.length === 0 ? (
        <Card>
          <div className="azals-empty">
            <Paperclip size={48} className="text-muted" />
            <p className="text-muted">Aucune piece jointe</p>
            <Button variant="ghost" leftIcon={<Upload size={14} />}>
              Ajouter un fichier
            </Button>
          </div>
        </Card>
      ) : (
        <Grid cols={2} gap="lg">
          {/* Documents */}
          <Card title="Documents" icon={<FileText size={18} />}>
            {documents.length > 0 ? (
              <ul className="azals-document-list">
                {documents.map((doc) => (
                  <AttachmentItem key={doc.id} attachment={doc} />
                ))}
              </ul>
            ) : (
              <div className="azals-empty azals-empty--sm">
                <FileText size={32} className="text-muted" />
                <p className="text-muted">Aucun document</p>
              </div>
            )}
          </Card>

          {/* Images */}
          <Card title="Images" icon={<Image size={18} />}>
            {images.length > 0 ? (
              <div className="azals-image-grid">
                {images.map((img) => (
                  <div key={img.id} className="azals-image-item">
                    <div className="azals-image-item__preview">
                      {img.file_url ? (
                        <img src={img.file_url} alt={img.name} />
                      ) : (
                        <Image size={32} className="text-muted" />
                      )}
                    </div>
                    <span className="azals-image-item__name text-sm">{img.name}</span>
                    <div className="azals-image-item__actions">
                      <button className="azals-btn-icon" title="Apercu">
                        <Eye size={14} />
                      </button>
                      <button className="azals-btn-icon" title="Telecharger">
                        <Download size={14} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="azals-empty azals-empty--sm">
                <Image size={32} className="text-muted" />
                <p className="text-muted">Aucune image</p>
              </div>
            )}
          </Card>
        </Grid>
      )}

      {/* Autres fichiers (ERP only) */}
      {others.length > 0 && (
        <Card
          title="Autres fichiers"
          icon={<File size={18} />}
          className="mt-4 azals-std-field--secondary"
        >
          <ul className="azals-document-list">
            {others.map((doc) => (
              <AttachmentItem key={doc.id} attachment={doc} />
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
};

/**
 * Composant piece jointe
 */
interface AttachmentItemProps {
  attachment: TicketAttachment & { from_message?: boolean; message_author?: string };
}

const AttachmentItem: React.FC<AttachmentItemProps> = ({ attachment }) => {
  const getIcon = () => {
    const mime = attachment.mime_type || '';
    if (mime.startsWith('image/')) return <Image size={20} className="text-cyan-500" />;
    if (mime.includes('pdf')) return <FileText size={20} className="text-red-500" />;
    if (mime.includes('document') || mime.includes('word')) return <FileText size={20} className="text-blue-500" />;
    if (mime.includes('spreadsheet') || mime.includes('excel')) return <FileText size={20} className="text-green-500" />;
    return <File size={20} className="text-gray-500" />;
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <li className="azals-document-list__item">
      <div className="azals-document-list__icon">{getIcon()}</div>
      <div className="azals-document-list__info">
        <span className="azals-document-list__name">{attachment.name}</span>
        <span className="azals-document-list__meta text-muted text-sm">
          {formatSize(attachment.file_size)}
          {attachment.from_message && attachment.message_author && (
            <span> . Joint par {attachment.message_author}</span>
          )}
          {' . '}{formatDate(attachment.created_at)}
        </span>
      </div>
      <div className="azals-document-list__actions">
        <button className="azals-btn-icon" title="Apercu">
          <Eye size={16} />
        </button>
        <button className="azals-btn-icon" title="Telecharger">
          <Download size={16} />
        </button>
        <button className="azals-btn-icon azals-btn-icon--danger" title="Supprimer">
          <Trash2 size={16} />
        </button>
      </div>
    </li>
  );
};

export default TicketDocsTab;
