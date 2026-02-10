/**
 * AZALSCORE - Gestion des Permissions (Ultra Simple)
 */

import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Users, Shield, Check, Save, Search } from 'lucide-react';
import { api } from '@core/api-client';

// Liste des modules et leurs permissions
const MODULES = [
  { id: 'projects', name: 'Affaires', perms: ['view', 'create', 'edit', 'delete'] },
  { id: 'partners', name: 'Clients', perms: ['view', 'create', 'edit', 'delete'] },
  { id: 'invoicing', name: 'Facturation', perms: ['view', 'create', 'edit', 'delete', 'validate'] },
  { id: 'inventory', name: 'Stock', perms: ['view', 'create', 'edit', 'delete'] },
  { id: 'accounting', name: 'Comptabilité', perms: ['view', 'create', 'edit', 'validate'] },
  { id: 'hr', name: 'RH', perms: ['view', 'create', 'edit', 'delete'] },
  { id: 'admin', name: 'Admin', perms: ['view', 'users', 'settings'] },
];

const PERM_LABELS: Record<string, string> = {
  view: 'Voir', create: 'Créer', edit: 'Modifier',
  delete: 'Supprimer', validate: 'Valider', users: 'Utilisateurs', settings: 'Paramètres',
};

export const PermissionsManager: React.FC = () => {
  const qc = useQueryClient();
  const [userId, setUserId] = useState<string>();
  const [search, setSearch] = useState('');
  const [perms, setPerms] = useState<string[]>([]);
  const [saved, setSaved] = useState(false);

  // Charger utilisateurs
  const { data: users = [] } = useQuery({
    queryKey: ['iam-users'],
    queryFn: async () => {
      try {
        const r = await api.get('/v1/iam/users?page_size=100', {
          headers: { 'X-Silent-Error': 'true' }
        });
        // Gérer les deux formats possibles
        const data = r && typeof r === 'object' && 'data' in r ? (r as any).data : r;
        return data?.items || [];
      } catch {
        return [];
      }
    },
  });

  // Charger permissions de l'utilisateur sélectionné
  const { data: serverPerms } = useQuery({
    queryKey: ['perms', userId],
    queryFn: async () => {
      try {
        const r = await api.get(`/v1/iam/users/${userId}/permissions`, {
          headers: { 'X-Silent-Error': 'true' }
        });
        // L'API retourne directement un tableau de permissions
        if (Array.isArray(r)) return r;
        const data = r && typeof r === 'object' && 'data' in r ? (r as any).data : r;
        return Array.isArray(data) ? data : (data?.capabilities || []);
      } catch {
        return [];
      }
    },
    enabled: !!userId,
  });

  // Sauvegarder
  const saveMutation = useMutation({
    mutationFn: () => api.put(`/v1/iam/users/${userId}/permissions`, { capabilities: perms }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['perms', userId] }); setSaved(true); setTimeout(() => setSaved(false), 2000); },
  });

  // Sync avec serveur
  useEffect(() => { if (serverPerms) setPerms(serverPerms); }, [serverPerms]);

  // Filtrer utilisateurs
  const filtered = users.filter((u: any) =>
    !search || u.email?.toLowerCase().includes(search.toLowerCase()) ||
    u.first_name?.toLowerCase().includes(search.toLowerCase())
  );

  const user = users.find((u: any) => u.id === userId);

  // Toggle permission
  const toggle = (cap: string) => {
    setPerms(p => p.includes(cap) ? p.filter(x => x !== cap) : [...p, cap]);
  };

  return (
    <div className="azals-pm">
      {/* Liste utilisateurs */}
      <div className="azals-pm-users">
        <div className="azals-pm-users__header"><Users size={18} /> Utilisateurs</div>
        <div className="azals-pm-users__search">
          <Search size={16} />
          <input placeholder="Rechercher..." value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <div className="azals-pm-users__list" role="listbox" aria-label="Liste des utilisateurs">
          {filtered.map((u: any) => (
            <div
              key={u.id}
              role="option"
              tabIndex={0}
              aria-selected={userId === u.id}
              className={`azals-pm-users__item ${userId === u.id ? 'azals-pm-users__item--active' : ''}`}
              onClick={() => setUserId(u.id)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  setUserId(u.id);
                }
              }}
            >
              <strong>{u.first_name} {u.last_name}</strong>
              <span>{u.email}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Grille permissions */}
      {user ? (
        <div className="azals-pm-grid">
          <div className="azals-pm-grid__header">
            <Shield size={18} /> Permissions: {user.first_name} {user.last_name}
          </div>
          <div className="azals-pm-grid__modules">
            {MODULES.map(m => (
              <div key={m.id} className="azals-pm-module">
                <div className="azals-pm-module__header">{m.name}</div>
                <div className="azals-pm-module__perms">
                  {m.perms.map(p => (
                    <label key={p} className="azals-pm-perm">
                      <input
                        type="checkbox"
                        checked={perms.includes(`${m.id}.${p}`)}
                        onChange={() => toggle(`${m.id}.${p}`)}
                      />
                      {PERM_LABELS[p] || p}
                    </label>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="azals-pm-grid__actions">
            <button className={`azals-pm-save ${saved ? 'azals-pm-save--success' : ''}`} onClick={() => saveMutation.mutate()}>
              {saved ? <><Check size={16} /> OK</> : <><Save size={16} /> Enregistrer</>}
            </button>
          </div>
        </div>
      ) : (
        <div className="azals-pm-empty">
          <Shield size={48} />
          <p>Sélectionnez un utilisateur</p>
        </div>
      )}
    </div>
  );
};

export default PermissionsManager;
