/**
 * AZALSCORE - Marceau Memory Component
 * =====================================
 * Gestion de la memoire et base de connaissances.
 */

import React, { useState, useEffect } from 'react';
import { api } from '@core/api-client';
import { Brain, Upload, Search, Trash2, Plus, FileText, AlertCircle, Tag, Star } from 'lucide-react';

interface MarceauMemory {
  id: string;
  memory_type: string;
  content: string;
  summary: string | null;
  tags: string[];
  importance_score: number;
  is_permanent: boolean;
  source: string | null;
  source_file_name: string | null;
  created_at: string;
}

interface KnowledgeDocument {
  id: string;
  file_name: string;
  file_type: string;
  file_size: number;
  is_processed: boolean;
  chunks_count: number;
  processing_error: string | null;
  category: string | null;
  tags: string[];
  created_at: string;
}

interface MemoryStats {
  total_memories: number;
  by_type: Record<string, number>;
  permanent_count: number;
  avg_importance: number;
}

const MEMORY_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  conversation: { label: 'Conversation', color: 'bg-blue-100 text-blue-700' },
  customer_profile: { label: 'Profil client', color: 'bg-green-100 text-green-700' },
  decision: { label: 'Decision', color: 'bg-purple-100 text-purple-700' },
  learning: { label: 'Apprentissage', color: 'bg-amber-100 text-amber-700' },
  knowledge: { label: 'Connaissance', color: 'bg-cyan-100 text-cyan-700' },
};

export function MarceauMemory() {
  const [memories, setMemories] = useState<MarceauMemory[]>([]);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'memories' | 'documents'>('memories');
  const [searchQuery, setSearchQuery] = useState('');
  const [uploading, setUploading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [statsRes, docsRes] = await Promise.all([
        api.get<MemoryStats>('/v1/marceau/memory/stats'),
        api.get<KnowledgeDocument[]>('/v1/marceau/knowledge'),
      ]);
      setStats(statsRes.data);
      setDocuments(docsRes.data);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Erreur chargement');
    } finally {
      setLoading(false);
    }
  };

  const searchMemories = async () => {
    if (!searchQuery.trim()) {
      setMemories([]);
      return;
    }

    try {
      const response = await api.post<{ memories: MarceauMemory[] }>('/v1/marceau/memory/search', {
        query: searchQuery,
        limit: 20,
      });
      setMemories(response.data.memories || []);
    } catch (e: any) {
      setError(e.message || 'Erreur recherche');
    }
  };

  const uploadDocument = async (file: File) => {
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await api.post('/v1/marceau/knowledge/upload', formData);
      loadData();
    } catch (e: any) {
      setError(e.message || 'Erreur upload');
    } finally {
      setUploading(false);
    }
  };

  const deleteDocument = async (id: string) => {
    if (!confirm('Supprimer ce document ?')) return;

    try {
      await api.delete(`/v1/marceau/knowledge/${id}`);
      loadData();
    } catch (e: any) {
      setError(e.message || 'Erreur suppression');
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          <AlertCircle className="inline mr-2" size={16} />
          {error}
        </div>
      )}

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <Brain className="mx-auto text-blue-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{stats.total_memories}</p>
            <p className="text-sm text-gray-500">Memoires totales</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <FileText className="mx-auto text-green-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{documents.length}</p>
            <p className="text-sm text-gray-500">Documents</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <Star className="mx-auto text-amber-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{stats.permanent_count}</p>
            <p className="text-sm text-gray-500">Permanentes</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4 text-center">
            <Tag className="mx-auto text-purple-500 mb-2" size={24} />
            <p className="text-2xl font-bold">{(stats.avg_importance * 100).toFixed(0)}%</p>
            <p className="text-sm text-gray-500">Importance moy.</p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          <button
            onClick={() => setActiveTab('memories')}
            className={`px-4 py-2 border-b-2 transition-colors ${
              activeTab === 'memories'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Recherche memoire
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={`px-4 py-2 border-b-2 transition-colors ${
              activeTab === 'documents'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Documents ({documents.length})
          </button>
        </nav>
      </div>

      {/* Memory Search */}
      {activeTab === 'memories' && (
        <div className="space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchMemories()}
                placeholder="Rechercher dans la memoire de Marceau..."
                className="w-full pl-10 pr-4 py-2 border rounded-lg"
              />
            </div>
            <button
              onClick={searchMemories}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Rechercher
            </button>
          </div>

          {memories.length > 0 && (
            <div className="space-y-2">
              {memories.map((memory) => (
                <div key={memory.id} className="bg-white border rounded-lg p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          MEMORY_TYPE_LABELS[memory.memory_type]?.color || 'bg-gray-100'
                        }`}>
                          {MEMORY_TYPE_LABELS[memory.memory_type]?.label || memory.memory_type}
                        </span>
                        {memory.is_permanent && (
                          <Star className="text-amber-500" size={14} />
                        )}
                        <span className="text-xs text-gray-400">
                          Importance: {(memory.importance_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-sm text-gray-700">{memory.content}</p>
                      {memory.tags.length > 0 && (
                        <div className="flex gap-1 mt-2">
                          {memory.tags.map((tag, i) => (
                            <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="text-xs text-gray-400">
                      {new Date(memory.created_at).toLocaleDateString('fr-FR')}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {searchQuery && memories.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              Aucun resultat pour "{searchQuery}"
            </div>
          )}
        </div>
      )}

      {/* Documents */}
      {activeTab === 'documents' && (
        <div className="space-y-4">
          {/* Upload Zone */}
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            <input
              type="file"
              id="file-upload"
              className="hidden"
              accept=".pdf,.doc,.docx,.txt,.csv"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) uploadDocument(file);
              }}
            />
            <label htmlFor="file-upload" className="cursor-pointer">
              <Upload className="mx-auto text-gray-400 mb-4" size={48} />
              <p className="text-gray-600 mb-2">
                {uploading ? 'Upload en cours...' : 'Glissez un fichier ou cliquez pour uploader'}
              </p>
              <p className="text-xs text-gray-400">
                Formats acceptes: PDF, Word, TXT, CSV
              </p>
            </label>
          </div>

          {/* Documents List */}
          <div className="space-y-2">
            {documents.map((doc) => (
              <div key={doc.id} className="bg-white border rounded-lg p-4 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <FileText className="text-blue-500" size={24} />
                  <div>
                    <p className="font-medium">{doc.file_name}</p>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <span>{formatFileSize(doc.file_size)}</span>
                      <span>-</span>
                      <span>{doc.chunks_count} chunks</span>
                      <span>-</span>
                      <span className={doc.is_processed ? 'text-green-600' : 'text-amber-600'}>
                        {doc.is_processed ? 'Traite' : 'En cours'}
                      </span>
                    </div>
                    {doc.processing_error && (
                      <p className="text-xs text-red-500 mt-1">{doc.processing_error}</p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => deleteDocument(doc.id)}
                  className="p-2 text-red-500 hover:bg-red-50 rounded"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            ))}
          </div>

          {documents.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <FileText size={48} className="mx-auto mb-4 opacity-50" />
              <p>Aucun document uploade</p>
              <p className="text-sm">Uploadez des fichiers pour enrichir la base de connaissances</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
