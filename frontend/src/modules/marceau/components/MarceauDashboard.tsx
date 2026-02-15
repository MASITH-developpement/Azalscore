/**
 * AZALSCORE - Marceau Dashboard Component
 * ========================================
 * Dashboard temps reel pour l'agent IA Marceau.
 */

import React, { useState, useEffect } from 'react';
import { api } from '@core/api-client';
import { Phone, FileText, Calendar, MessageSquare, TrendingUp, TrendingDown, AlertCircle, Clock, Bot } from 'lucide-react';

interface DashboardData {
  total_actions_today: number;
  total_conversations_today: number;
  total_quotes_today: number;
  total_appointments_today: number;
  actions_trend: number;
  conversations_trend: number;
  quotes_trend: number;
  appointments_trend: number;
  actions_by_module: Record<string, number>;
  pending_validations: number;
  recent_actions: any[];
  alerts: any[];
  avg_confidence_score: number;
}

export function MarceauDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboard();
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboard, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboard = async () => {
    try {
      const response = await api.get<DashboardData>('/v3/marceau/dashboard');
      setData(response.data);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Erreur chargement dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
        <AlertCircle className="inline mr-2" size={16} />
        {error}
      </div>
    );
  }

  if (!data) return null;

  const TrendIcon = ({ value }: { value: number }) => {
    if (value > 0) return <TrendingUp className="text-green-500" size={16} />;
    if (value < 0) return <TrendingDown className="text-red-500" size={16} />;
    return null;
  };

  return (
    <div className="space-y-6">
      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Actions aujourd'hui</p>
              <p className="text-2xl font-bold">{data.total_actions_today}</p>
            </div>
            <div className="flex items-center gap-1">
              <Bot className="text-blue-500" size={24} />
              <TrendIcon value={data.actions_trend} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            {data.actions_trend > 0 ? '+' : ''}{data.actions_trend.toFixed(0)}% vs hier
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Conversations</p>
              <p className="text-2xl font-bold">{data.total_conversations_today}</p>
            </div>
            <div className="flex items-center gap-1">
              <Phone className="text-green-500" size={24} />
              <TrendIcon value={data.conversations_trend} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            {data.conversations_trend > 0 ? '+' : ''}{data.conversations_trend.toFixed(0)}% vs hier
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">Devis crees</p>
              <p className="text-2xl font-bold">{data.total_quotes_today}</p>
            </div>
            <div className="flex items-center gap-1">
              <FileText className="text-purple-500" size={24} />
              <TrendIcon value={data.quotes_trend} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            {data.quotes_trend > 0 ? '+' : ''}{data.quotes_trend.toFixed(0)}% vs hier
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500">RDV planifies</p>
              <p className="text-2xl font-bold">{data.total_appointments_today}</p>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="text-orange-500" size={24} />
              <TrendIcon value={data.appointments_trend} />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-1">
            {data.appointments_trend > 0 ? '+' : ''}{data.appointments_trend.toFixed(0)}% vs hier
          </p>
        </div>
      </div>

      {/* Alertes et validations */}
      {data.pending_validations > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <AlertCircle className="text-amber-500" size={20} />
            <span className="font-medium text-amber-700">
              {data.pending_validations} action{data.pending_validations > 1 ? 's' : ''} en attente de validation
            </span>
          </div>
        </div>
      )}

      {/* Actions par module */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="font-semibold mb-4">Actions par module</h3>
        <div className="grid grid-cols-3 md:grid-cols-5 gap-4">
          {Object.entries(data.actions_by_module).map(([module, count]) => (
            <div key={module} className="text-center p-3 bg-gray-50 rounded-lg">
              <p className="text-2xl font-bold text-gray-700">{count}</p>
              <p className="text-xs text-gray-500 capitalize">{module}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Dernieres actions */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="font-semibold mb-4">Actions recentes</h3>
        <div className="space-y-2">
          {data.recent_actions.slice(0, 10).map((action: any) => (
            <div
              key={action.id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <div className={`w-2 h-2 rounded-full ${
                  action.status === 'completed' ? 'bg-green-500' :
                  action.status === 'failed' ? 'bg-red-500' :
                  action.status === 'needs_validation' ? 'bg-amber-500' :
                  'bg-blue-500'
                }`} />
                <div>
                  <p className="font-medium text-sm">{action.action_type}</p>
                  <p className="text-xs text-gray-500">{action.module}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-xs text-gray-400">
                  <Clock className="inline mr-1" size={12} />
                  {new Date(action.created_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                </p>
                <p className="text-xs text-gray-500">
                  Confiance: {(action.confidence_score * 100).toFixed(0)}%
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Metriques IA */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="font-semibold mb-4">Metriques IA</h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <p className="text-3xl font-bold text-blue-600">
              {(data.avg_confidence_score * 100).toFixed(0)}%
            </p>
            <p className="text-sm text-gray-600">Confiance moyenne</p>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <p className="text-3xl font-bold text-green-600">
              {data.pending_validations === 0 ? '100%' :
                ((data.total_actions_today - data.pending_validations) / Math.max(data.total_actions_today, 1) * 100).toFixed(0) + '%'}
            </p>
            <p className="text-sm text-gray-600">Autonomie effective</p>
          </div>
        </div>
      </div>
    </div>
  );
}
