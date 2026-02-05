/**
 * AZALSCORE - Shared Documents Components
 * ========================================
 * Composants partagés pour les onglets documents.
 *
 * Usage:
 * import { DocumentCard, DocumentList, LinkedDocumentItem } from '@ui/components/shared-documents';
 */

export {
  DocumentCard,
  type DocumentData,
  type DocumentCardProps,
  type DocumentType,
  type DocumentStatus,
} from './DocumentCard';

export {
  DocumentList,
  type DocumentListProps,
  type ViewMode,
} from './DocumentList';

export {
  LinkedDocumentItem,
  LinkedDocumentList,
  type LinkedDocumentData,
  type LinkedDocumentItemProps,
  type LinkedDocumentListProps,
  type LinkType,
} from './LinkedDocumentItem';

export {
  DocumentUploadWidget,
  type DocumentUploadWidgetProps,
  type UploadFile,
  type UploadStatus,
} from './DocumentUploadWidget';
