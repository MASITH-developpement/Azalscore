/**
 * AZALSCORE Module - HR Vault - Document Detail View
 * Vue detaillee d'un document
 */

import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Download, Lock, PenTool, CheckCircle, XCircle
} from 'lucide-react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { formatDate, formatDateTime } from '@/utils/formatters';
import {
  useDocument,
  useDocumentVersions,
  useAccessLogs,
} from '../hooks';
import { hrVaultApi } from '../api';
import {
  DOCUMENT_TYPE_CONFIG,
  DOCUMENT_STATUS_CONFIG,
  SIGNATURE_STATUS_CONFIG,
  formatFileSize,
  needsSignature,
} from '../types';
import { Badge } from './LocalComponents';

export const DocumentDetailView: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: document, isLoading, error } = useDocument(id || '');
  const { data: versions = [] } = useDocumentVersions(id || '');
  const { data: accessLogs } = useAccessLogs(id);

  if (isLoading) {
    return (
      <PageWrapper title="Chargement...">
        <div className="flex items-center justify-center h-64">
          <div className="azals-spinner" />
        </div>
      </PageWrapper>
    );
  }

  if (error || !document) {
    return (
      <PageWrapper title="Erreur">
        <Card>
          <div className="text-center py-8">
            <p className="text-red-600">Document non trouve</p>
            <Button variant="secondary" onClick={() => navigate('/hr-vault')} className="mt-4">
              <ArrowLeft size={16} className="mr-2" />
              Retour
            </Button>
          </div>
        </Card>
      </PageWrapper>
    );
  }

  const handleDownload = async () => {
    try {
      const response = await hrVaultApi.downloadDocument(document.id);
      const blob = response.data;
      const url = window.URL.createObjectURL(blob);
      const a = window.document.createElement('a');
      a.href = url;
      a.download = document.file_name;
      window.document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      window.document.body.removeChild(a);
    } catch (err) {
      console.error('Erreur telechargement:', err);
    }
  };

  return (
    <PageWrapper
      title={document.title}
      subtitle={document.file_name}
    >
      <div className="mb-4 flex gap-2">
        <Button variant="secondary" onClick={() => navigate('/hr-vault')}>
          <ArrowLeft size={16} className="mr-2" />
          Retour
        </Button>
        <Button onClick={handleDownload}>
          <Download size={16} className="mr-2" />
          Telecharger
        </Button>
      </div>

      <Grid cols={3}>
        {/* Informations */}
        <Card title="Informations" className="col-span-2">
          <Grid cols={2} gap="md">
            <div className="azals-field">
              <span className="azals-field__label">Type</span>
              <div className="azals-field__value">
                <Badge color={DOCUMENT_TYPE_CONFIG[document.document_type]?.color || 'gray'}>
                  {DOCUMENT_TYPE_CONFIG[document.document_type]?.label || document.document_type}
                </Badge>
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Statut</span>
              <div className="azals-field__value">
                <Badge color={DOCUMENT_STATUS_CONFIG[document.status]?.color || 'gray'}>
                  {DOCUMENT_STATUS_CONFIG[document.status]?.label || document.status}
                </Badge>
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Taille</span>
              <div className="azals-field__value">{formatFileSize(document.file_size)}</div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Chiffrement</span>
              <div className="azals-field__value">
                {document.is_encrypted ? (
                  <span className="text-green-600 flex items-center gap-1">
                    <Lock size={14} /> Chiffre
                  </span>
                ) : (
                  <span className="text-red-600">Non chiffre</span>
                )}
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Date du document</span>
              <div className="azals-field__value">
                {document.document_date ? formatDate(document.document_date) : '-'}
              </div>
            </div>
            <div className="azals-field">
              <span className="azals-field__label">Conservation jusqu au</span>
              <div className="azals-field__value">
                {document.retention_end_date ? formatDate(document.retention_end_date) : '-'}
              </div>
            </div>
            {document.description && (
              <div className="azals-field col-span-2">
                <span className="azals-field__label">Description</span>
                <div className="azals-field__value">{document.description}</div>
              </div>
            )}
          </Grid>
        </Card>

        {/* Signature */}
        <Card title="Signature">
          <div className="space-y-4">
            <div className="azals-field">
              <span className="azals-field__label">Statut</span>
              <div className="azals-field__value">
                <Badge color={SIGNATURE_STATUS_CONFIG[document.signature_status]?.color || 'gray'}>
                  {SIGNATURE_STATUS_CONFIG[document.signature_status]?.label}
                </Badge>
              </div>
            </div>
            {document.signed_at && (
              <div className="azals-field">
                <span className="azals-field__label">Signe le</span>
                <div className="azals-field__value">{formatDateTime(document.signed_at)}</div>
              </div>
            )}
            {needsSignature(document) && (
              <Button className="w-full">
                <PenTool size={16} className="mr-2" />
                Demander signature
              </Button>
            )}
          </div>
        </Card>
      </Grid>

      {/* Versions */}
      <Card title="Versions" className="mt-4">
        {versions.length === 0 ? (
          <p className="text-gray-500">Aucune version</p>
        ) : (
          <div className="space-y-2">
            {versions.map((version) => (
              <div key={version.id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <div className="flex items-center gap-4">
                  <span className="font-medium">v{version.version_number}</span>
                  <span>{version.file_name}</span>
                  <span className="text-sm text-gray-500">{formatFileSize(version.file_size)}</span>
                </div>
                <span className="text-sm text-gray-500">{formatDateTime(version.created_at)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>

      {/* Historique des acces */}
      <Card title="Historique des acces" className="mt-4">
        {!accessLogs?.items?.length ? (
          <p className="text-gray-500">Aucun acces enregistre</p>
        ) : (
          <div className="space-y-2">
            {accessLogs.items.slice(0, 10).map((log) => (
              <div key={log.id} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <div className="flex items-center gap-2">
                  {log.success ? (
                    <CheckCircle size={14} className="text-green-500" />
                  ) : (
                    <XCircle size={14} className="text-red-500" />
                  )}
                  <span>{log.access_type}</span>
                  <span className="text-sm text-gray-500">par {log.accessed_by_name || log.accessed_by}</span>
                </div>
                <span className="text-sm text-gray-500">{formatDateTime(log.access_date)}</span>
              </div>
            ))}
          </div>
        )}
      </Card>
    </PageWrapper>
  );
};

export default DocumentDetailView;
