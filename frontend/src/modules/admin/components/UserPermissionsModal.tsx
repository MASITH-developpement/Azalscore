/**
 * AZALSCORE Module - Admin - UserPermissionsModal
 * Modal de gestion des permissions utilisateur par module
 */

import React, { useState, useEffect } from 'react';
import { useAuth } from '@core/auth';
import { useCapabilitiesStore } from '@core/capabilities';
import { Button, Modal } from '@ui/actions';
import { useCapabilitiesByModule, useUserPermissions, useUpdateUserPermissions } from '../hooks';

interface User {
  id: string;
  username: string;
  first_name?: string;
  last_name?: string;
}

interface UserPermissionsModalProps {
  isOpen: boolean;
  user: User | null;
  onClose: () => void;
}

const UserPermissionsModal: React.FC<UserPermissionsModalProps> = ({ isOpen, user, onClose }) => {
  const { data: modulesCaps = {}, isLoading: loadingModules, error: modulesError } = useCapabilitiesByModule();
  const { data: userPerms = [], isLoading: loadingPerms } = useUserPermissions(user?.id);
  const updatePermissions = useUpdateUserPermissions();

  const refreshCapabilities = useCapabilitiesStore((state) => state.refreshCapabilities);
  const { user: _currentUser } = useAuth();

  const [selectedCaps, setSelectedCaps] = useState<Set<string>>(new Set());
  const [expandedModules, setExpandedModules] = useState<Set<string>>(new Set());
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    if (modulesError) console.error('[UserPermissionsModal] Error:', modulesError);
  }, [modulesCaps, userPerms, modulesError]);

  useEffect(() => {
    if (userPerms.length > 0) {
      setSelectedCaps(new Set(userPerms));
    } else {
      setSelectedCaps(new Set());
    }
  }, [userPerms, user?.id]);

  const toggleCapability = (code: string) => {
    setSelectedCaps(prev => {
      const next = new Set(prev);
      if (next.has(code)) {
        next.delete(code);
      } else {
        next.add(code);
      }
      return next;
    });
  };

  const toggleModule = (moduleKey: string) => {
    const module = modulesCaps[moduleKey];
    if (!module) return;

    const moduleCodes = module.capabilities.map(c => c.code);
    const allSelected = moduleCodes.every(c => selectedCaps.has(c));

    setSelectedCaps(prev => {
      const next = new Set(prev);
      if (allSelected) {
        moduleCodes.forEach(c => next.delete(c));
      } else {
        moduleCodes.forEach(c => next.add(c));
      }
      return next;
    });
  };

  const toggleExpandModule = (moduleKey: string) => {
    setExpandedModules(prev => {
      const next = new Set(prev);
      if (next.has(moduleKey)) {
        next.delete(moduleKey);
      } else {
        next.add(moduleKey);
      }
      return next;
    });
  };

  const expandAll = () => setExpandedModules(new Set(Object.keys(modulesCaps)));
  const collapseAll = () => setExpandedModules(new Set());
  const selectAll = () => {
    const allCodes = Object.values(modulesCaps).flatMap(m => m.capabilities.map(c => c.code));
    setSelectedCaps(new Set(allCodes));
  };
  const deselectAll = () => setSelectedCaps(new Set());

  const handleSave = async () => {
    if (!user) return;
    await updatePermissions.mutateAsync({
      userId: user.id,
      capabilities: Array.from(selectedCaps)
    });
    await refreshCapabilities();
    onClose();
  };

  const filteredModules = Object.entries(modulesCaps).filter(([, module]) => {
    if (!searchTerm) return true;
    const term = searchTerm.toLowerCase();
    if (module.name.toLowerCase().includes(term)) return true;
    return module.capabilities.some(c =>
      c.name.toLowerCase().includes(term) ||
      c.code.toLowerCase().includes(term)
    );
  });

  const totalCaps = Object.values(modulesCaps).reduce((acc, m) => acc + m.capabilities.length, 0);
  const selectedCount = selectedCaps.size;

  if (!isOpen || !user) return null;

  const isLoading = loadingModules || loadingPerms;
  const hasModules = Object.keys(modulesCaps).length > 0;

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Acces modules: ${user.first_name || ''} ${user.last_name || user.username}`.trim()}
    >
      <div style={{ minWidth: '600px' }}>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          gap: '12px',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--azals-border)',
          paddingBottom: '12px',
          marginBottom: '12px'
        }}>
          <input
            type="text"
            className="azals-input"
            style={{ width: '200px', padding: '8px 12px', fontSize: '14px' }}
            placeholder="Rechercher..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
          <div style={{ display: 'flex', gap: '8px', fontSize: '13px' }}>
            <button type="button" onClick={expandAll} style={{ background: 'none', border: 'none', color: 'var(--azals-primary)', cursor: 'pointer' }}>
              Tout deplier
            </button>
            <span style={{ color: 'var(--azals-border)' }}>|</span>
            <button type="button" onClick={collapseAll} style={{ background: 'none', border: 'none', color: 'var(--azals-primary)', cursor: 'pointer' }}>
              Tout replier
            </button>
            <span style={{ color: 'var(--azals-border)' }}>|</span>
            <button type="button" onClick={selectAll} style={{ background: 'none', border: 'none', color: 'var(--azals-success)', cursor: 'pointer' }}>
              Tout activer
            </button>
            <span style={{ color: 'var(--azals-border)' }}>|</span>
            <button type="button" onClick={deselectAll} style={{ background: 'none', border: 'none', color: 'var(--azals-danger)', cursor: 'pointer' }}>
              Tout desactiver
            </button>
          </div>
        </div>

        <div style={{ fontSize: '14px', color: 'var(--azals-text-muted)', marginBottom: '12px' }}>
          <strong style={{ color: 'var(--azals-primary)' }}>{selectedCount}</strong> / {totalCaps} permissions actives
        </div>

        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--azals-text-muted)' }}>
            Chargement des modules...
          </div>
        ) : modulesError ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--azals-danger)' }}>
            <p>Erreur lors du chargement des modules</p>
            <p style={{ fontSize: '12px', marginTop: '8px', color: 'var(--azals-text-muted)' }}>
              {String((modulesError as Error)?.message || modulesError)}
            </p>
          </div>
        ) : !hasModules ? (
          <div style={{ textAlign: 'center', padding: '40px', color: 'var(--azals-text-muted)' }}>
            <p>Aucun module disponible.</p>
          </div>
        ) : (
          <div style={{
            maxHeight: '400px',
            overflowY: 'auto',
            border: '1px solid var(--azals-border)',
            borderRadius: 'var(--azals-radius)'
          }}>
            {filteredModules.map(([moduleKey, module]) => {
              const moduleCodes = module.capabilities.map(c => c.code);
              const selectedInModule = moduleCodes.filter(c => selectedCaps.has(c)).length;
              const allSelected = selectedInModule === moduleCodes.length && moduleCodes.length > 0;
              const someSelected = selectedInModule > 0 && !allSelected;
              const isExpanded = expandedModules.has(moduleKey);

              return (
                <div key={moduleKey} style={{ borderBottom: '1px solid var(--azals-border-light)' }}>
                  <div
                    onClick={() => toggleExpandModule(moduleKey)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '12px 16px',
                      background: 'var(--azals-bg)',
                      cursor: 'pointer'
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={(el) => { if (el) el.indeterminate = someSelected; }}
                      onChange={(e) => {
                        e.stopPropagation();
                        toggleModule(moduleKey);
                      }}
                      onClick={(e) => e.stopPropagation()}
                      style={{ width: '16px', height: '16px', accentColor: 'var(--azals-primary)' }}
                    />
                    <span style={{ fontWeight: 500, flex: 1 }}>{module.name}</span>
                    <span className="azals-badge azals-badge--blue" style={{ fontSize: '11px' }}>
                      {selectedInModule}/{moduleCodes.length}
                    </span>
                    <span style={{ color: 'var(--azals-text-muted)', fontSize: '12px' }}>
                      {isExpanded ? '▼' : '▶'}
                    </span>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: '8px 16px 8px 44px', background: 'var(--azals-surface)' }}>
                      {module.capabilities
                        .filter(cap => {
                          if (!searchTerm) return true;
                          const term = searchTerm.toLowerCase();
                          return cap.name.toLowerCase().includes(term) ||
                                 cap.code.toLowerCase().includes(term);
                        })
                        .map(cap => (
                          <label
                            key={cap.code}
                            aria-label={cap.name}
                            style={{
                              display: 'flex',
                              alignItems: 'flex-start',
                              gap: '10px',
                              padding: '8px',
                              borderRadius: 'var(--azals-radius)',
                              cursor: 'pointer'
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={selectedCaps.has(cap.code)}
                              onChange={() => toggleCapability(cap.code)}
                              style={{ width: '14px', height: '14px', marginTop: '2px', accentColor: 'var(--azals-primary)' }}
                            />
                            <div style={{ flex: 1, minWidth: 0 }}>
                              <div style={{ fontWeight: 500, fontSize: '13px' }}>{cap.name}</div>
                              <div style={{ fontSize: '12px', color: 'var(--azals-text-muted)' }}>{cap.description}</div>
                              <code style={{ fontSize: '11px', color: 'var(--azals-text-light)' }}>{cap.code}</code>
                            </div>
                          </label>
                        ))}
                    </div>
                  )}
                </div>
              );
            })}

            {filteredModules.length === 0 && hasModules && (
              <div style={{ padding: '40px', textAlign: 'center', color: 'var(--azals-text-muted)' }}>
                Aucun module trouve pour &quot;{searchTerm}&quot;
              </div>
            )}
          </div>
        )}

        <div style={{
          display: 'flex',
          justifyContent: 'flex-end',
          gap: '8px',
          paddingTop: '16px',
          marginTop: '16px',
          borderTop: '1px solid var(--azals-border)'
        }}>
          <Button variant="secondary" onClick={onClose}>
            Annuler
          </Button>
          <Button
            onClick={handleSave}
            isLoading={updatePermissions.isPending}
            disabled={!hasModules}
          >
            Enregistrer ({selectedCount})
          </Button>
        </div>
      </div>
    </Modal>
  );
};

export default UserPermissionsModal;
