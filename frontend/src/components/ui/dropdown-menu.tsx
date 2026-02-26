/**
 * AZALSCORE - Dropdown Menu Components
 * Composants DropdownMenu simples pour l'UI
 */

import React, { createContext, useContext, useState, useRef, useEffect } from 'react';

interface DropdownMenuContextValue {
  open: boolean;
  setOpen: (open: boolean) => void;
}

const DropdownMenuContext = createContext<DropdownMenuContextValue | null>(null);

interface DropdownMenuProps {
  children: React.ReactNode;
}

export function DropdownMenu({ children }: DropdownMenuProps) {
  const [open, setOpen] = useState(false);

  return (
    <DropdownMenuContext.Provider value={{ open, setOpen }}>
      <div className="relative inline-block">
        {children}
      </div>
    </DropdownMenuContext.Provider>
  );
}

interface DropdownMenuTriggerProps {
  asChild?: boolean;
  children: React.ReactNode;
}

export function DropdownMenuTrigger({ asChild, children }: DropdownMenuTriggerProps) {
  const context = useContext(DropdownMenuContext);
  if (!context) throw new Error('DropdownMenuTrigger must be used within DropdownMenu');

  const handleClick = () => context.setOpen(!context.open);

  if (asChild && React.isValidElement(children)) {
    return React.cloneElement(children as React.ReactElement<{ onClick?: () => void }>, {
      onClick: handleClick,
    });
  }

  return (
    <button type="button" onClick={handleClick}>
      {children}
    </button>
  );
}

interface DropdownMenuContentProps {
  align?: 'start' | 'center' | 'end';
  children: React.ReactNode;
}

export function DropdownMenuContent({ align = 'end', children }: DropdownMenuContentProps) {
  const context = useContext(DropdownMenuContext);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        context?.setOpen(false);
      }
    };
    if (context?.open) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [context?.open]);

  if (!context?.open) return null;

  const alignClass = align === 'end' ? 'right-0' : align === 'start' ? 'left-0' : 'left-1/2 -translate-x-1/2';

  return (
    <div
      ref={ref}
      className={`absolute z-50 mt-1 min-w-[8rem] overflow-hidden rounded-md border border-gray-200 bg-white p-1 shadow-lg ${alignClass}`}
    >
      {children}
    </div>
  );
}

interface DropdownMenuItemProps extends React.HTMLAttributes<HTMLDivElement> {
  asChild?: boolean;
  children: React.ReactNode;
}

export function DropdownMenuItem({ className = '', asChild, children, onClick, ...props }: DropdownMenuItemProps) {
  const context = useContext(DropdownMenuContext);

  const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
    onClick?.(e);
    context?.setOpen(false);
  };

  if (asChild && React.isValidElement(children)) {
    return (
      <div
        className={`relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-gray-100 ${className}`}
        onClick={handleClick}
        {...props}
      >
        {children}
      </div>
    );
  }

  return (
    <div
      className={`relative flex cursor-pointer select-none items-center rounded-sm px-2 py-1.5 text-sm outline-none hover:bg-gray-100 ${className}`}
      onClick={handleClick}
      {...props}
    >
      {children}
    </div>
  );
}

export function DropdownMenuSeparator() {
  return <div className="-mx-1 my-1 h-px bg-gray-200" />;
}

export function DropdownMenuLabel({ className = '', children }: { className?: string; children: React.ReactNode }) {
  return (
    <div className={`px-2 py-1.5 text-sm font-semibold ${className}`}>
      {children}
    </div>
  );
}
