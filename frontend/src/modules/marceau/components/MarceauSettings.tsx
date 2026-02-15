/**
 * AZALSCORE - Marceau Settings Component
 * =======================================
 * Configuration de l'agent IA Marceau.
 */

import React, { useState, useEffect } from 'react';
import { api } from '@core/api-client';
import { Save, RefreshCw, AlertCircle, Check, Settings, Phone, Share2, Brain, History } from 'lucide-react';

interface MarceauConfig {
  id: string;
  tenant_id: string;
  enabled_modules: Record<string, boolean>;
  autonomy_levels: Record<string, number>;
  llm_temperature: number;
  llm_model: string;
  stt_model: string;
  tts_voice: string;
  telephony_config: {
    asterisk_ami_host: string;
    asterisk_ami_port: number;
    working_hours: { start: string; end: string };
    overflow_threshold: number;
    appointment_duration_minutes: number;
    max_wait_days: number;
    use_travel_time: boolean;
    travel_buffer_minutes: number;
  };
  integrations: Record<string, string | null>;
}

const MODULE_LABELS: Record<string, string> = {
  telephonie: 'Telephonie',
  marketing: 'Marketing',
  seo: 'SEO & Contenu',
  commercial: 'Commercial',
  comptabilite: 'Comptabilite',
  juridique: 'Juridique',
  recrutement: 'Recrutement',
  support: 'Support Client',
  orchestration: 'Orchestration',
};

export function MarceauSettings() {
  const [config, setConfig] = useState<MarceauConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const response = await api.get<MarceauConfig>('/v3/marceau/config');
      setConfig(response.data);
      setError(null);
    } catch (e: any) {
      setError(e.message || 'Erreur chargement configuration');
    } finally {
      setLoading(false);
    }
  };

  const saveConfig = async () => {
    if (!config) return;
    setSaving(true);
    setError(null);
    setSuccess(null);

    try {
      await api.patch('/v3/marceau/config', {
        enabled_modules: config.enabled_modules,
        autonomy_levels: config.autonomy_levels,
        llm_temperature: config.llm_temperature,
        llm_model: config.llm_model,
        stt_model: config.stt_model,
        tts_voice: config.tts_voice,
        telephony_config: config.telephony_config,
        integrations: config.integrations,
      });
      setSuccess('Configuration sauvegardee avec succes');
      setTimeout(() => setSuccess(null), 3000);
    } catch (e: any) {
      setError(e.message || 'Erreur sauvegarde');
    } finally {
      setSaving(false);
    }
  };

  const resetConfig = async () => {
    if (!confirm('Reinitialiser la configuration aux valeurs par defaut ?')) return;

    try {
      const response = await api.post<MarceauConfig>('/v3/marceau/config/reset', {});
      setConfig(response.data);
      setSuccess('Configuration reinitialisee');
    } catch (e: any) {
      setError(e.message || 'Erreur reinitialisation');
    }
  };

  const toggleModule = (module: string) => {
    if (!config) return;
    setConfig({
      ...config,
      enabled_modules: {
        ...config.enabled_modules,
        [module]: !config.enabled_modules[module],
      },
    });
  };

  const updateAutonomy = (module: string, value: number) => {
    if (!config) return;
    setConfig({
      ...config,
      autonomy_levels: {
        ...config.autonomy_levels,
        [module]: value,
      },
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
      </div>
    );
  }

  if (!config) return null;

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'telephonie', label: 'Telephonie', icon: Phone },
    { id: 'integrations', label: 'Integrations', icon: Share2 },
    { id: 'ia', label: 'IA', icon: Brain },
  ];

  return (
    <div className="space-y-6">
      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700 flex items-center gap-2">
          <AlertCircle size={16} />
          {error}
        </div>
      )}
      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-700 flex items-center gap-2">
          <Check size={16} />
          {success}
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex gap-4">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              <tab.icon size={16} />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {activeTab === 'general' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Modules actives</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(MODULE_LABELS).map(([key, label]) => (
                <div key={key} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium">{label}</span>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={config.enabled_modules[key] || false}
                        onChange={() => toggleModule(key)}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-gray-200 peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
                  </div>
                  {config.enabled_modules[key] && (
                    <div>
                      <label className="text-sm text-gray-500">
                        Autonomie: {config.autonomy_levels[key] || 100}%
                      </label>
                      <input
                        type="range"
                        min="0"
                        max="100"
                        step="10"
                        value={config.autonomy_levels[key] || 100}
                        onChange={(e) => updateAutonomy(key, parseInt(e.target.value))}
                        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                      />
                      <div className="flex justify-between text-xs text-gray-400">
                        <span>Validation manuelle</span>
                        <span>100% autonome</span>
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'telephonie' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Configuration Telephonie</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Horaires de travail
                </label>
                <div className="flex gap-2 items-center">
                  <input
                    type="time"
                    value={config.telephony_config.working_hours.start}
                    onChange={(e) => setConfig({
                      ...config,
                      telephony_config: {
                        ...config.telephony_config,
                        working_hours: {
                          ...config.telephony_config.working_hours,
                          start: e.target.value,
                        },
                      },
                    })}
                    className="border rounded px-3 py-2"
                  />
                  <span>a</span>
                  <input
                    type="time"
                    value={config.telephony_config.working_hours.end}
                    onChange={(e) => setConfig({
                      ...config,
                      telephony_config: {
                        ...config.telephony_config,
                        working_hours: {
                          ...config.telephony_config.working_hours,
                          end: e.target.value,
                        },
                      },
                    })}
                    className="border rounded px-3 py-2"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Seuil de debordement (appels en attente)
                </label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={config.telephony_config.overflow_threshold}
                  onChange={(e) => setConfig({
                    ...config,
                    telephony_config: {
                      ...config.telephony_config,
                      overflow_threshold: parseInt(e.target.value),
                    },
                  })}
                  className="border rounded px-3 py-2 w-24"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Duree RDV par defaut (minutes)
                </label>
                <input
                  type="number"
                  min="15"
                  max="240"
                  step="15"
                  value={config.telephony_config.appointment_duration_minutes}
                  onChange={(e) => setConfig({
                    ...config,
                    telephony_config: {
                      ...config.telephony_config,
                      appointment_duration_minutes: parseInt(e.target.value),
                    },
                  })}
                  className="border rounded px-3 py-2 w-24"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Delai max RDV (jours)
                </label>
                <input
                  type="number"
                  min="1"
                  max="60"
                  value={config.telephony_config.max_wait_days}
                  onChange={(e) => setConfig({
                    ...config,
                    telephony_config: {
                      ...config.telephony_config,
                      max_wait_days: parseInt(e.target.value),
                    },
                  })}
                  className="border rounded px-3 py-2 w-24"
                />
              </div>

              <div className="col-span-2">
                <label className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.telephony_config.use_travel_time}
                    onChange={(e) => setConfig({
                      ...config,
                      telephony_config: {
                        ...config.telephony_config,
                        use_travel_time: e.target.checked,
                      },
                    })}
                    className="rounded"
                  />
                  <span className="text-sm">Inclure temps de trajet dans le planning</span>
                </label>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'integrations' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Integrations externes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  OpenRouteService API Key
                </label>
                <input
                  type="password"
                  value={config.integrations.ors_api_key || ''}
                  onChange={(e) => setConfig({
                    ...config,
                    integrations: {
                      ...config.integrations,
                      ors_api_key: e.target.value || null,
                    },
                  })}
                  placeholder="Cle API pour geocodage et calcul trajet"
                  className="border rounded px-3 py-2 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  WordPress URL
                </label>
                <input
                  type="url"
                  value={config.integrations.wordpress_url || ''}
                  onChange={(e) => setConfig({
                    ...config,
                    integrations: {
                      ...config.integrations,
                      wordpress_url: e.target.value || null,
                    },
                  })}
                  placeholder="https://votre-site.com"
                  className="border rounded px-3 py-2 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Slack Webhook URL
                </label>
                <input
                  type="url"
                  value={config.integrations.slack_webhook || ''}
                  onChange={(e) => setConfig({
                    ...config,
                    integrations: {
                      ...config.integrations,
                      slack_webhook: e.target.value || null,
                    },
                  })}
                  placeholder="https://hooks.slack.com/..."
                  className="border rounded px-3 py-2 w-full"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  HubSpot API Key
                </label>
                <input
                  type="password"
                  value={config.integrations.hubspot_api_key || ''}
                  onChange={(e) => setConfig({
                    ...config,
                    integrations: {
                      ...config.integrations,
                      hubspot_api_key: e.target.value || null,
                    },
                  })}
                  placeholder="Cle API HubSpot"
                  className="border rounded px-3 py-2 w-full"
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === 'ia' && (
          <div className="space-y-6">
            <h3 className="text-lg font-semibold">Configuration IA</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Modele LLM
                </label>
                <select
                  value={config.llm_model}
                  onChange={(e) => setConfig({ ...config, llm_model: e.target.value })}
                  className="border rounded px-3 py-2 w-full"
                >
                  <option value="llama3-8b-instruct">Llama 3 8B Instruct</option>
                  <option value="llama3-70b-instruct">Llama 3 70B Instruct</option>
                  <option value="mistral-7b-instruct">Mistral 7B Instruct</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Temperature: {config.llm_temperature}
                </label>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                  value={config.llm_temperature}
                  onChange={(e) => setConfig({ ...config, llm_temperature: parseFloat(e.target.value) })}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-gray-400">
                  <span>Precis</span>
                  <span>Creatif</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Modele STT (Speech-to-Text)
                </label>
                <select
                  value={config.stt_model}
                  onChange={(e) => setConfig({ ...config, stt_model: e.target.value })}
                  className="border rounded px-3 py-2 w-full"
                >
                  <option value="whisper-small">Whisper Small</option>
                  <option value="whisper-medium">Whisper Medium</option>
                  <option value="whisper-large">Whisper Large</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Voix TTS (Text-to-Speech)
                </label>
                <select
                  value={config.tts_voice}
                  onChange={(e) => setConfig({ ...config, tts_voice: e.target.value })}
                  className="border rounded px-3 py-2 w-full"
                >
                  <option value="fr_FR-sise-medium">Francais - Sise (Medium)</option>
                  <option value="fr_FR-male-1">Francais - Male 1</option>
                  <option value="fr_FR-upmc-medium">Francais - UPMC (Medium)</option>
                </select>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Actions */}
      <div className="flex justify-end gap-3">
        <button
          onClick={resetConfig}
          className="flex items-center gap-2 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
        >
          <RefreshCw size={16} />
          Reinitialiser
        </button>
        <button
          onClick={saveConfig}
          disabled={saving}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? (
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
          ) : (
            <Save size={16} />
          )}
          Sauvegarder
        </button>
      </div>
    </div>
  );
}
