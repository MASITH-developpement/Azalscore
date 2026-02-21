/**
 * AZALS MODULE - Réseaux Sociaux - Panneau de Configuration
 * =========================================================
 * Interface pour configurer les connexions aux plateformes marketing
 */

import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings, Link2, Link2Off, RefreshCw, CheckCircle, XCircle,
  AlertTriangle, ExternalLink, Key, Eye, EyeOff, Save, Trash2
} from 'lucide-react';
import { socialNetworksApi } from '../api';
import {
  PLATFORMS,
  type MarketingPlatform,
  type PlatformStatus,
  type AllPlatformsStatus,
  usesOAuth
} from '../types';

interface ConfigurationPanelProps {
  onClose?: () => void;
}

export function ConfigurationPanel({ onClose }: ConfigurationPanelProps) {
  const queryClient = useQueryClient();
  const [selectedPlatform, setSelectedPlatform] = useState<MarketingPlatform | null>(null);
  const [showApiKey, setShowApiKey] = useState(false);
  const [apiKeyInput, setApiKeyInput] = useState('');
  const [apiSecretInput, setApiSecretInput] = useState('');
  const [accountIdInput, setAccountIdInput] = useState('');
  const [propertyIdInput, setPropertyIdInput] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Récupération du statut de toutes les plateformes
  const { data: statusResponse, isLoading } = useQuery({
    queryKey: ['social-networks', 'config', 'status'],
    queryFn: socialNetworksApi.getAllPlatformsStatus,
  });

  const statusData = (statusResponse?.data || statusResponse || null) as AllPlatformsStatus | null;

  // Mutation pour sauvegarder la configuration
  const saveMutation = useMutation({
    mutationFn: async ({ platform, data }: { platform: MarketingPlatform; data: any }) => {
      return socialNetworksApi.savePlatformConfig(platform, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-networks', 'config'] });
      setMessage({ type: 'success', text: 'Configuration sauvegardée' });
      setTimeout(() => setMessage(null), 3000);
      resetForm();
    },
    onError: (error: any) => {
      setMessage({ type: 'error', text: error.message || 'Erreur de sauvegarde' });
    },
  });

  // Mutation pour initialiser OAuth
  const oauthMutation = useMutation({
    mutationFn: async (platform: MarketingPlatform) => {
      return socialNetworksApi.initOAuth(platform);
    },
    onSuccess: (response) => {
      const data = response?.data || response;
      if (data?.auth_url) {
        // Ouvrir la fenêtre OAuth
        window.open(data.auth_url, '_blank', 'width=600,height=700');
        setMessage({ type: 'success', text: 'Fenêtre OAuth ouverte. Terminez l\'autorisation.' });
      }
    },
    onError: (error: any) => {
      setMessage({ type: 'error', text: error.message || 'Erreur OAuth' });
    },
  });

  // Mutation pour synchroniser
  const syncMutation = useMutation({
    mutationFn: async (platform: MarketingPlatform) => {
      return socialNetworksApi.syncPlatform(platform);
    },
    onSuccess: (response) => {
      const data = response?.data || response;
      queryClient.invalidateQueries({ queryKey: ['social-networks'] });
      setMessage({
        type: data?.success ? 'success' : 'error',
        text: data?.message || 'Synchronisation terminée'
      });
      setTimeout(() => setMessage(null), 3000);
    },
    onError: (error: any) => {
      setMessage({ type: 'error', text: error.message || 'Erreur de synchronisation' });
    },
  });

  // Mutation pour supprimer la configuration
  const deleteMutation = useMutation({
    mutationFn: async (platform: MarketingPlatform) => {
      return socialNetworksApi.deletePlatformConfig(platform);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['social-networks', 'config'] });
      setMessage({ type: 'success', text: 'Configuration supprimée' });
      setTimeout(() => setMessage(null), 3000);
      setSelectedPlatform(null);
    },
    onError: (error: any) => {
      setMessage({ type: 'error', text: error.message || 'Erreur de suppression' });
    },
  });

  // Mutation pour tester la connexion
  const testMutation = useMutation({
    mutationFn: async (platform: MarketingPlatform) => {
      return socialNetworksApi.testConnection(platform);
    },
    onSuccess: (response) => {
      const data = response?.data || response;
      if (data?.status === 'connected') {
        setMessage({ type: 'success', text: 'Connexion réussie !' });
      } else {
        setMessage({ type: 'error', text: 'Connexion échouée' });
      }
      setTimeout(() => setMessage(null), 3000);
    },
    onError: (error: any) => {
      setMessage({ type: 'error', text: error.message || 'Erreur de test' });
    },
  });

  const resetForm = () => {
    setApiKeyInput('');
    setApiSecretInput('');
    setAccountIdInput('');
    setPropertyIdInput('');
    setSelectedPlatform(null);
  };

  const handleSaveConfig = () => {
    if (!selectedPlatform) return;

    const data: any = { platform: selectedPlatform };
    if (apiKeyInput) data.api_key = apiKeyInput;
    if (apiSecretInput) data.api_secret = apiSecretInput;
    if (accountIdInput) data.account_id = accountIdInput;
    if (propertyIdInput) data.property_id = propertyIdInput;

    saveMutation.mutate({ platform: selectedPlatform, data });
  };

  const getPlatformStatus = (platformId: string): PlatformStatus | undefined => {
    if (!statusData?.platforms) return undefined;
    return statusData.platforms.find(p => p.platform === platformId);
  };

  const getStatusIcon = (status: PlatformStatus | undefined) => {
    if (!status) return <Link2Off className="w-4 h-4 text-gray-400" />;
    if (status.is_connected && status.sync_status === 'success') {
      return <CheckCircle className="w-4 h-4 text-green-500" />;
    }
    if (status.is_connected && status.sync_status === 'error') {
      return <AlertTriangle className="w-4 h-4 text-yellow-500" />;
    }
    if (status.is_connected) {
      return <Link2 className="w-4 h-4 text-blue-500" />;
    }
    return <Link2Off className="w-4 h-4 text-gray-400" />;
  };

  const getStatusText = (status: PlatformStatus | undefined) => {
    if (!status) return 'Non configuré';
    if (status.is_connected) {
      if (status.sync_status === 'success') return 'Connecté et synchronisé';
      if (status.sync_status === 'error') return 'Connecté, erreur sync';
      return 'Connecté';
    }
    if (status.is_configured) return 'Configuré, non connecté';
    return 'Non configuré';
  };

  const formatLastSync = (dateStr: string | null) => {
    if (!dateStr) return 'Jamais';
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100">
      {/* Header */}
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Settings className="w-5 h-5 text-gray-500" />
          <h2 className="text-lg font-semibold text-gray-900">Configuration des Plateformes</h2>
        </div>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-xl">
            ×
          </button>
        )}
      </div>

      {/* Message */}
      {message && (
        <div className={`mx-4 mt-4 p-3 rounded-lg flex items-center gap-2 ${
          message.type === 'success'
            ? 'bg-green-50 border border-green-200 text-green-700'
            : 'bg-red-50 border border-red-200 text-red-700'
        }`}>
          {message.type === 'success' ? <CheckCircle className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
          {message.text}
        </div>
      )}

      {/* Summary */}
      <div className="p-4 bg-gray-50 border-b border-gray-100">
        <div className="grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl font-bold text-gray-900">{statusData?.total_configured || 0}</p>
            <p className="text-sm text-gray-500">Configurées</p>
          </div>
          <div>
            <p className="text-2xl font-bold text-green-600">{statusData?.total_connected || 0}</p>
            <p className="text-sm text-gray-500">Connectées</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">
              Dernière sync: {formatLastSync(statusData?.last_global_sync || null)}
            </p>
          </div>
        </div>
      </div>

      <div className="p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <RefreshCw className="w-6 h-6 text-gray-400 animate-spin" />
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4">
            {/* Liste des plateformes */}
            <div className="space-y-2">
              <h3 className="font-medium text-gray-700 mb-3">Plateformes</h3>
              {PLATFORMS.map((platform) => {
                const status = getPlatformStatus(platform.id);
                const isSelected = selectedPlatform === platform.id;

                return (
                  <button
                    key={platform.id}
                    onClick={() => setSelectedPlatform(platform.id as MarketingPlatform)}
                    className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
                      isSelected
                        ? 'bg-blue-50 border-2 border-blue-500'
                        : 'bg-gray-50 border-2 border-transparent hover:bg-gray-100'
                    }`}
                  >
                    <div
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${platform.color}20` }}
                    >
                      <Settings className="w-4 h-4" style={{ color: platform.color }} />
                    </div>
                    <div className="flex-1 text-left">
                      <p className="font-medium text-gray-900">{platform.name}</p>
                      <p className="text-xs text-gray-500">{getStatusText(status)}</p>
                    </div>
                    {getStatusIcon(status)}
                  </button>
                );
              })}
            </div>

            {/* Panneau de configuration */}
            <div>
              {selectedPlatform ? (
                <div className="bg-gray-50 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-4">
                    Configurer {PLATFORMS.find(p => p.id === selectedPlatform)?.name}
                  </h3>

                  {usesOAuth(selectedPlatform) ? (
                    // Configuration OAuth
                    <div className="space-y-4">
                      <p className="text-sm text-gray-600">
                        Cette plateforme utilise OAuth pour l'authentification.
                        Cliquez sur le bouton ci-dessous pour autoriser l'accès.
                      </p>

                      <button
                        onClick={() => oauthMutation.mutate(selectedPlatform)}
                        disabled={oauthMutation.isPending}
                        className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                      >
                        <ExternalLink className="w-4 h-4" />
                        {oauthMutation.isPending ? 'Ouverture...' : 'Connecter via OAuth'}
                      </button>

                      {/* Champs supplémentaires pour certaines plateformes */}
                      {(selectedPlatform === 'google_analytics' || selectedPlatform === 'google_search_console') && (
                        <div className="mt-4">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Property ID / Site URL
                          </label>
                          <input
                            type="text"
                            value={propertyIdInput}
                            onChange={(e) => setPropertyIdInput(e.target.value)}
                            placeholder="Ex: 123456789 ou https://example.com"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      )}

                      {(selectedPlatform === 'google_ads' || selectedPlatform === 'google_my_business') && (
                        <div className="mt-4">
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            Account ID / Location ID
                          </label>
                          <input
                            type="text"
                            value={accountIdInput}
                            onChange={(e) => setAccountIdInput(e.target.value)}
                            placeholder="Ex: 123-456-7890"
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          />
                        </div>
                      )}
                    </div>
                  ) : (
                    // Configuration avec clé API
                    <div className="space-y-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Clé API
                        </label>
                        <div className="relative">
                          <input
                            type={showApiKey ? 'text' : 'password'}
                            value={apiKeyInput}
                            onChange={(e) => setApiKeyInput(e.target.value)}
                            placeholder="Votre clé API"
                            className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                          />
                          <button
                            type="button"
                            onClick={() => setShowApiKey(!showApiKey)}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                          >
                            {showApiKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          Secret API (optionnel)
                        </label>
                        <input
                          type="password"
                          value={apiSecretInput}
                          onChange={(e) => setApiSecretInput(e.target.value)}
                          placeholder="Votre secret API"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          ID de compte/établissement
                        </label>
                        <input
                          type="text"
                          value={accountIdInput}
                          onChange={(e) => setAccountIdInput(e.target.value)}
                          placeholder="ID de votre compte"
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  )}

                  {/* Boutons d'action */}
                  <div className="flex gap-2 mt-6">
                    <button
                      onClick={handleSaveConfig}
                      disabled={saveMutation.isPending}
                      className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      <Save className="w-4 h-4" />
                      {saveMutation.isPending ? 'Sauvegarde...' : 'Sauvegarder'}
                    </button>

                    {getPlatformStatus(selectedPlatform)?.is_connected && (
                      <>
                        <button
                          onClick={() => testMutation.mutate(selectedPlatform)}
                          disabled={testMutation.isPending}
                          className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50"
                          title="Tester la connexion"
                        >
                          <Link2 className={`w-4 h-4 ${testMutation.isPending ? 'animate-pulse' : ''}`} />
                        </button>

                        <button
                          onClick={() => syncMutation.mutate(selectedPlatform)}
                          disabled={syncMutation.isPending}
                          className="px-4 py-2 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 disabled:opacity-50"
                          title="Synchroniser"
                        >
                          <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
                        </button>
                      </>
                    )}

                    {getPlatformStatus(selectedPlatform)?.is_configured && (
                      <button
                        onClick={() => {
                          if (confirm('Supprimer cette configuration ?')) {
                            deleteMutation.mutate(selectedPlatform);
                          }
                        }}
                        disabled={deleteMutation.isPending}
                        className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50"
                        title="Supprimer"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  {/* Infos sur la plateforme */}
                  {getPlatformStatus(selectedPlatform)?.is_configured && (
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <h4 className="text-sm font-medium text-gray-700 mb-2">Informations</h4>
                      <div className="text-sm text-gray-600 space-y-1">
                        <p>
                          Statut: {getStatusText(getPlatformStatus(selectedPlatform))}
                        </p>
                        <p>
                          Dernière sync: {formatLastSync(getPlatformStatus(selectedPlatform)?.last_sync_at || null)}
                        </p>
                        {getPlatformStatus(selectedPlatform)?.account_id && (
                          <p>
                            Compte: {getPlatformStatus(selectedPlatform)?.account_id}
                          </p>
                        )}
                        {getPlatformStatus(selectedPlatform)?.error_message && (
                          <p className="text-red-600">
                            Erreur: {getPlatformStatus(selectedPlatform)?.error_message}
                          </p>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-gray-50 rounded-lg p-8 text-center">
                  <Settings className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                  <p className="text-gray-500">
                    Sélectionnez une plateforme pour la configurer
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Bouton de synchronisation globale */}
        {statusData && statusData.total_connected > 0 && (
          <div className="mt-6 pt-4 border-t border-gray-100">
            <button
              onClick={() => {
                syncMutation.mutate('' as MarketingPlatform); // sync all via empty call
              }}
              disabled={syncMutation.isPending}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${syncMutation.isPending ? 'animate-spin' : ''}`} />
              Synchroniser toutes les plateformes connectées
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ConfigurationPanel;
