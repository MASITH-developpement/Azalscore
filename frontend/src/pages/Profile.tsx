/**
 * AZALSCORE - Page Profil Utilisateur
 */

import React from 'react';
import { useUser } from '@core/auth';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';

const ProfilePage: React.FC = () => {
  const user = useUser();

  return (
    <PageWrapper title="Mon Profil">
      <Grid cols={2} gap="md">
        <Card title="Informations personnelles">
          <div className="azals-profile__info">
            <div className="azals-profile__field">
              <span className="azals-profile__label">Nom</span>
              <span>{user?.name}</span>
            </div>
            <div className="azals-profile__field">
              <span className="azals-profile__label">Email</span>
              <span>{user?.email}</span>
            </div>
            <div className="azals-profile__field">
              <span className="azals-profile__label">Rôles</span>
              <span>{user?.roles.join(', ')}</span>
            </div>
            <div className="azals-profile__field">
              <span className="azals-profile__label">Dernière connexion</span>
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
