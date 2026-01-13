/**
 * Document Detail View - Comptabilité Automatisée
 *
 * Affiche le détail d'un document avec:
 * - Prévisualisation du fichier
 * - Données OCR extraites
 * - Classification IA
 * - Écriture générée (si applicable)
 * - Actions selon le rôle
 */

import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  FileText,
  Brain,
  Calculator,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Eye,
  Download,
  MessageSquare,
  Link2,
  Edit3,
  History,
  User,
  Building,
  Calendar,
  Hash,
  CreditCard,
  Receipt,
  Tag,
} from 'lucide-react';
import { api } from '@core/api-client';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button, ButtonGroup } from '@ui/actions';
import { StatusBadge } from '@ui/dashboards';
import { Modal, Input, TextArea, Select } from '@ui/forms';
import { useAuth } from '@core/auth';

// ============================================================
// TYPES
// ============================================================

interface ExtractedField {
  field_name: string;
  value: string | null;
  confidence: number;
  bounding_box?: { x: number; y: number; width: number; height: number };
}

interface OCRResult {
  id: string;
  raw_text: string;
  extracted_fields: ExtractedField[];
  confidence_score: number;
  processing_time_ms: number;
  ocr_engine: string;
  processed_at: string;
}

interface AIClassification {
  id: string;
  document_type: string;
  confidence_level: string;
  confidence_score: number;
  suggested_vendor_id: string | null;
  suggested_vendor_name: string | null;
  suggested_account_code: string | null;
  suggested_account_name: string | null;
  suggested_journal_code: string | null;
  suggested_tax_code: string | null;
  reasoning: string | null;
  processed_at: string;
}

interface AutoEntry {
  id: string;
  status: string;
  journal_code: string;
  entry_date: string;
  description: string;
  lines: {
    account_code: string;
    account_name: string;
    debit: number;
    credit: number;
    label: string;
  }[];
  total_debit: number;
  total_credit: number;
  validated_at: string | null;
  validated_by: string | null;
}

interface DocumentHistory {
  id: string;
  action: string;
  actor_name: string;
  comment: string | null;
  created_at: string;
}

interface DocumentDetail {
  id: string;
  tenant_id: string;
  document_type: string;
  status: string;
  source: string;
  reference: string | null;
  partner_id: string | null;
  partner_name: string | null;
  amount_ht: number | null;
  amount_tva: number | null;
  amount_total: number | null;
  currency: string;
  document_date: string | null;
  due_date: string | null;
  payment_status: string;
  original_filename: string;
  file_path: string;
  file_mime_type: string;
  notes: string | null;
  tags: string[];
  ocr_result: OCRResult | null;
  ai_classification: AIClassification | null;
  auto_entry: AutoEntry | null;
  history: DocumentHistory[];
  received_at: string;
  created_at: string;
  updated_at: string;
}

// ============================================================
// API HOOKS
// ============================================================

const useDocumentDetail = (documentId: string) => {
  return useQuery({
    queryKey: ['accounting', 'document', documentId],
    queryFn: async () => {
      const response = await api.get<DocumentDetail>(
        `/accounting/documents/${documentId}`
      );
      return response.data;
    },
    enabled: !!documentId,
  });
};

const useValidateDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      documentId,
      comment,
    }: {
      documentId: string;
      comment?: string;
    }) => {
      const response = await api.post(
        `/accounting/expert/documents/${documentId}/validate`,
        { comment }
      );
      return response.data;
    },
    onSuccess: (_, { documentId }) => {
      queryClient.invalidateQueries({
        queryKey: ['accounting', 'document', documentId],
      });
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useRejectDocument = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      documentId,
      reason,
    }: {
      documentId: string;
      reason: string;
    }) => {
      const response = await api.post(
        `/accounting/expert/documents/${documentId}/reject`,
        { reason }
      );
      return response.data;
    },
    onSuccess: (_, { documentId }) => {
      queryClient.invalidateQueries({
        queryKey: ['accounting', 'document', documentId],
      });
      queryClient.invalidateQueries({ queryKey: ['accounting'] });
    },
  });
};

const useUpdateDocumentContext = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      documentId,
      notes,
      tags,
    }: {
      documentId: string;
      notes?: string;
      tags?: string[];
    }) => {
      const response = await api.patch(
        `/accounting/assistante/documents/${documentId}/context`,
        { notes, tags }
      );
      return response.data;
    },
    onSuccess: (_, { documentId }) => {
      queryClient.invalidateQueries({
        queryKey: ['accounting', 'document', documentId],
      });
    },
  });
};

// ============================================================
// HELPER FUNCTIONS
// ============================================================

const formatCurrency = (value: number | null, currency = 'EUR') =>
  value !== null
    ? new Intl.NumberFormat('fr-FR', {
        style: 'currency',
        currency,
      }).format(value)
    : '-';

const formatDate = (dateStr: string | null) =>
  dateStr ? new Date(dateStr).toLocaleDateString('fr-FR') : '-';

const formatDateTime = (dateStr: string) =>
  new Date(dateStr).toLocaleString('fr-FR');

const getStatusVariant = (
  status: string
): 'success' | 'warning' | 'danger' | 'info' | 'default' => {
  switch (status) {
    case 'ACCOUNTED':
    case 'VALIDATED':
      return 'success';
    case 'PENDING_VALIDATION':
    case 'ANALYZED':
      return 'warning';
    case 'ERROR':
    case 'REJECTED':
      return 'danger';
    case 'PROCESSING':
      return 'info';
    default:
      return 'default';
  }
};

const getStatusLabel = (status: string): string => {
  const labels: Record<string, string> = {
    RECEIVED: 'Reçu',
    PROCESSING: 'En traitement',
    ANALYZED: 'Analysé',
    PENDING_VALIDATION: 'À valider',
    VALIDATED: 'Validé',
    ACCOUNTED: 'Comptabilisé',
    REJECTED: 'Rejeté',
    ERROR: 'Erreur',
  };
  return labels[status] || status;
};

const getTypeLabel = (type: string): string => {
  const labels: Record<string, string> = {
    INVOICE_RECEIVED: 'Facture fournisseur',
    INVOICE_SENT: 'Facture client',
    EXPENSE_NOTE: 'Note de frais',
    CREDIT_NOTE_RECEIVED: 'Avoir reçu',
    CREDIT_NOTE_SENT: 'Avoir émis',
    QUOTE: 'Devis',
    PURCHASE_ORDER: 'Bon de commande',
    OTHER: 'Autre',
  };
  return labels[type] || type;
};

const getConfidenceVariant = (
  confidence: string
): 'success' | 'warning' | 'danger' | 'info' => {
  switch (confidence) {
    case 'HIGH':
      return 'success';
    case 'MEDIUM':
      return 'warning';
    case 'LOW':
    case 'VERY_LOW':
      return 'danger';
    default:
      return 'info';
  }
};

const getSourceLabel = (source: string): string => {
  const labels: Record<string, string> = {
    EMAIL: 'Email',
    UPLOAD: 'Upload manuel',
    API: 'API',
    BANK: 'Banque',
    SCAN: 'Scanner',
  };
  return labels[source] || source;
};

// ============================================================
// SUB-COMPONENTS
// ============================================================

const DocumentPreview: React.FC<{ document: DocumentDetail }> = ({
  document,
}) => {
  const previewUrl = `/api/accounting/documents/${document.id}/preview`;

  return (
    <Card title="Document" icon={<FileText size={18} />} noPadding>
      <div className="azals-auto-accounting__doc-preview">
        {document.file_mime_type.startsWith('image/') ? (
          <img src={previewUrl} alt={document.original_filename} />
        ) : document.file_mime_type === 'application/pdf' ? (
          <iframe src={previewUrl} title={document.original_filename} />
        ) : (
          <div className="azals-auto-accounting__doc-preview-placeholder">
            <FileText size={48} />
            <p>{document.original_filename}</p>
          </div>
        )}
      </div>
      <div className="azals-auto-accounting__doc-preview-actions">
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<Eye size={14} />}
          onClick={() => { window.open(previewUrl, '_blank'); }}
        >
          Ouvrir
        </Button>
        <Button
          variant="ghost"
          size="sm"
          leftIcon={<Download size={14} />}
          onClick={() => {
            const link = document.createElement('a');
            link.href = previewUrl;
            link.download = document.original_filename;
            link.click();
          }}
        >
          Télécharger
        </Button>
      </div>
    </Card>
  );
};

const DocumentInfo: React.FC<{ document: DocumentDetail }> = ({ document }) => {
  return (
    <Card title="Informations" icon={<Receipt size={18} />}>
      <div className="azals-auto-accounting__info-grid">
        <div className="azals-auto-accounting__info-item">
          <Tag size={14} />
          <span className="azals-auto-accounting__info-label">Type</span>
          <span className="azals-auto-accounting__info-value">
            {getTypeLabel(document.document_type)}
          </span>
        </div>

        <div className="azals-auto-accounting__info-item">
          <Clock size={14} />
          <span className="azals-auto-accounting__info-label">Statut</span>
          <StatusBadge variant={getStatusVariant(document.status)} size="sm" status={getStatusLabel(document.status)} />
        </div>

        {document.reference && (
          <div className="azals-auto-accounting__info-item">
            <Hash size={14} />
            <span className="azals-auto-accounting__info-label">Référence</span>
            <span className="azals-auto-accounting__info-value">
              {document.reference}
            </span>
          </div>
        )}

        {document.partner_name && (
          <div className="azals-auto-accounting__info-item">
            <Building size={14} />
            <span className="azals-auto-accounting__info-label">Partenaire</span>
            <span className="azals-auto-accounting__info-value">
              {document.partner_name}
            </span>
          </div>
        )}

        {document.document_date && (
          <div className="azals-auto-accounting__info-item">
            <Calendar size={14} />
            <span className="azals-auto-accounting__info-label">Date document</span>
            <span className="azals-auto-accounting__info-value">
              {formatDate(document.document_date)}
            </span>
          </div>
        )}

        {document.due_date && (
          <div className="azals-auto-accounting__info-item">
            <Calendar size={14} />
            <span className="azals-auto-accounting__info-label">Échéance</span>
            <span className="azals-auto-accounting__info-value">
              {formatDate(document.due_date)}
            </span>
          </div>
        )}

        <div className="azals-auto-accounting__info-item azals-auto-accounting__info-item--full">
          <CreditCard size={14} />
          <span className="azals-auto-accounting__info-label">Montants</span>
          <div className="azals-auto-accounting__info-amounts">
            {document.amount_ht !== null && (
              <span>HT: {formatCurrency(document.amount_ht, document.currency)}</span>
            )}
            {document.amount_tva !== null && (
              <span>TVA: {formatCurrency(document.amount_tva, document.currency)}</span>
            )}
            <strong>
              TTC: {formatCurrency(document.amount_total, document.currency)}
            </strong>
          </div>
        </div>

        <div className="azals-auto-accounting__info-item">
          <User size={14} />
          <span className="azals-auto-accounting__info-label">Source</span>
          <span className="azals-auto-accounting__info-value">
            {getSourceLabel(document.source)}
          </span>
        </div>

        <div className="azals-auto-accounting__info-item">
          <Clock size={14} />
          <span className="azals-auto-accounting__info-label">Reçu le</span>
          <span className="azals-auto-accounting__info-value">
            {formatDateTime(document.received_at)}
          </span>
        </div>
      </div>
    </Card>
  );
};

const OCRResultCard: React.FC<{ ocr: OCRResult }> = ({ ocr }) => {
  const [showRawText, setShowRawText] = useState(false);

  return (
    <Card
      title="Extraction OCR"
      icon={<Eye size={18} />}
      actions={
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setShowRawText(!showRawText)}
        >
          {showRawText ? 'Champs extraits' : 'Texte brut'}
        </Button>
      }
    >
      <div className="azals-auto-accounting__ocr-result">
        <div className="azals-auto-accounting__ocr-meta">
          <span>Moteur: {ocr.ocr_engine}</span>
          <span>Confiance: {(ocr.confidence_score * 100).toFixed(0)}%</span>
          <span>Temps: {ocr.processing_time_ms}ms</span>
        </div>

        {showRawText ? (
          <div className="azals-auto-accounting__ocr-raw">
            <pre>{ocr.raw_text}</pre>
          </div>
        ) : (
          <div className="azals-auto-accounting__ocr-fields">
            {ocr.extracted_fields.map((field, index) => (
              <div key={index} className="azals-auto-accounting__ocr-field">
                <span className="azals-auto-accounting__ocr-field-name">
                  {field.field_name}
                </span>
                <span className="azals-auto-accounting__ocr-field-value">
                  {field.value || '-'}
                </span>
                <span
                  className={`azals-auto-accounting__ocr-field-confidence ${
                    field.confidence > 0.9
                      ? 'azals-text--success'
                      : field.confidence > 0.7
                      ? 'azals-text--warning'
                      : 'azals-text--danger'
                  }`}
                >
                  {(field.confidence * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
};

const AIClassificationCard: React.FC<{ classification: AIClassification }> = ({
  classification,
}) => {
  return (
    <Card title="Classification IA" icon={<Brain size={18} />}>
      <div className="azals-auto-accounting__ai-classification">
        <div className="azals-auto-accounting__ai-header">
          <StatusBadge
            variant={getConfidenceVariant(classification.confidence_level)}
            status={`Confiance: ${(classification.confidence_score * 100).toFixed(0)}%`}
          />
        </div>

        <div className="azals-auto-accounting__ai-suggestions">
          {classification.suggested_vendor_name && (
            <div className="azals-auto-accounting__ai-suggestion">
              <Building size={14} />
              <span>Fournisseur:</span>
              <strong>{classification.suggested_vendor_name}</strong>
            </div>
          )}

          {classification.suggested_account_code && (
            <div className="azals-auto-accounting__ai-suggestion">
              <Calculator size={14} />
              <span>Compte:</span>
              <strong>
                {classification.suggested_account_code}
                {classification.suggested_account_name &&
                  ` - ${classification.suggested_account_name}`}
              </strong>
            </div>
          )}

          {classification.suggested_journal_code && (
            <div className="azals-auto-accounting__ai-suggestion">
              <FileText size={14} />
              <span>Journal:</span>
              <strong>{classification.suggested_journal_code}</strong>
            </div>
          )}

          {classification.suggested_tax_code && (
            <div className="azals-auto-accounting__ai-suggestion">
              <Receipt size={14} />
              <span>TVA:</span>
              <strong>{classification.suggested_tax_code}</strong>
            </div>
          )}
        </div>

        {classification.reasoning && (
          <div className="azals-auto-accounting__ai-reasoning">
            <span className="azals-auto-accounting__ai-reasoning-label">
              Raisonnement IA:
            </span>
            <p>{classification.reasoning}</p>
          </div>
        )}

        <div className="azals-auto-accounting__ai-footer">
          <span>Traité le {formatDateTime(classification.processed_at)}</span>
        </div>
      </div>
    </Card>
  );
};

const AutoEntryCard: React.FC<{ entry: AutoEntry }> = ({ entry }) => {
  return (
    <Card title="Écriture comptable" icon={<Calculator size={18} />}>
      <div className="azals-auto-accounting__entry">
        <div className="azals-auto-accounting__entry-header">
          <StatusBadge
            variant={
              entry.status === 'VALIDATED'
                ? 'success'
                : entry.status === 'PENDING'
                ? 'warning'
                : 'default'
            }
            status={entry.status === 'VALIDATED' ? 'Validée' : 'En attente'}
          />
          <span>Journal: {entry.journal_code}</span>
          <span>Date: {formatDate(entry.entry_date)}</span>
        </div>

        <div className="azals-auto-accounting__entry-description">
          {entry.description}
        </div>

        <table className="azals-auto-accounting__entry-lines">
          <thead>
            <tr>
              <th>Compte</th>
              <th>Libellé</th>
              <th className="azals-text--right">Débit</th>
              <th className="azals-text--right">Crédit</th>
            </tr>
          </thead>
          <tbody>
            {entry.lines.map((line, index) => (
              <tr key={index}>
                <td>
                  {line.account_code}
                  <span className="azals-text--muted">
                    {' '}
                    - {line.account_name}
                  </span>
                </td>
                <td>{line.label}</td>
                <td className="azals-text--right">
                  {line.debit > 0 ? formatCurrency(line.debit) : ''}
                </td>
                <td className="azals-text--right">
                  {line.credit > 0 ? formatCurrency(line.credit) : ''}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan={2}>
                <strong>Total</strong>
              </td>
              <td className="azals-text--right">
                <strong>{formatCurrency(entry.total_debit)}</strong>
              </td>
              <td className="azals-text--right">
                <strong>{formatCurrency(entry.total_credit)}</strong>
              </td>
            </tr>
          </tfoot>
        </table>

        {entry.validated_at && (
          <div className="azals-auto-accounting__entry-footer">
            Validée le {formatDateTime(entry.validated_at)}
            {entry.validated_by && ` par ${entry.validated_by}`}
          </div>
        )}
      </div>
    </Card>
  );
};

const HistoryCard: React.FC<{ history: DocumentHistory[] }> = ({ history }) => {
  if (history.length === 0) return null;

  const getActionLabel = (action: string): string => {
    const labels: Record<string, string> = {
      CREATED: 'Document créé',
      OCR_PROCESSED: 'OCR traité',
      AI_CLASSIFIED: 'Classification IA',
      AUTO_VALIDATED: 'Auto-validé',
      MANUAL_VALIDATED: 'Validé manuellement',
      REJECTED: 'Rejeté',
      CONTEXT_UPDATED: 'Contexte mis à jour',
      RECONCILED: 'Rapproché',
    };
    return labels[action] || action;
  };

  return (
    <Card title="Historique" icon={<History size={18} />}>
      <div className="azals-auto-accounting__history">
        {history.map((item) => (
          <div key={item.id} className="azals-auto-accounting__history-item">
            <div className="azals-auto-accounting__history-dot" />
            <div className="azals-auto-accounting__history-content">
              <div className="azals-auto-accounting__history-header">
                <span className="azals-auto-accounting__history-action">
                  {getActionLabel(item.action)}
                </span>
                <span className="azals-auto-accounting__history-date">
                  {formatDateTime(item.created_at)}
                </span>
              </div>
              <span className="azals-auto-accounting__history-actor">
                Par {item.actor_name}
              </span>
              {item.comment && (
                <p className="azals-auto-accounting__history-comment">
                  {item.comment}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};

// ============================================================
// MODALS
// ============================================================

const ContextModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  document: DocumentDetail;
  onSave: (notes: string, tags: string[]) => void;
  isLoading: boolean;
}> = ({ isOpen, onClose, document, onSave, isLoading }) => {
  const [notes, setNotes] = useState(document.notes || '');
  const [tagsInput, setTagsInput] = useState(document.tags.join(', '));

  const handleSave = () => {
    const tags = tagsInput
      .split(',')
      .map((t) => t.trim())
      .filter((t) => t.length > 0);
    onSave(notes, tags);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Ajouter du contexte">
      <div className="azals-auto-accounting__context-form">
        <div className="azals-form-group">
          <label className="azals-form-label">Notes / Commentaire</label>
          <TextArea
            value={notes}
            onChange={(value) => setNotes(value)}
            placeholder="Ajouter des informations utiles..."
            rows={4}
          />
        </div>

        <div className="azals-form-group">
          <label className="azals-form-label">Tags (séparés par virgule)</label>
          <Input
            value={tagsInput}
            onChange={(value) => setTagsInput(value)}
            placeholder="projet-x, urgent, à vérifier..."
          />
        </div>

        <div className="azals-modal__actions">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button onClick={handleSave} disabled={isLoading}>
            {isLoading ? 'Enregistrement...' : 'Enregistrer'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

const ValidationModal: React.FC<{
  isOpen: boolean;
  onClose: () => void;
  action: 'validate' | 'reject';
  onConfirm: (comment: string) => void;
  isLoading: boolean;
}> = ({ isOpen, onClose, action, onConfirm, isLoading }) => {
  const [comment, setComment] = useState('');

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={action === 'validate' ? 'Valider le document' : 'Rejeter le document'}
    >
      <div className="azals-auto-accounting__validation-form">
        <div className="azals-form-group">
          <label className="azals-form-label">
            {action === 'validate' ? 'Commentaire (optionnel)' : 'Motif du rejet'}
          </label>
          <TextArea
            value={comment}
            onChange={(value) => setComment(value)}
            placeholder={
              action === 'validate'
                ? 'Commentaire...'
                : 'Expliquez pourquoi ce document est rejeté...'
            }
            rows={3}
          />
        </div>

        <div className="azals-modal__actions">
          <Button variant="ghost" onClick={onClose}>
            Annuler
          </Button>
          <Button
            variant={action === 'validate' ? 'primary' : 'danger'}
            onClick={() => onConfirm(comment)}
            disabled={isLoading || (action === 'reject' && !comment.trim())}
          >
            {isLoading
              ? 'En cours...'
              : action === 'validate'
              ? 'Valider'
              : 'Rejeter'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};

// ============================================================
// MAIN COMPONENT
// ============================================================

export const DocumentDetail: React.FC = () => {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [showContextModal, setShowContextModal] = useState(false);
  const [validationAction, setValidationAction] = useState<
    'validate' | 'reject' | null
  >(null);

  const { data: document, isLoading } = useDocumentDetail(documentId || '');
  const validateDocument = useValidateDocument();
  const rejectDocument = useRejectDocument();
  const updateContext = useUpdateDocumentContext();

  const isExpert = user?.roles?.includes('expert_comptable') || false;
  const isAssistante = user?.roles?.includes('assistante') || false;
  const canValidate =
    isExpert &&
    document &&
    ['ANALYZED', 'PENDING_VALIDATION'].includes(document.status);

  const handleValidation = async (comment: string) => {
    if (!documentId || !validationAction) return;

    try {
      if (validationAction === 'validate') {
        await validateDocument.mutateAsync({ documentId, comment });
      } else {
        await rejectDocument.mutateAsync({ documentId, reason: comment });
      }
      setValidationAction(null);
    } catch (error) {
      console.error('Validation failed:', error);
    }
  };

  const handleContextSave = async (notes: string, tags: string[]) => {
    if (!documentId) return;

    try {
      await updateContext.mutateAsync({ documentId, notes, tags });
      setShowContextModal(false);
    } catch (error) {
      console.error('Context update failed:', error);
    }
  };

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="azals-loading">
          <div className="azals-spinner" />
          <p>Chargement du document...</p>
        </div>
      </PageWrapper>
    );
  }

  if (!document) {
    return (
      <PageWrapper title="Document non trouvé">
        <Card>
          <div className="azals-empty-state">
            <AlertTriangle size={48} />
            <p>Ce document n'existe pas ou vous n'y avez pas accès.</p>
            <Button onClick={() => navigate(-1)}>Retour</Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  return (
    <PageWrapper
      title={document.reference || document.original_filename}
      subtitle={getTypeLabel(document.document_type)}
      backAction={{
        label: 'Retour',
        onClick: () => navigate(-1),
      }}
      actions={
        <ButtonGroup>
          {(isAssistante || isExpert) && (
            <Button
              variant="ghost"
              leftIcon={<MessageSquare size={16} />}
              onClick={() => setShowContextModal(true)}
            >
              Ajouter contexte
            </Button>
          )}
          {canValidate && (
            <>
              <Button
                variant="danger"
                leftIcon={<XCircle size={16} />}
                onClick={() => setValidationAction('reject')}
              >
                Rejeter
              </Button>
              <Button
                variant="success"
                leftIcon={<CheckCircle size={16} />}
                onClick={() => setValidationAction('validate')}
              >
                Valider
              </Button>
            </>
          )}
        </ButtonGroup>
      }
    >
      <div className="azals-auto-accounting__document-detail">
        <Grid columns={2}>
          {/* Colonne gauche - Prévisualisation */}
          <div className="azals-auto-accounting__document-preview-col">
            <DocumentPreview document={document} />
          </div>

          {/* Colonne droite - Informations */}
          <div className="azals-auto-accounting__document-info-col">
            <DocumentInfo document={document} />

            {document.ocr_result && (
              <OCRResultCard ocr={document.ocr_result} />
            )}

            {document.ai_classification && (
              <AIClassificationCard
                classification={document.ai_classification}
              />
            )}

            {document.auto_entry && (
              <AutoEntryCard entry={document.auto_entry} />
            )}

            <HistoryCard history={document.history} />
          </div>
        </Grid>
      </div>

      {/* Modal contexte */}
      {showContextModal && (
        <ContextModal
          isOpen={true}
          onClose={() => setShowContextModal(false)}
          document={document}
          onSave={handleContextSave}
          isLoading={updateContext.isPending}
        />
      )}

      {/* Modal validation */}
      {validationAction && (
        <ValidationModal
          isOpen={true}
          onClose={() => setValidationAction(null)}
          action={validationAction}
          onConfirm={handleValidation}
          isLoading={
            validateDocument.isPending || rejectDocument.isPending
          }
        />
      )}
    </PageWrapper>
  );
};

export default DocumentDetail;
