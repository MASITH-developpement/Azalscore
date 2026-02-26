/**
 * AZALSCORE - Badge Component
 * Composant Badge simple pour l'UI
 */

import React from 'react';

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'default' | 'secondary' | 'outline' | 'destructive';
  children: React.ReactNode;
}

const variantClasses: Record<string, string> = {
  default: 'bg-blue-100 text-blue-800',
  secondary: 'bg-gray-100 text-gray-800',
  outline: 'border border-gray-300 text-gray-800',
  destructive: 'bg-red-100 text-red-800',
};

export function Badge({
  className = '',
  variant = 'default',
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </span>
  );
}
