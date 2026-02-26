/**
 * AZALSCORE - Table Components
 * Composants Table simples pour l'UI
 */

import React from 'react';

interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  children: React.ReactNode;
}

export function Table({ className = '', children, ...props }: TableProps) {
  return (
    <div className="relative w-full overflow-auto">
      <table
        className={`w-full caption-bottom text-sm ${className}`}
        {...props}
      >
        {children}
      </table>
    </div>
  );
}

interface TableHeaderProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  children: React.ReactNode;
}

export function TableHeader({ className = '', children, ...props }: TableHeaderProps) {
  return (
    <thead className={`[&_tr]:border-b ${className}`} {...props}>
      {children}
    </thead>
  );
}

interface TableBodyProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  children: React.ReactNode;
}

export function TableBody({ className = '', children, ...props }: TableBodyProps) {
  return (
    <tbody className={`[&_tr:last-child]:border-0 ${className}`} {...props}>
      {children}
    </tbody>
  );
}

interface TableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  children: React.ReactNode;
}

export function TableRow({ className = '', children, ...props }: TableRowProps) {
  return (
    <tr
      className={`border-b transition-colors hover:bg-gray-50 ${className}`}
      {...props}
    >
      {children}
    </tr>
  );
}

interface TableHeadProps extends React.ThHTMLAttributes<HTMLTableCellElement> {
  children?: React.ReactNode;
}

export function TableHead({ className = '', children, ...props }: TableHeadProps) {
  return (
    <th
      className={`h-12 px-4 text-left align-middle font-medium text-gray-500 [&:has([role=checkbox])]:pr-0 ${className}`}
      {...props}
    >
      {children}
    </th>
  );
}

interface TableCellProps extends React.TdHTMLAttributes<HTMLTableCellElement> {
  children?: React.ReactNode;
}

export function TableCell({ className = '', children, ...props }: TableCellProps) {
  return (
    <td
      className={`p-4 align-middle [&:has([role=checkbox])]:pr-0 ${className}`}
      {...props}
    >
      {children}
    </td>
  );
}
