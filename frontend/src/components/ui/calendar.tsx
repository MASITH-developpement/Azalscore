/**
 * AZALSCORE - Calendar Component
 * Composant Calendar simple pour l'UI
 */

import React, { useState } from 'react';

interface CalendarProps {
  mode?: 'single' | 'range';
  selected?: Date | Date[];
  onSelect?: (date: Date | undefined) => void;
  disabled?: (date: Date) => boolean;
  className?: string;
  initialFocus?: boolean;
}

export function Calendar({
  selected,
  onSelect,
  disabled,
  className = '',
}: CalendarProps) {
  const [currentMonth, setCurrentMonth] = useState(() => {
    if (selected instanceof Date) return selected;
    return new Date();
  });

  const daysInMonth = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth() + 1,
    0
  ).getDate();

  const firstDayOfMonth = new Date(
    currentMonth.getFullYear(),
    currentMonth.getMonth(),
    1
  ).getDay();

  const days = [];
  for (let i = 0; i < firstDayOfMonth; i++) {
    days.push(null);
  }
  for (let i = 1; i <= daysInMonth; i++) {
    days.push(i);
  }

  const isSelected = (day: number) => {
    if (!selected || !day) return false;
    if (selected instanceof Date) {
      return (
        selected.getDate() === day &&
        selected.getMonth() === currentMonth.getMonth() &&
        selected.getFullYear() === currentMonth.getFullYear()
      );
    }
    return false;
  };

  const isDisabled = (day: number) => {
    if (!day || !disabled) return false;
    const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    return disabled(date);
  };

  const handleDayClick = (day: number) => {
    if (!day || isDisabled(day)) return;
    const date = new Date(currentMonth.getFullYear(), currentMonth.getMonth(), day);
    onSelect?.(date);
  };

  const monthNames = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
  ];

  const dayNames = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];

  return (
    <div className={`p-3 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <button
          type="button"
          className="p-1 hover:bg-gray-100 rounded"
          onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() - 1))}
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <span className="font-medium">
          {monthNames[currentMonth.getMonth()]} {currentMonth.getFullYear()}
        </span>
        <button
          type="button"
          className="p-1 hover:bg-gray-100 rounded"
          onClick={() => setCurrentMonth(new Date(currentMonth.getFullYear(), currentMonth.getMonth() + 1))}
        >
          <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1 text-center text-xs text-gray-500 mb-2">
        {dayNames.map((day) => (
          <div key={day} className="p-1">{day}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 gap-1">
        {days.map((day, index) => (
          <button
            key={index}
            type="button"
            disabled={!day || isDisabled(day)}
            className={`p-2 text-sm rounded ${
              !day
                ? ''
                : isSelected(day)
                ? 'bg-blue-600 text-white'
                : isDisabled(day)
                ? 'text-gray-300 cursor-not-allowed'
                : 'hover:bg-gray-100'
            }`}
            onClick={() => day && handleDayClick(day)}
          >
            {day}
          </button>
        ))}
      </div>
    </div>
  );
}
