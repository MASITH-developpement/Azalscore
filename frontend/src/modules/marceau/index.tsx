/**
 * AZALSCORE - Module Marceau AI Assistant
 * ========================================
 * Agent IA polyvalent capable de gerer 9 domaines metiers.
 */

import React, { useState } from 'react';
import { Bot, Activity, Phone, Brain, Settings } from 'lucide-react';

import { MarceauDashboard } from './components/MarceauDashboard';
import { MarceauSettings } from './components/MarceauSettings';
import { MarceauActions } from './components/MarceauActions';
import { MarceauConversations } from './components/MarceauConversations';
import { MarceauMemory } from './components/MarceauMemory';

interface TabConfig {
  id: string;
  label: string;
  icon: React.ReactNode;
  component: React.ComponentType;
}

const TABS: TabConfig[] = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: <Activity size={16} />,
    component: MarceauDashboard,
  },
  {
    id: 'actions',
    label: 'Actions',
    icon: <Bot size={16} />,
    component: MarceauActions,
  },
  {
    id: 'conversations',
    label: 'Conversations',
    icon: <Phone size={16} />,
    component: MarceauConversations,
  },
  {
    id: 'memory',
    label: 'Memoire',
    icon: <Brain size={16} />,
    component: MarceauMemory,
  },
  {
    id: 'settings',
    label: 'Configuration',
    icon: <Settings size={16} />,
    component: MarceauSettings,
  },
];

/**
 * Module Marceau - Agent IA Polyvalent
 */
export default function MarceauModule() {
  const [activeTab, setActiveTab] = useState('dashboard');

  const ActiveComponent = TABS.find(t => t.id === activeTab)?.component || MarceauDashboard;

  return (
    <div className="azals-page">
      {/* Header */}
      <header className="azals-page__header">
        <div className="azals-page__header-text">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <Bot className="text-blue-600" size={24} />
            </div>
            <div>
              <h1 className="azals-page__title">Marceau AI Assistant</h1>
              <p className="text-sm text-gray-500">Agent IA polyvalent - 9 domaines metiers</p>
            </div>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <div className="border-b border-gray-200 mb-6">
        <nav className="flex gap-1">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors text-sm font-medium ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Content */}
      <div className="azals-page__body">
        <ActiveComponent />
      </div>
    </div>
  );
}
