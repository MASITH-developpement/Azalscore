/**
 * AZALSCORE - Marceau Conversations Component
 * ============================================
 * Historique des conversations telephoniques.
 */

import React, { useState, useEffect } from 'react';
import { Phone, Clock, Star, ChevronDown, ChevronUp, AlertCircle, Play } from 'lucide-react';
import { api } from '@core/api-client';

interface MarceauConversation {
  id: string;
  caller_phone: string;
  caller_name: string | null;
  customer_id: string | null;
  transcript: string | null;
  summary: string | null;
  intent: string | null;
  duration_seconds: number;
  satisfaction_score: number | null;
  outcome: string | null;
  recording_url: string | null;
  transferred_to: string | null;
  transfer_reason: string | null;
  started_at: string;
  ended_at: string | null;
}

const OUTCOME_LABELS: Record<string, { label: string; color: string }> = {
  quote_created: { label: 'Devis cree', color: 'bg-green-100 text-green-700' },
  appointment_scheduled: { label: 'RDV planifie', color: 'bg-blue-100 text-blue-700' },
  transferred: { label: 'Transfere', color: 'bg-purple-100 text-purple-700' },
  voicemail: { label: 'Messagerie', color: 'bg-gray-100 text-gray-700' },
  abandoned: { label: 'Abandonne', color: 'bg-red-100 text-red-700' },
  information_provided: { label: 'Info fournie', color: 'bg-cyan-100 text-cyan-700' },
  callback_scheduled: { label: 'Rappel prevu', color: 'bg-amber-100 text-amber-700' },
  complaint_recorded: { label: 'Reclamation', color: 'bg-orange-100 text-orange-700' },
};

export function MarceauConversations() {
  const [conversations, setConversations] = useState<MarceauConversation[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [filterOutcome, setFilterOutcome] = useState<string>('');
  const pageSize = 20;

  useEffect(() => {
    loadConversations();
  }, [page, filterOutcome]);

  const loadConversations = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filterOutcome) params.append('outcome', filterOutcome);
      params.append('skip', String((page - 1) * pageSize));
      params.append('limit', String(pageSize));

      const response = await api.get<{ items: MarceauConversation[]; total: number }>(
        `/marceau/conversations?${params}`
      );
      setConversations(response.data.items || []);
      setTotal(response.data.total || 0);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Erreur chargement');
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (loading && conversations.length === 0) {
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
        <select
          value={filterOutcome}
          onChange={(e) => { setFilterOutcome(e.target.value); setPage(1); }}
          className="border rounded px-3 py-2 text-sm"
        >
          <option value="">Tous les resultats</option>
          {Object.entries(OUTCOME_LABELS).map(([key, { label }]) => (
            <option key={key} value={key}>{label}</option>
          ))}
        </select>
        <div className="text-sm text-gray-500">
          {total} conversation{total > 1 ? 's' : ''}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <AlertCircle className="inline mr-2" size={16} />
          {error}
        </div>
      )}

      {/* Conversations List */}
      <div className="space-y-2">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            className="bg-white border rounded-lg overflow-hidden"
          >
            <div
              className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
              onClick={() => setExpandedId(expandedId === conv.id ? null : conv.id)}
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 bg-green-100 rounded-full flex items-center justify-center">
                  <Phone className="text-green-600" size={20} />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-medium">
                      {conv.caller_name || conv.caller_phone}
                    </span>
                    {conv.outcome && (
                      <span className={`text-xs px-2 py-0.5 rounded-full ${OUTCOME_LABELS[conv.outcome]?.color || 'bg-gray-100'}`}>
                        {OUTCOME_LABELS[conv.outcome]?.label || conv.outcome}
                      </span>
                    )}
                  </div>
                  <div className="text-sm text-gray-500">
                    {new Date(conv.started_at).toLocaleString('fr-FR')}
                    {conv.intent && ` - ${conv.intent}`}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right">
                  <div className="flex items-center gap-1 text-sm">
                    <Clock size={14} className="text-gray-400" />
                    {formatDuration(conv.duration_seconds)}
                  </div>
                  {conv.satisfaction_score && (
                    <div className="flex items-center gap-1 text-sm">
                      <Star size={14} className="text-amber-400" />
                      {conv.satisfaction_score.toFixed(1)}
                    </div>
                  )}
                </div>
                {expandedId === conv.id ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
              </div>
            </div>

            {/* Expanded Details */}
            {expandedId === conv.id && (
              <div className="border-t p-4 bg-gray-50 space-y-4">
                {conv.summary && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Resume</h4>
                    <p className="text-sm text-gray-700 bg-white p-3 rounded border">
                      {conv.summary}
                    </p>
                  </div>
                )}

                {conv.transcript && (
                  <div>
                    <h4 className="text-sm font-medium mb-2">Transcript</h4>
                    <pre className="text-xs bg-white p-3 rounded border overflow-auto max-h-60 whitespace-pre-wrap">
                      {conv.transcript}
                    </pre>
                  </div>
                )}

                {conv.transferred_to && (
                  <div className="text-sm">
                    <strong>Transfere vers:</strong> {conv.transferred_to}
                    {conv.transfer_reason && ` (${conv.transfer_reason})`}
                  </div>
                )}

                {conv.recording_url && (
                  <div>
                    <button className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700" onClick={() => { if (conv.recording_url) window.open(conv.recording_url, '_blank'); }}>
                      <Play size={14} />
                      Ecouter l'enregistrement
                    </button>
                  </div>
                )}

                <div className="flex gap-4 text-sm text-gray-500">
                  <span>
                    <strong>Telephone:</strong> {conv.caller_phone}
                  </span>
                  {conv.customer_id && (
                    <span>
                      <strong>Client:</strong> {conv.customer_id.slice(0, 8)}...
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Empty State */}
      {conversations.length === 0 && !loading && (
        <div className="text-center py-12 text-gray-500">
          <Phone size={48} className="mx-auto mb-4 opacity-50" />
          <p>Aucune conversation trouvee</p>
        </div>
      )}

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
