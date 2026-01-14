/**
 * AZALSCORE - Store centralisé des documents
 *
 * Gestion d'état Zustand pour la vue unique /documents
 *
 * Principes :
 * - Le type de document est un état, pas une route
 * - Le mode (saisie/liste) est un état
 * - Les filtres sont partagés entre les types
 * - Le document en cours est conservé pendant la navigation
 */

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

// ============================================================
// TYPES
// ============================================================

/**
 * Types de documents supportés
 * VENTES : QUOTE, INVOICE, CREDIT_NOTE, PROFORMA, DELIVERY
 * ACHATS : PURCHASE_ORDER, PURCHASE_INVOICE
 */
export type DocumentType =
  | 'QUOTE'           // Devis client
  | 'INVOICE'         // Facture client
  | 'ORDER'           // Commande client
  | 'CREDIT_NOTE'     // Avoir client
  | 'PROFORMA'        // Proforma
  | 'DELIVERY'        // Bon de livraison
  | 'PURCHASE_ORDER'  // Commande fournisseur
  | 'PURCHASE_INVOICE'; // Facture fournisseur

/**
 * Catégories de documents
 */
export type DocumentCategory = 'SALES' | 'PURCHASES';

/**
 * Statuts de documents
 */
export type DocumentStatus =
  | 'DRAFT'
  | 'PENDING'
  | 'VALIDATED'
  | 'SENT'
  | 'ACCEPTED'
  | 'REJECTED'
  | 'DELIVERED'
  | 'INVOICED'
  | 'PAID'
  | 'PARTIAL'
  | 'CANCELLED'
  | 'CONFIRMED'
  | 'RECEIVED';

/**
 * Modes de la vue
 */
export type ViewMode = 'entry' | 'list';

/**
 * Ligne de document (format unifié)
 */
export interface DocumentLine {
  id?: string;
  tempId?: string;
  lineNumber: number;
  productId?: string;
  productCode?: string;
  description: string;
  quantity: number;
  unit?: string;
  unitPrice: number;
  discountPercent: number;
  taxRate: number;
  // Calculés
  subtotal?: number;
  taxAmount?: number;
  total?: number;
  notes?: string;
}

/**
 * Document (format unifié)
 */
export interface Document {
  id?: string;
  number?: string;
  type: DocumentType;
  status: DocumentStatus;
  // Partenaire (client ou fournisseur)
  partnerId: string;
  partnerName?: string;
  partnerCode?: string;
  // Dates
  date: string;
  dueDate?: string;
  validityDate?: string;
  expectedDate?: string;
  // Références
  reference?: string;
  parentId?: string;
  parentNumber?: string;
  // Montants
  subtotal: number;
  discountPercent: number;
  discountAmount: number;
  taxAmount: number;
  total: number;
  currency: string;
  // Notes
  notes?: string;
  internalNotes?: string;
  // Lignes
  lines: DocumentLine[];
  // Méta
  validatedAt?: string;
  validatedBy?: string;
  createdAt?: string;
  createdBy?: string;
  updatedAt?: string;
}

/**
 * Filtres de liste
 */
export interface DocumentFilters {
  search?: string;
  status?: DocumentStatus;
  partnerId?: string;
  dateFrom?: string;
  dateTo?: string;
}

/**
 * État de pagination
 */
export interface PaginationState {
  page: number;
  pageSize: number;
  total: number;
}

// ============================================================
// CONFIGURATION DES TYPES
// ============================================================

/**
 * Configuration par type de document
 */
export interface DocumentTypeConfig {
  type: DocumentType;
  category: DocumentCategory;
  labelKey: string;
  labelPluralKey: string;
  prefix: string;
  allowedStatuses: DocumentStatus[];
  partnerType: 'customer' | 'supplier';
  hasValidityDate?: boolean;
  hasDueDate?: boolean;
  hasExpectedDate?: boolean;
  canConvertTo?: DocumentType[];
  capability: string;
}

export const DOCUMENT_TYPE_CONFIG: Record<DocumentType, DocumentTypeConfig> = {
  // Ventes
  QUOTE: {
    type: 'QUOTE',
    category: 'SALES',
    labelKey: 'documents.types.QUOTE',
    labelPluralKey: 'documents.typesPlural.QUOTE',
    prefix: 'DEV',
    allowedStatuses: ['DRAFT', 'VALIDATED', 'ACCEPTED', 'REJECTED', 'INVOICED', 'CANCELLED'],
    partnerType: 'customer',
    hasValidityDate: true,
    canConvertTo: ['INVOICE', 'ORDER'],
    capability: 'invoicing',
  },
  INVOICE: {
    type: 'INVOICE',
    category: 'SALES',
    labelKey: 'documents.types.INVOICE',
    labelPluralKey: 'documents.typesPlural.INVOICE',
    prefix: 'FAC',
    allowedStatuses: ['DRAFT', 'VALIDATED', 'SENT', 'PAID', 'PARTIAL', 'CANCELLED'],
    partnerType: 'customer',
    hasDueDate: true,
    capability: 'invoicing',
  },
  ORDER: {
    type: 'ORDER',
    category: 'SALES',
    labelKey: 'documents.types.ORDER',
    labelPluralKey: 'documents.typesPlural.ORDER',
    prefix: 'CMD',
    allowedStatuses: ['DRAFT', 'VALIDATED', 'DELIVERED', 'INVOICED', 'CANCELLED'],
    partnerType: 'customer',
    hasExpectedDate: true,
    canConvertTo: ['INVOICE', 'DELIVERY'],
    capability: 'invoicing',
  },
  CREDIT_NOTE: {
    type: 'CREDIT_NOTE',
    category: 'SALES',
    labelKey: 'documents.types.CREDIT_NOTE',
    labelPluralKey: 'documents.typesPlural.CREDIT_NOTE',
    prefix: 'AVO',
    allowedStatuses: ['DRAFT', 'VALIDATED', 'CANCELLED'],
    partnerType: 'customer',
    capability: 'invoicing',
  },
  PROFORMA: {
    type: 'PROFORMA',
    category: 'SALES',
    labelKey: 'documents.types.PROFORMA',
    labelPluralKey: 'documents.typesPlural.PROFORMA',
    prefix: 'PRO',
    allowedStatuses: ['DRAFT', 'VALIDATED', 'SENT', 'CANCELLED'],
    partnerType: 'customer',
    hasValidityDate: true,
    canConvertTo: ['INVOICE'],
    capability: 'invoicing',
  },
  DELIVERY: {
    type: 'DELIVERY',
    category: 'SALES',
    labelKey: 'documents.types.DELIVERY',
    labelPluralKey: 'documents.typesPlural.DELIVERY',
    prefix: 'BL',
    allowedStatuses: ['DRAFT', 'VALIDATED', 'DELIVERED', 'CANCELLED'],
    partnerType: 'customer',
    canConvertTo: ['INVOICE'],
    capability: 'invoicing',
  },
  // Achats
  PURCHASE_ORDER: {
    type: 'PURCHASE_ORDER',
    category: 'PURCHASES',
    labelKey: 'documents.types.PURCHASE_ORDER',
    labelPluralKey: 'documents.typesPlural.PURCHASE_ORDER',
    prefix: 'CDF',
    allowedStatuses: ['DRAFT', 'SENT', 'CONFIRMED', 'PARTIAL', 'RECEIVED', 'INVOICED', 'CANCELLED'],
    partnerType: 'supplier',
    hasExpectedDate: true,
    canConvertTo: ['PURCHASE_INVOICE'],
    capability: 'purchases',
  },
  PURCHASE_INVOICE: {
    type: 'PURCHASE_INVOICE',
    category: 'PURCHASES',
    labelKey: 'documents.types.PURCHASE_INVOICE',
    labelPluralKey: 'documents.typesPlural.PURCHASE_INVOICE',
    prefix: 'FAF',
    allowedStatuses: ['DRAFT', 'VALIDATED', 'PAID', 'PARTIAL', 'CANCELLED'],
    partnerType: 'supplier',
    hasDueDate: true,
    capability: 'purchases',
  },
};

// ============================================================
// HELPERS
// ============================================================

/**
 * Obtenir la catégorie d'un type de document
 */
export const getDocumentCategory = (type: DocumentType): DocumentCategory => {
  return DOCUMENT_TYPE_CONFIG[type].category;
};

/**
 * Vérifier si un document est modifiable
 */
export const isDocumentEditable = (status: DocumentStatus): boolean => {
  return status === 'DRAFT';
};

/**
 * Créer un document vide
 */
export const createEmptyDocument = (type: DocumentType): Document => {
  return {
    type,
    status: 'DRAFT',
    partnerId: '',
    date: new Date().toISOString().split('T')[0],
    subtotal: 0,
    discountPercent: 0,
    discountAmount: 0,
    taxAmount: 0,
    total: 0,
    currency: 'EUR',
    lines: [],
  };
};

/**
 * Créer une ligne vide
 */
export const createEmptyLine = (): DocumentLine => {
  return {
    tempId: `temp-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    lineNumber: 0,
    description: '',
    quantity: 1,
    unit: 'unité',
    unitPrice: 0,
    discountPercent: 0,
    taxRate: 20,
  };
};

/**
 * Calculer les totaux d'une ligne
 */
export const calculateLineTotal = (line: DocumentLine): {
  subtotal: number;
  taxAmount: number;
  total: number;
} => {
  const baseAmount = line.quantity * line.unitPrice;
  const discountAmount = baseAmount * (line.discountPercent / 100);
  const subtotal = baseAmount - discountAmount;
  const taxAmount = subtotal * (line.taxRate / 100);
  const total = subtotal + taxAmount;

  return { subtotal, taxAmount, total };
};

/**
 * Calculer les totaux d'un document
 */
export const calculateDocumentTotals = (lines: DocumentLine[]): {
  subtotal: number;
  taxAmount: number;
  total: number;
} => {
  return lines.reduce(
    (acc, line) => {
      const lineTotals = calculateLineTotal(line);
      return {
        subtotal: acc.subtotal + lineTotals.subtotal,
        taxAmount: acc.taxAmount + lineTotals.taxAmount,
        total: acc.total + lineTotals.total,
      };
    },
    { subtotal: 0, taxAmount: 0, total: 0 }
  );
};

// ============================================================
// STORE
// ============================================================

interface DocumentsState {
  // Vue
  mode: ViewMode;
  documentType: DocumentType;

  // Document en cours
  currentDocument: Document | null;
  isDirty: boolean;

  // Liste
  filters: DocumentFilters;
  pagination: PaginationState;

  // Actions - Vue
  setMode: (mode: ViewMode) => void;
  setDocumentType: (type: DocumentType) => void;

  // Actions - Document
  setCurrentDocument: (doc: Document | null) => void;
  updateCurrentDocument: (updates: Partial<Document>) => void;
  resetCurrentDocument: () => void;
  newDocument: (type?: DocumentType) => void;

  // Actions - Lignes
  addLine: () => void;
  updateLine: (index: number, updates: Partial<DocumentLine>) => void;
  removeLine: (index: number) => void;
  reorderLines: (fromIndex: number, toIndex: number) => void;

  // Actions - Filtres
  setFilters: (filters: Partial<DocumentFilters>) => void;
  resetFilters: () => void;

  // Actions - Pagination
  setPage: (page: number) => void;
  setPageSize: (size: number) => void;
  setTotal: (total: number) => void;

  // Computed
  getTypeConfig: () => DocumentTypeConfig;
  isEditable: () => boolean;
}

export const useDocumentsStore = create<DocumentsState>()(
  persist(
    (set, get) => ({
      // État initial
      mode: 'entry',
      documentType: 'QUOTE',
      currentDocument: null,
      isDirty: false,
      filters: {},
      pagination: {
        page: 1,
        pageSize: 25,
        total: 0,
      },

      // Actions - Vue
      setMode: (mode) => set({ mode }),

      setDocumentType: (type) => {
        const state = get();
        // Ne pas perdre le document si on est en mode saisie et que le document n'est pas sauvegardé
        if (state.mode === 'entry' && state.isDirty && state.currentDocument) {
          // Garder le document actuel, juste changer le type affiché
          set({ documentType: type });
        } else {
          // Réinitialiser pour le nouveau type
          set({
            documentType: type,
            currentDocument: createEmptyDocument(type),
            isDirty: false,
            filters: {},
            pagination: { page: 1, pageSize: 25, total: 0 },
          });
        }
      },

      // Actions - Document
      setCurrentDocument: (doc) => set({
        currentDocument: doc,
        isDirty: false,
        documentType: doc?.type || get().documentType,
      }),

      updateCurrentDocument: (updates) => {
        const current = get().currentDocument;
        if (!current) return;

        set({
          currentDocument: { ...current, ...updates },
          isDirty: true,
        });
      },

      resetCurrentDocument: () => {
        const type = get().documentType;
        set({
          currentDocument: createEmptyDocument(type),
          isDirty: false,
        });
      },

      newDocument: (type) => {
        const docType = type || get().documentType;
        set({
          documentType: docType,
          currentDocument: createEmptyDocument(docType),
          isDirty: false,
          mode: 'entry',
        });
      },

      // Actions - Lignes
      addLine: () => {
        const current = get().currentDocument;
        if (!current) return;

        const newLine = createEmptyLine();
        newLine.lineNumber = current.lines.length + 1;

        const lines = [...current.lines, newLine];
        const totals = calculateDocumentTotals(lines);

        set({
          currentDocument: {
            ...current,
            lines,
            ...totals,
          },
          isDirty: true,
        });
      },

      updateLine: (index, updates) => {
        const current = get().currentDocument;
        if (!current) return;

        const lines = [...current.lines];
        lines[index] = { ...lines[index], ...updates };

        const totals = calculateDocumentTotals(lines);

        set({
          currentDocument: {
            ...current,
            lines,
            ...totals,
          },
          isDirty: true,
        });
      },

      removeLine: (index) => {
        const current = get().currentDocument;
        if (!current) return;

        const lines = current.lines
          .filter((_, i) => i !== index)
          .map((line, i) => ({ ...line, lineNumber: i + 1 }));

        const totals = calculateDocumentTotals(lines);

        set({
          currentDocument: {
            ...current,
            lines,
            ...totals,
          },
          isDirty: true,
        });
      },

      reorderLines: (fromIndex, toIndex) => {
        const current = get().currentDocument;
        if (!current) return;

        const lines = [...current.lines];
        const [removed] = lines.splice(fromIndex, 1);
        lines.splice(toIndex, 0, removed);

        // Renuméroter
        const reorderedLines = lines.map((line, i) => ({
          ...line,
          lineNumber: i + 1,
        }));

        set({
          currentDocument: {
            ...current,
            lines: reorderedLines,
          },
          isDirty: true,
        });
      },

      // Actions - Filtres
      setFilters: (filters) => set((state) => ({
        filters: { ...state.filters, ...filters },
        pagination: { ...state.pagination, page: 1 }, // Reset page on filter change
      })),

      resetFilters: () => set({
        filters: {},
        pagination: { page: 1, pageSize: get().pagination.pageSize, total: 0 },
      }),

      // Actions - Pagination
      setPage: (page) => set((state) => ({
        pagination: { ...state.pagination, page },
      })),

      setPageSize: (pageSize) => set((state) => ({
        pagination: { ...state.pagination, pageSize, page: 1 },
      })),

      setTotal: (total) => set((state) => ({
        pagination: { ...state.pagination, total },
      })),

      // Computed
      getTypeConfig: () => DOCUMENT_TYPE_CONFIG[get().documentType],

      isEditable: () => {
        const doc = get().currentDocument;
        return !doc || isDocumentEditable(doc.status);
      },
    }),
    {
      name: 'azals-documents-store',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        documentType: state.documentType,
        mode: state.mode,
        filters: state.filters,
        pagination: { page: 1, pageSize: state.pagination.pageSize, total: 0 },
      }),
    }
  )
);

// ============================================================
// SELECTORS (pour optimiser les re-renders)
// ============================================================

export const selectMode = (state: DocumentsState) => state.mode;
export const selectDocumentType = (state: DocumentsState) => state.documentType;
export const selectCurrentDocument = (state: DocumentsState) => state.currentDocument;
export const selectIsDirty = (state: DocumentsState) => state.isDirty;
export const selectFilters = (state: DocumentsState) => state.filters;
export const selectPagination = (state: DocumentsState) => state.pagination;

export default useDocumentsStore;
