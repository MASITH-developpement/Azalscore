/**
 * AZALSCORE - Module Profil Utilisateur
 * Gestion du profil utilisateur
 */

import React, { useState, useEffect, useRef } from 'react';
import { Key, ShieldCheck, Smartphone, User, Save, Edit, X, Loader2, Check, Camera, Copy, RefreshCw, Eye, EyeOff } from 'lucide-react';
import { MainLayout } from '@/ui-engine/layouts/MainLayout';
import { useAuth } from '@/core/auth';
import {
  profileKeys,
  useProfile,
  useUpdateProfile,
  useGenerateApiToken,
  type UserProfile,
} from './hooks';

export default function ProfileModule() {
  const { user: authUser } = useAuth();

  // React Query hooks
  const { data: profileData } = useProfile();
  const updateProfile = useUpdateProfile();
  const generateApiToken = useGenerateApiToken();

  // Local state for form
  const [formData, setFormData] = useState<UserProfile>({
    name: '',
    email: '',
    phone: '',
    photo: '',
    api_token: '',
    role: 'Utilisateur',
  });

  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showToken, setShowToken] = useState(false);
  const [tokenCopied, setTokenCopied] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Synchroniser formData avec les données du profil
  useEffect(() => {
    if (profileData?.id) {
      setFormData({
        name: profileData.name || authUser?.name || 'Utilisateur',
        email: profileData.email || authUser?.email || '',
        phone: profileData.phone || '',
        photo: profileData.photo || '',
        api_token: profileData.api_token || '',
        role: profileData.role || 'Utilisateur',
      });
    } else if (authUser) {
      setFormData({
        name: authUser.name || 'Utilisateur',
        email: authUser.email || '',
        phone: '',
        photo: '',
        api_token: '',
        role: 'Utilisateur',
      });
    }
  }, [profileData, authUser]);

  // Utiliser les données du profil ou formData
  const user = profileData?.id ? {
    ...profileData,
    name: editing ? formData.name : profileData.name,
    email: editing ? formData.email : profileData.email,
    phone: editing ? formData.phone : profileData.phone,
    photo: editing ? formData.photo : profileData.photo,
  } : formData;

  const saving = updateProfile.isPending;
  const generatingToken = generateApiToken.isPending;

  // Sauvegarder le profil
  const handleSave = async () => {
    setError(null);
    try {
      await updateProfile.mutateAsync({
        name: formData.name,
        email: formData.email,
        phone: formData.phone,
        photo: formData.photo,
      });
      setSaved(true);
      setEditing(false);
      setTimeout(() => setSaved(false), 3000);
    } catch (err) {
      setError('Erreur lors de la sauvegarde du profil');
    }
  };

  // Gestion de l'upload de photo
  const handlePhotoUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    // Vérifier la taille (max 2MB)
    if (file.size > 2 * 1024 * 1024) {
      setError('La photo ne doit pas dépasser 2 Mo');
      return;
    }

    // Vérifier le type
    if (!file.type.startsWith('image/')) {
      setError('Le fichier doit être une image');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const base64 = e.target?.result as string;
      setFormData({ ...formData, photo: base64 });
    };
    reader.readAsDataURL(file);
  };

  // Copier le token API
  const copyToken = () => {
    if (user.api_token) {
      navigator.clipboard.writeText(user.api_token);
      setTokenCopied(true);
      setTimeout(() => setTokenCopied(false), 2000);
    }
  };

  // Générer un nouveau token API
  const generateToken = async () => {
    setError(null);
    try {
      const result = await generateApiToken.mutateAsync();
      if (result?.api_token) {
        setShowToken(true);
      }
    } catch (err) {
      setError('Erreur lors de la génération du token');
    }
  };

  return (
    <MainLayout title="Mon Profil">
      <div style={{ maxWidth: '800px', margin: '0 auto' }}>
        {/* Header Profil */}
        <div className="azals-card" style={{ textAlign: 'center', marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <div style={{ marginBottom: 'var(--azals-spacing-md)', position: 'relative', display: 'inline-block' }}>
              {user.photo ? (
                <img
                  src={user.photo}
                  alt="Photo de profil"
                  style={{
                    width: '96px',
                    height: '96px',
                    borderRadius: '50%',
                    objectFit: 'cover',
                    border: '3px solid var(--azals-brand-500)',
                  }}
                />
              ) : (
                <div style={{
                  width: '96px',
                  height: '96px',
                  borderRadius: '50%',
                  background: 'var(--azals-brand-100)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                }}>
                  <User size={48} style={{ color: 'var(--azals-brand-500)' }} />
                </div>
              )}
              {editing && (
                <>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handlePhotoUpload}
                    style={{ display: 'none' }}
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    style={{
                      position: 'absolute',
                      bottom: '0',
                      right: '0',
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      background: 'var(--azals-brand-500)',
                      color: 'white',
                      border: 'none',
                      cursor: 'pointer',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                    }}
                    title="Changer la photo"
                  >
                    <Camera size={16} />
                  </button>
                </>
              )}
            </div>
            <h1 className="azals-card__title" style={{ fontSize: 'var(--azals-font-size-2xl)' }}>
              {user.name}
            </h1>
            <p className="text-muted" style={{ marginBottom: 'var(--azals-spacing-sm)' }}>
              {user.email}
            </p>
            <span className="azals-badge azals-badge--blue">
              {user.role}
            </span>
          </div>
        </div>

        {/* Informations Personnelles */}
        <div className="azals-card" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <div className="flex justify-between items-center" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              <h2 className="azals-card__title">
                Informations Personnelles
              </h2>
              <button
                className={`azals-btn azals-btn--sm ${editing ? 'azals-btn--ghost' : 'azals-btn--primary'}`}
                onClick={() => setEditing(!editing)}
              >
                {editing ? <><X size={16} /> Annuler</> : <><Edit size={16} /> Modifier</>}
              </button>
            </div>

            <div style={{ display: 'grid', gap: 'var(--azals-spacing-md)' }}>
              <div className="azals-form-field">
                <label htmlFor="profile-name">Nom complet</label>
                {editing ? (
                  <input
                    id="profile-name"
                    type="text"
                    className="azals-input"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                ) : (
                  <p id="profile-name">{user.name}</p>
                )}
              </div>

              <div className="azals-form-field">
                <label htmlFor="profile-email">Email</label>
                {editing ? (
                  <input
                    id="profile-email"
                    type="email"
                    className="azals-input"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                ) : (
                  <p id="profile-email">{user.email}</p>
                )}
              </div>

              <div className="azals-form-field">
                <label htmlFor="profile-phone">Téléphone</label>
                {editing ? (
                  <input
                    id="profile-phone"
                    type="tel"
                    className="azals-input"
                    value={formData.phone || ''}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    placeholder="+33 6 12 34 56 78"
                  />
                ) : (
                  <p id="profile-phone">{user.phone || '-'}</p>
                )}
              </div>

              {error && (
                <div style={{
                  padding: 'var(--azals-spacing-md)',
                  background: '#fef2f2',
                  color: '#dc2626',
                  borderRadius: 'var(--azals-radius-md)',
                  marginBottom: 'var(--azals-spacing-md)'
                }}>
                  {error}
                </div>
              )}

              {saved && (
                <div style={{
                  padding: 'var(--azals-spacing-md)',
                  background: '#ecfdf5',
                  color: '#059669',
                  borderRadius: 'var(--azals-radius-md)',
                  marginBottom: 'var(--azals-spacing-md)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <Check size={16} /> Profil enregistré avec succès
                </div>
              )}

              {editing && (
                <button
                  className="azals-btn azals-btn--success"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? (
                    <><Loader2 size={16} className="animate-spin" /> Enregistrement...</>
                  ) : (
                    <><Save size={16} /> Enregistrer les modifications</>
                  )}
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Sécurité */}
        <div className="azals-card" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
          <div className="azals-card__body">
            <h2 className="azals-card__title" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              Sécurité
            </h2>

            <div style={{ display: 'grid', gap: 'var(--azals-spacing-md)' }}>
              <button className="azals-btn azals-btn--primary" style={{ justifyContent: 'flex-start' }} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'changePassword' } })); }}>
                <Key size={16} /> Changer le mot de passe
              </button>

              <button className="azals-btn azals-btn--secondary" style={{ justifyContent: 'flex-start' }} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'configure2FA' } })); }}>
                <ShieldCheck size={16} /> Configurer l'authentification à deux facteurs
              </button>

              <button className="azals-btn azals-btn--secondary" style={{ justifyContent: 'flex-start' }} onClick={() => { window.dispatchEvent(new CustomEvent('azals:action', { detail: { type: 'manageSessions' } })); }}>
                <Smartphone size={16} /> Gérer les sessions actives
              </button>
            </div>
          </div>
        </div>

        {/* Token API */}
        <div className="azals-card">
          <div className="azals-card__body">
            <h2 className="azals-card__title" style={{ marginBottom: 'var(--azals-spacing-lg)' }}>
              Token API
            </h2>
            <p className="text-muted" style={{ marginBottom: 'var(--azals-spacing-md)', fontSize: 'var(--azals-font-size-sm)' }}>
              Utilisez ce token pour accéder à l'API AZALSCORE depuis vos applications externes.
            </p>

            {user.api_token ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--azals-spacing-md)' }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 'var(--azals-spacing-sm)',
                  padding: 'var(--azals-spacing-md)',
                  background: 'var(--azals-gray-100)',
                  borderRadius: 'var(--azals-radius-md)',
                  fontFamily: 'monospace',
                  fontSize: 'var(--azals-font-size-sm)',
                }}>
                  <code style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {showToken ? user.api_token : '••••••••••••••••••••••••••••••••'}
                  </code>
                  <button
                    className="azals-btn azals-btn--ghost azals-btn--sm"
                    onClick={() => setShowToken(!showToken)}
                    title={showToken ? 'Masquer' : 'Afficher'}
                  >
                    {showToken ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                  <button
                    className="azals-btn azals-btn--ghost azals-btn--sm"
                    onClick={copyToken}
                    title="Copier"
                  >
                    {tokenCopied ? <Check size={16} style={{ color: 'var(--azals-success)' }} /> : <Copy size={16} />}
                  </button>
                </div>

                <button
                  className="azals-btn azals-btn--secondary"
                  onClick={generateToken}
                  disabled={generatingToken}
                  style={{ justifyContent: 'flex-start' }}
                >
                  {generatingToken ? (
                    <><Loader2 size={16} className="animate-spin" /> Génération...</>
                  ) : (
                    <><RefreshCw size={16} /> Régénérer le token</>
                  )}
                </button>
                <p className="text-muted" style={{ fontSize: 'var(--azals-font-size-xs)' }}>
                  Attention : la régénération invalidera l'ancien token.
                </p>
              </div>
            ) : (
              <button
                className="azals-btn azals-btn--primary"
                onClick={generateToken}
                disabled={generatingToken}
              >
                {generatingToken ? (
                  <><Loader2 size={16} className="animate-spin" /> Génération...</>
                ) : (
                  <><Key size={16} /> Générer un token API</>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </MainLayout>
  );
}

// Re-export hooks for external use
export {
  profileKeys,
  useProfile,
  useUpdateProfile,
  useGenerateApiToken,
} from './hooks';
