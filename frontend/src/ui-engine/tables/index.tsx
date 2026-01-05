/**
 * AZALSCORE UI Engine - Table System
 * Tables génériques avec tri, filtres, pagination
 * Données fournies par API - AUCUNE logique métier
 */

import React, { useMemo, useState, useCallback } from 'react';
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
} from 'lucide-react';
import { CapabilityGuard } from '@core/capabilities';
import type { TableColumn, TableAction, TableState, PaginatedResponse } from '@/types';

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
  isLoading?: boolean;
  emptyMessage?: string;
  onRefresh?: () => void;
  onExport?: () => void;
  selectable?: boolean;
  selectedRows?: T[];
  onSelectionChange?: (rows: T[]) => void;
  className?: string;
}

// ============================================================
// TABLE HEADER
// ============================================================

interface TableHeaderProps<T> {
  columns: TableColumn<T>[];
  hasActions: boolean;
  sorting?: DataTableProps<T>['sorting'];
  selectable?: boolean;
  allSelected: boolean;
  onSelectAll: () => void;
}

function TableHeader<T>({
  columns,
  hasActions,
  sorting,
  selectable,
  allSelected,
  onSelectAll,
}: TableHeaderProps<T>) {
  const handleSort = (column: TableColumn<T>) => {
    if (!column.sortable || !sorting) return;

    const columnId = String(column.id);
    const newOrder =
      sorting.sortBy === columnId && sorting.sortOrder === 'asc' ? 'desc' : 'asc';
    sorting.onSort(columnId, newOrder);
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
        {columns.map((column) => (
          <th
            key={String(column.id)}
            className={clsx('azals-table__th', {
              'azals-table__th--sortable': column.sortable,
              [`azals-table__th--align-${column.align}`]: column.align,
            })}
            style={{ width: column.width }}
            onClick={() => column.sortable && handleSort(column)}
          >
            <div className="azals-table__th-content">
              <span>{column.header}</span>
              {column.sortable && sorting && (
                <span className="azals-table__sort-icon">
                  {sorting.sortBy === String(column.id) ? (
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
          </th>
        ))}
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
}

function TableRow<T>({
  row,
  columns,
  actions,
  selectable,
  isSelected,
  onSelect,
}: TableRowProps<T>) {
  const [actionsOpen, setActionsOpen] = useState(false);

  const getCellValue = (column: TableColumn<T>): unknown => {
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
      })}
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
  isLoading,
  emptyMessage = 'Aucune donnée disponible',
  onRefresh,
  onExport,
  selectable,
  selectedRows = [],
  onSelectionChange,
  className,
}: DataTableProps<T>) {
  const hasActions = actions && actions.length > 0;

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

    if (selectedRows.length === data.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange([...data]);
    }
  }, [data, selectedRows, onSelectionChange]);

  const allSelected = data.length > 0 && selectedRows.length === data.length;

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

      {/* Table */}
      <div className="azals-table__wrapper">
        <table className="azals-table">
          <TableHeader
            columns={columns}
            hasActions={!!hasActions}
            sorting={sorting}
            selectable={selectable}
            allSelected={allSelected}
            onSelectAll={handleSelectAll}
          />
          <tbody className="azals-table__body">
            {isLoading ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0) + (hasActions ? 1 : 0)}
                  className="azals-table__loading"
                >
                  <div className="azals-spinner" />
                  <span>Chargement...</span>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (selectable ? 1 : 0) + (hasActions ? 1 : 0)}
                  className="azals-table__empty"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row) => (
                <TableRow
                  key={String(row[keyField])}
                  row={row}
                  columns={columns}
                  actions={actions}
                  selectable={selectable}
                  isSelected={isRowSelected(row)}
                  onSelect={() => handleSelectRow(row)}
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
