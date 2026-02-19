/**
 * AZALSCORE UI Engine - Table System
 * Tables génériques avec tri, filtres, pagination
 * Données fournies par API - AUCUNE logique métier
 */

import React, { useMemo, useState, useCallback, useRef, useEffect } from 'react';
import { clsx } from 'clsx';
import {
  ChevronUp,
  ChevronDown,
  ChevronsUpDown,
  ChevronLeft,
  ChevronRight,
  MoreVertical,
  Search,
  Filter,
  Download,
  RefreshCw,
  X,
  Check,
} from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import type { TableColumn, TableAction } from '@/types';
import { ErrorState, LoadingState } from '../components/StateViews';

// ============================================================
// COLUMN FILTER TYPES
// ============================================================

export interface ColumnFilterConfig {
  type: 'text' | 'select' | 'date' | 'number';
  options?: Array<{ value: string; label: string }>;
  placeholder?: string;
}

export type ColumnFilters = Record<string, string | string[]>;

// ============================================================
// TYPES
// ============================================================

interface DataTableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  keyField: keyof T;
  actions?: TableAction<T>[];
  pagination?: {
    page: number;
    pageSize: number;
    total: number;
    onPageChange: (page: number) => void;
    onPageSizeChange: (size: number) => void;
  };
  sorting?: {
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
    onSort: (column: string, order: 'asc' | 'desc') => void;
  };
  search?: {
    value: string;
    onChange: (value: string) => void;
    placeholder?: string;
  };
  // Column filters (manual configuration)
  columnFilters?: {
    filters: ColumnFilters;
    configs: Record<string, ColumnFilterConfig>;
    onFilterChange: (columnId: string, value: string | string[] | null) => void;
    onClearAllFilters?: () => void;
  };
  // Simple filterable mode - auto-enables text filtering on all columns
  filterable?: boolean;
  // Optional: specify which columns should have select filters with options
  filterOptions?: Record<string, Array<{ value: string; label: string }>>;
  isLoading?: boolean;
  error?: Error | null;
  onRetry?: () => void;
  emptyMessage?: string;
  onRefresh?: () => void;
  onExport?: () => void;
  selectable?: boolean;
  selectedRows?: T[];
  onSelectionChange?: (rows: T[]) => void;
  onRowClick?: (row: T) => void;
  className?: string;
}

// ============================================================
// COLUMN FILTER POPOVER
// ============================================================

interface ColumnFilterPopoverProps {
  columnId: string;
  config: ColumnFilterConfig;
  value: string | string[] | undefined;
  onApply: (value: string | string[] | null) => void;
  onClose: () => void;
}

const ColumnFilterPopover: React.FC<ColumnFilterPopoverProps> = ({
  columnId: _columnId,
  config,
  value,
  onApply,
  onClose,
}) => {
  const [localValue, setLocalValue] = useState<string | string[]>(
    value || (config.type === 'select' && config.options ? '' : '')
  );
  const popoverRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    // Focus input on open
    if (inputRef.current) {
      inputRef.current.focus();
    }

    // Close on click outside
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    // Close on Escape
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  const handleApply = () => {
    const trimmedValue = typeof localValue === 'string' ? localValue.trim() : localValue;
    onApply(trimmedValue || null);
    onClose();
  };

  const handleClear = () => {
    onApply(null);
    onClose();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleApply();
    }
  };

  return (
    <div ref={popoverRef} className="azals-column-filter-popover">
      <div className="azals-column-filter-popover__content">
        {config.type === 'select' && config.options ? (
          <select
            className="azals-select azals-select--sm"
            value={localValue as string}
            onChange={(e) => setLocalValue(e.target.value)}
          >
            <option value="">Tous</option>
            {config.options.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            ref={inputRef}
            type={config.type === 'number' ? 'number' : config.type === 'date' ? 'date' : 'text'}
            className="azals-input azals-input--sm"
            placeholder={config.placeholder || 'Filtrer...'}
            value={localValue as string}
            onChange={(e) => setLocalValue(e.target.value)}
            onKeyDown={handleKeyDown}
          />
        )}
      </div>
      <div className="azals-column-filter-popover__actions">
        <button
          className="azals-btn azals-btn--sm azals-btn--ghost"
          onClick={handleClear}
          title="Effacer"
        >
          <X size={14} />
        </button>
        <button
          className="azals-btn azals-btn--sm azals-btn--primary"
          onClick={handleApply}
          title="Appliquer"
        >
          <Check size={14} />
        </button>
      </div>
    </div>
  );
};

// ============================================================
// TABLE HEADER
// ============================================================

interface TableHeaderProps<T> {
  columns: TableColumn<T>[];
  hasActions: boolean;
  sorting?: DataTableProps<T>['sorting'];
  columnFilters?: DataTableProps<T>['columnFilters'];
  selectable?: boolean;
  allSelected: boolean;
  onSelectAll: () => void;
}

function TableHeader<T>({
  columns,
  hasActions,
  sorting,
  columnFilters,
  selectable,
  allSelected,
  onSelectAll,
}: TableHeaderProps<T>) {
  const [openFilterId, setOpenFilterId] = useState<string | null>(null);

  const handleSort = (column: TableColumn<T>) => {
    if (!column.sortable || !sorting) return;

    const columnId = String(column.id);
    const newOrder =
      sorting.sortBy === columnId && sorting.sortOrder === 'asc' ? 'desc' : 'asc';
    sorting.onSort(columnId, newOrder);
  };

  const handleFilterClick = (e: React.MouseEvent, columnId: string) => {
    e.stopPropagation();
    setOpenFilterId(openFilterId === columnId ? null : columnId);
  };

  const hasFilter = (columnId: string): boolean => {
    if (!columnFilters) return false;
    const value = columnFilters.filters[columnId];
    return value !== undefined && value !== null && value !== '';
  };

  return (
    <thead className="azals-table__head">
      <tr>
        {selectable && (
          <th className="azals-table__th azals-table__th--checkbox">
            <input
              type="checkbox"
              checked={allSelected}
              onChange={onSelectAll}
              className="azals-checkbox"
            />
          </th>
        )}
        {columns.map((column) => {
          const columnId = String(column.id);
          const filterConfig = columnFilters?.configs[columnId];
          const isFilterable = !!filterConfig;
          const isFiltered = hasFilter(columnId);

          return (
            <th
              key={columnId}
              className={clsx('azals-table__th', {
                'azals-table__th--sortable': column.sortable,
                'azals-table__th--filterable': isFilterable,
                'azals-table__th--filtered': isFiltered,
                [`azals-table__th--align-${column.align}`]: column.align,
              })}
              style={{ width: column.width }}
            >
              <div
                className="azals-table__th-content"
                onClick={() => column.sortable && handleSort(column)}
              >
                <span
                  className={clsx('azals-table__th-label', {
                    'azals-table__th-label--clickable': isFilterable,
                  })}
                  onClick={isFilterable ? (e) => handleFilterClick(e, columnId) : undefined}
                >
                  {column.header}
                  {isFilterable && (
                    <Filter
                      size={12}
                      className={clsx('azals-table__filter-icon', {
                        'azals-table__filter-icon--active': isFiltered,
                      })}
                    />
                  )}
                </span>
                {column.sortable && sorting && (
                  <span className="azals-table__sort-icon">
                    {sorting.sortBy === columnId ? (
                      sorting.sortOrder === 'asc' ? (
                        <ChevronUp size={14} />
                      ) : (
                        <ChevronDown size={14} />
                      )
                    ) : (
                      <ChevronsUpDown size={14} />
                    )}
                  </span>
                )}
              </div>
              {/* Filter popover */}
              {isFilterable && openFilterId === columnId && (
                <ColumnFilterPopover
                  columnId={columnId}
                  config={filterConfig}
                  value={columnFilters?.filters[columnId]}
                  onApply={(value) => columnFilters?.onFilterChange(columnId, value)}
                  onClose={() => setOpenFilterId(null)}
                />
              )}
            </th>
          );
        })}
        {hasActions && <th className="azals-table__th azals-table__th--actions">Actions</th>}
      </tr>
    </thead>
  );
}

// ============================================================
// TABLE ROW
// ============================================================

interface TableRowProps<T> {
  row: T;
  columns: TableColumn<T>[];
  actions?: TableAction<T>[];
  selectable?: boolean;
  isSelected: boolean;
  onSelect: () => void;
  onClick?: () => void;
}

function TableRow<T>({
  row,
  columns,
  actions,
  selectable,
  isSelected,
  onSelect,
  onClick,
}: TableRowProps<T>) {
  const [actionsOpen, setActionsOpen] = useState(false);

  const getCellValue = (column: TableColumn<T>): unknown => {
    if (!column.accessor) return undefined;
    if (typeof column.accessor === 'function') {
      return column.accessor(row);
    }
    return row[column.accessor];
  };

  const visibleActions = actions?.filter((action) => {
    if (action.isHidden?.(row)) return false;
    return true;
  });

  return (
    <tr
      className={clsx('azals-table__row', {
        'azals-table__row--selected': isSelected,
        'azals-table__row--clickable': !!onClick,
      })}
      onClick={onClick}
      role={onClick ? 'button' : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={onClick ? (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick(); } } : undefined}
    >
      {selectable && (
        <td className="azals-table__td azals-table__td--checkbox">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={onSelect}
            className="azals-checkbox"
          />
        </td>
      )}
      {columns.map((column) => {
        const value = getCellValue(column);
        return (
          <td
            key={String(column.id)}
            className={clsx('azals-table__td', {
              [`azals-table__td--align-${column.align}`]: column.align,
            })}
          >
            {column.render ? column.render(value, row) : String(value ?? '')}
          </td>
        );
      })}
      {visibleActions && visibleActions.length > 0 && (
        <td className="azals-table__td azals-table__td--actions">
          <div className="azals-table__actions-wrapper">
            <button
              className="azals-table__actions-trigger"
              onClick={() => setActionsOpen(!actionsOpen)}
              aria-label="Actions"
            >
              <MoreVertical size={16} />
            </button>
            {actionsOpen && (
              <>
                <div
                  className="azals-table__actions-overlay"
                  onClick={() => setActionsOpen(false)}
                />
                <div className="azals-table__actions-menu">
                  {visibleActions.map((action) => (
                    <CapabilityGuard key={action.id} capability={action.capability}>
                      <button
                        className={clsx('azals-table__action-item', {
                          'azals-table__action-item--danger': action.variant === 'danger',
                          'azals-table__action-item--warning': action.variant === 'warning',
                        })}
                        onClick={() => {
                          action.onClick(row);
                          setActionsOpen(false);
                        }}
                        disabled={action.isDisabled?.(row)}
                      >
                        {action.label}
                      </button>
                    </CapabilityGuard>
                  ))}
                </div>
              </>
            )}
          </div>
        </td>
      )}
    </tr>
  );
}

// ============================================================
// PAGINATION
// ============================================================

interface PaginationProps {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
  onPageSizeChange: (size: number) => void;
}

const Pagination: React.FC<PaginationProps> = ({
  page,
  pageSize,
  total,
  onPageChange,
  onPageSizeChange,
}) => {
  const totalPages = Math.ceil(total / pageSize);
  const startItem = (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, total);

  return (
    <div className="azals-table__pagination">
      <div className="azals-table__pagination-info">
        <span>
          {startItem}-{endItem} sur {total}
        </span>
        <select
          value={pageSize}
          onChange={(e) => onPageSizeChange(Number(e.target.value))}
          className="azals-select azals-select--sm"
        >
          <option value={10}>10 / page</option>
          <option value={25}>25 / page</option>
          <option value={50}>50 / page</option>
          <option value={100}>100 / page</option>
        </select>
      </div>

      <div className="azals-table__pagination-controls">
        <button
          className="azals-btn azals-btn--icon"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Page précédente"
        >
          <ChevronLeft size={16} />
        </button>
        <span className="azals-table__pagination-current">
          Page {page} / {totalPages}
        </span>
        <button
          className="azals-btn azals-btn--icon"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          aria-label="Page suivante"
        >
          <ChevronRight size={16} />
        </button>
      </div>
    </div>
  );
};

// ============================================================
// DATA TABLE
// ============================================================

export function DataTable<T>({
  columns,
  data,
  keyField,
  actions,
  pagination,
  sorting,
  search,
  columnFilters: externalColumnFilters,
  filterable = false,
  filterOptions = {},
  isLoading,
  error,
  onRetry,
  emptyMessage = 'Aucune donnée disponible',
  onRefresh,
  onExport,
  selectable,
  selectedRows = [],
  onSelectionChange,
  onRowClick,
  className,
}: DataTableProps<T>) {
  const hasActions = actions && actions.length > 0;

  // Internal filter state for filterable mode
  const [internalFilters, setInternalFilters] = useState<ColumnFilters>({});

  // Build filter configs for filterable mode
  const autoFilterConfigs = useMemo(() => {
    if (!filterable) return {};
    const configs: Record<string, ColumnFilterConfig> = {};
    columns.forEach((col) => {
      const colId = String(col.id);
      // Skip actions column
      if (colId === 'actions') return;
      // Use provided options if available
      if (filterOptions[colId]) {
        configs[colId] = {
          type: 'select',
          options: filterOptions[colId],
        };
      } else {
        configs[colId] = {
          type: 'text',
          placeholder: `Filtrer...`,
        };
      }
    });
    return configs;
  }, [columns, filterable, filterOptions]);

  // Handle internal filter change
  const handleInternalFilterChange = useCallback((columnId: string, value: string | string[] | null) => {
    setInternalFilters(prev => {
      if (value === null || value === '') {
        const { [columnId]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [columnId]: value };
    });
  }, []);

  // Clear all internal filters
  const handleClearAllInternalFilters = useCallback(() => {
    setInternalFilters({});
  }, []);

  // Use external filters if provided, otherwise use internal filters
  const columnFilters = externalColumnFilters || (filterable ? {
    filters: internalFilters,
    configs: autoFilterConfigs,
    onFilterChange: handleInternalFilterChange,
    onClearAllFilters: handleClearAllInternalFilters,
  } : undefined);

  // Filter data when using internal filters
  const filteredData = useMemo(() => {
    if (!filterable || Object.keys(internalFilters).length === 0) {
      return data;
    }
    return data.filter((row) => {
      return Object.entries(internalFilters).every(([columnId, filterValue]) => {
        if (!filterValue) return true;
        const col = columns.find((c) => String(c.id) === columnId);
        if (!col || !col.accessor) return true;

        const cellValue = typeof col.accessor === 'function'
          ? col.accessor(row)
          : row[col.accessor as keyof T];

        if (cellValue === null || cellValue === undefined) {
          return filterValue === '';
        }

        const config = autoFilterConfigs[columnId];
        if (config?.type === 'select') {
          return String(cellValue) === filterValue;
        }

        // Text filter - case insensitive contains
        return String(cellValue).toLowerCase().includes(String(filterValue).toLowerCase());
      });
    });
  }, [data, internalFilters, filterable, columns, autoFilterConfigs]);

  // Use filtered data when filterable
  const displayData = filterable && !externalColumnFilters ? filteredData : data;

  // Count active filters
  const activeFilterCount = useMemo(() => {
    if (!columnFilters) return 0;
    return Object.values(columnFilters.filters).filter(
      (v) => v !== undefined && v !== null && v !== ''
    ).length;
  }, [columnFilters]);

  const isRowSelected = useCallback(
    (row: T) => {
      return selectedRows.some(
        (selected) => selected[keyField] === row[keyField]
      );
    },
    [selectedRows, keyField]
  );

  const handleSelectRow = useCallback(
    (row: T) => {
      if (!onSelectionChange) return;

      const isSelected = isRowSelected(row);
      if (isSelected) {
        onSelectionChange(
          selectedRows.filter((r) => r[keyField] !== row[keyField])
        );
      } else {
        onSelectionChange([...selectedRows, row]);
      }
    },
    [selectedRows, onSelectionChange, keyField, isRowSelected]
  );

  const handleSelectAll = useCallback(() => {
    if (!onSelectionChange) return;

    if (selectedRows.length === displayData.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange([...displayData]);
    }
  }, [displayData, selectedRows, onSelectionChange]);

  const allSelected = displayData.length > 0 && selectedRows.length === displayData.length;

  return (
    <div className={clsx('azals-table-container', className)}>
      {/* Toolbar */}
      <div className="azals-table__toolbar">
        {search && (
          <div className="azals-table__search">
            <Search size={16} className="azals-table__search-icon" />
            <input
              type="text"
              value={search.value}
              onChange={(e) => search.onChange(e.target.value)}
              placeholder={search.placeholder || 'Rechercher...'}
              className="azals-input azals-table__search-input"
            />
          </div>
        )}

        <div className="azals-table__toolbar-actions">
          {onRefresh && (
            <button
              className="azals-btn azals-btn--ghost"
              onClick={onRefresh}
              disabled={isLoading}
              aria-label="Actualiser"
            >
              <RefreshCw size={16} className={isLoading ? 'azals-spin' : ''} />
            </button>
          )}
          {onExport && (
            <button
              className="azals-btn azals-btn--ghost"
              onClick={onExport}
              aria-label="Exporter"
            >
              <Download size={16} />
            </button>
          )}
        </div>
      </div>

      {/* Active filters bar */}
      {columnFilters && activeFilterCount > 0 && (
        <div className="azals-table__active-filters">
          <span className="azals-table__active-filters-label">
            <Filter size={14} />
            {activeFilterCount} filtre{activeFilterCount > 1 ? 's' : ''} actif{activeFilterCount > 1 ? 's' : ''}
          </span>
          <div className="azals-table__active-filters-list">
            {Object.entries(columnFilters.filters).map(([key, value]) => {
              if (!value) return null;
              const col = columns.find((c) => String(c.id) === key);
              const config = columnFilters.configs[key];
              let displayValue = String(value);
              if (config?.type === 'select' && config.options) {
                const opt = config.options.find((o) => o.value === value);
                displayValue = opt?.label || displayValue;
              }
              return (
                <span key={key} className="azals-table__active-filter-tag">
                  <span className="azals-table__active-filter-tag-label">{col?.header}:</span>
                  <span className="azals-table__active-filter-tag-value">{displayValue}</span>
                  <button
                    className="azals-table__active-filter-tag-remove"
                    onClick={() => columnFilters.onFilterChange(key, null)}
                    title="Supprimer ce filtre"
                  >
                    <X size={12} />
                  </button>
                </span>
              );
            })}
          </div>
          {columnFilters.onClearAllFilters && (
            <button
              className="azals-btn azals-btn--ghost azals-btn--sm"
              onClick={columnFilters.onClearAllFilters}
            >
              Effacer tout
            </button>
          )}
        </div>
      )}

      {/* Table */}
      <div className="azals-table__wrapper">
        <table className="azals-table">
          <TableHeader
            columns={columns}
            hasActions={!!hasActions}
            sorting={sorting}
            columnFilters={columnFilters}
            selectable={selectable}
            allSelected={allSelected}
            onSelectAll={handleSelectAll}
          />
          <tbody className="azals-table__body">
            {error ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0) + (hasActions ? 1 : 0)}
                  className="azals-table__error"
                >
                  <ErrorState
                    message={error.message}
                    onRetry={onRetry}
                  />
                </td>
              </tr>
            ) : isLoading ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0) + (hasActions ? 1 : 0)}
                  className="azals-table__loading"
                >
                  <LoadingState onRetry={onRetry} />
                </td>
              </tr>
            ) : displayData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0) + (hasActions ? 1 : 0)}
                  className="azals-table__empty"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              displayData.map((row) => (
                <TableRow
                  key={String(row[keyField])}
                  row={row}
                  columns={columns}
                  actions={actions}
                  selectable={selectable}
                  isSelected={isRowSelected(row)}
                  onSelect={() => handleSelectRow(row)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                />
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {pagination && (
        <Pagination
          page={pagination.page}
          pageSize={pagination.pageSize}
          total={pagination.total}
          onPageChange={pagination.onPageChange}
          onPageSizeChange={pagination.onPageSizeChange}
        />
      )}
    </div>
  );
}

// ============================================================
// SIMPLE TABLE (SANS PAGINATION)
// ============================================================

interface SimpleTableProps<T> {
  columns: TableColumn<T>[];
  data: T[];
  keyField: keyof T;
  isLoading?: boolean;
  emptyMessage?: string;
}

export function SimpleTable<T>({
  columns,
  data,
  keyField,
  isLoading,
  emptyMessage,
}: SimpleTableProps<T>) {
  return (
    <DataTable
      columns={columns}
      data={data}
      keyField={keyField}
      isLoading={isLoading}
      emptyMessage={emptyMessage}
    />
  );
}

export default DataTable;
