/**
 * AZALSCORE - Marceau Actions Component
 * ======================================
 * Liste et validation des actions Marceau.
 */

import React, { useState, useEffect } from 'react';
import { Check, X, AlertCircle, Filter, ChevronDown, ChevronUp, Bot } from 'lucide-react';
import { api } from '@core/api-client';
import type { ApiMutationError } from '@/types';

interface MarceauAction {
  id: string;
  module: string;
  action_type: string;
  status: string;
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  confidence_score: number;
  required_human_validation: boolean;
  validated_by: string | null;
  validated_at: string | null;
  validation_notes: string | null;
  related_entity_type: string | null;
  related_entity_id: string | null;
  duration_seconds: number;
  error_message: string | null;
  created_at: string;
}

const STATUS_LABELS: Record<string, { label: string; color: string }> = {
  pending: { label: 'En attente', color: 'bg-gray-100 text-gray-700' },
  in_progress: { label: 'En cours', color: 'bg-blue-100 text-blue-700' },
  completed: { label: 'Terminee', color: 'bg-green-100 text-green-700' },
  failed: { label: 'Echouee', color: 'bg-red-100 text-red-700' },
  needs_validation: { label: 'A valider', color: 'bg-amber-100 text-amber-700' },
  validated: { label: 'Validee', color: 'bg-green-100 text-green-700' },
  rejected: { label: 'Rejetee', color: 'bg-red-100 text-red-700' },
};

export function MarceauActions() {
  const [actions, setActions] = useState<MarceauAction[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [validating, setValidating] = useState<string | null>(null);

  // Filters
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [filterModule, setFilterModule] = useState<string>('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    loadActions();
  }, [filterStatus, filterModule, page]);

  const loadActions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterStatus) params.append('status', filterStatus);
      if (filterModule) params.append('module', filterModule);
      params.append('skip', String((page - 1) * pageSize));
      params.append('limit', String(pageSize));

      const response = await api.get<{ items: MarceauAction[]; total: number }>(
        `/marceau/actions?${params}`
      );
      setActions(response.data?.items || []);
      setTotal(response.data?.total || 0);
      setError(null);
    } catch (e: unknown) {
      setError((e as ApiMutationError).message || 'Erreur chargement');
    } finally {
      setLoading(false);
    }
  };

  const validateAction = async (actionId: string, approved: boolean, notes?: string) => {
    setValidating(actionId);
    try {
      await api.post(`/marceau/actions/${actionId}/validate`, {
        approved,
        notes,
      });
      loadActions();
    } catch (e: unknown) {
      setError((e as ApiMutationError).message || 'Erreur validation');
    } finally {
      setValidating(null);
    }
  };

  if (loading && actions.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex gap-4 items-center">
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-400" />
          <select
            value={filterStatus}
            onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="">Tous les statuts</option>
            <option value="needs_validation">A valider</option>
            <option value="completed">Terminees</option>
            <option value="failed">Echouees</option>
            <option value="pending">En attente</option>
          </select>
          <select
            value={filterModule}
            onChange={(e) => { setFilterModule(e.target.value); setPage(1); }}
            className="border rounded px-3 py-2 text-sm"
          >
            <option value="">Tous les modules</option>
            <option value="telephonie">Telephonie</option>
            <option value="commercial">Commercial</option>
            <option value="marketing">Marketing</option>
            <option value="seo">SEO</option>
            <option value="support">Support</option>
          </select>
        </div>
        <div className="text-sm text-gray-500">
          {total} action{total > 1 ? 's' : ''}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <AlertCircle className="inline mr-2" size={16} />
          {error}
        </div>
      )}

      {/* Actions List */}
      <div className="space-y-2">
        {actions.map((action) => (
          <div
            key={action.id}
            className="bg-white border rounded-lg overflow-hidden"
          >
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
              onClick={() => setExpandedId(expandedId === action.id ? null : action.id)}
            >
              <div className="flex items-center gap-4">
                <Bot className="text-blue-500" size={20} />
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{action.action_type}</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${STATUS_LABELS[action.status]?.color || 'bg-gray-100'}`}>
                      {STATUS_LABELS[action.status]?.label || action.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-500">
                    {action.module} - {new Date(action.created_at).toLocaleString('fr-FR')}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="text-sm font-medium">
                    {(action.confidence_score * 100).toFixed(0)}% confiance
                  </div>
                  <div className="text-xs text-gray-400">
                    {action.duration_seconds.toFixed(1)}s
                  </div>
                </div>
                {expandedId === action.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </div>
            </div>

            {/* Expanded Details */}
            {expandedId === action.id && (
              <div className="border-t p-4 bg-gray-50">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <h4 className="text-sm font-medium mb-2">Donnees d'entree</h4>
                    <pre className="text-xs bg-white p-3 rounded border overflow-auto max-h-40">
                      {JSON.stringify(action.input_data, null, 2)}
                    </pre>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium mb-2">Resultat</h4>
                    <pre className="text-xs bg-white p-3 rounded border overflow-auto max-h-40">
                      {JSON.stringify(action.output_data, null, 2)}
                    </pre>
                  </div>
                </div>

                {action.error_message && (
                  <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                    <strong>Erreur:</strong> {action.error_message}
                  </div>
                )}

                {action.related_entity_type && (
                  <div className="mt-4 text-sm">
                    <strong>Entite liee:</strong> {action.related_entity_type}
                    {action.related_entity_id && ` (${action.related_entity_id.slice(0, 8)}...)`}
                  </div>
                )}

                {/* Validation Actions */}
                {action.status === 'needs_validation' && (
                  <div className="mt-4 flex gap-3">
                    <button
                      onClick={() => validateAction(action.id, true)}
                      disabled={validating === action.id}
                      className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      {validating === action.id ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                      ) : (
                        <Check size={16} />
                      )}
                      Valider
                    </button>
                    <button
                      onClick={() => {
                        const notes = prompt('Raison du rejet:');
                        if (notes !== null) validateAction(action.id, false, notes);
                      }}
                      disabled={validating === action.id}
                      className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                    >
                      <X size={16} />
                      Rejeter
                    </button>
                  </div>
                )}

                {action.validated_at && (
                  <div className="mt-4 text-sm text-gray-500">
                    Valide le {new Date(action.validated_at).toLocaleString('fr-FR')}
                    {action.validation_notes && ` - ${action.validation_notes}`}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Pagination */}
      {total > pageSize && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Precedent
          </button>
          <span className="px-4 py-2">
            Page {page} / {Math.ceil(total / pageSize)}
          </span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={page >= Math.ceil(total / pageSize)}
            className="px-4 py-2 border rounded disabled:opacity-50"
          >
            Suivant
          </button>
        </div>
      )}
    </div>
  );
}
