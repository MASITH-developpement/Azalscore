/**
 * AZALSCORE - Page Profil Utilisateur
 */

import React from 'react';
import { useUser } from '@core/auth';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';

const ProfilePage: React.FC = () => {
  const user = useUser();

  return (
    <PageWrapper title="Mon Profil">
      <Grid cols={2} gap="md">
        <Card title="Informations personnelles">
          <div className="azals-profile__info">
            <div className="azals-profile__field">
              <label>Nom</label>
              <span>{user?.name}</span>
            </div>
            <div className="azals-profile__field">
              <label>Email</label>
              <span>{user?.email}</span>
            </div>
            <div className="azals-profile__field">
              <label>Rôles</label>
              <span>{user?.roles.join(', ')}</span>
            </div>
            <div className="azals-profile__field">
              <label>Dernière connexion</label>
              <span>{user?.last_login ? new Date(user.last_login).toLocaleString('fr-FR') : 'N/A'}</span>
            </div>
          </div>
          <div className="azals-mt-4">
            <Button variant="secondary">Modifier mes informations</Button>
          </div>
        </Card>

        <Card title="Sécurité">
          <div className="azals-profile__security">
            <div className="azals-profile__security-item">
              <span>Mot de passe</span>
              <Button variant="ghost" size="sm">Modifier</Button>
            </div>
            <div className="azals-profile__security-item">
              <span>Authentification 2FA</span>
              <span className={user?.requires_2fa ? 'azals-badge azals-badge--green' : 'azals-badge azals-badge--orange'}>
                {user?.requires_2fa ? 'Activée' : 'Désactivée'}
              </span>
            </div>
          </div>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

export default ProfilePage;
