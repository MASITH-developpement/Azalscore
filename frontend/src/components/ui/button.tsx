/**
 * AZALSCORE - Button Component
 * Composant Button simple pour l'UI
 */

import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'primary' | 'secondary' | 'outline' | 'ghost' | 'link' | 'destructive';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  asChild?: boolean;
  children: React.ReactNode;
}

const variantClasses: Record<string, string> = {
  default: 'bg-blue-600 text-white hover:bg-blue-700',
  primary: 'bg-blue-600 text-white hover:bg-blue-700',
  secondary: 'bg-gray-100 text-gray-900 hover:bg-gray-200',
  outline: 'border border-gray-300 bg-white hover:bg-gray-50',
  ghost: 'hover:bg-gray-100',
  link: 'text-blue-600 underline-offset-4 hover:underline',
  destructive: 'bg-red-600 text-white hover:bg-red-700',
};

const sizeClasses: Record<string, string> = {
  default: 'h-10 px-4 py-2',
  sm: 'h-8 px-3 text-sm',
  lg: 'h-12 px-8 text-lg',
  icon: 'h-10 w-10 p-0',
};

export function Button({
  className = '',
  variant = 'default',
  size = 'default',
  asChild = false,
  children,
  ...props
}: ButtonProps) {
  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50';
  const classes = `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`;

  return (
    <button className={classes} {...props}>
      {children}
    </button>
  );
}
