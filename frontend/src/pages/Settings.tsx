/**
 * AZALSCORE - Page Paramètres
 */

import React from 'react';
import { Button } from '@ui/actions';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { useUIStore } from '@ui/states';

const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useUIStore();

  return (
    <PageWrapper title="Paramètres">
      <Grid cols={2} gap="md">
        <Card title="Apparence">
          <div className="azals-settings__option">
            <label htmlFor="setting-theme">Thème</label>
            <select
              id="setting-theme"
              value={theme}
              onChange={(e) => setTheme(e.target.value as 'light' | 'dark' | 'system')}
              className="azals-select"
            >
              <option value="system">Système</option>
              <option value="light">Clair</option>
              <option value="dark">Sombre</option>
            </select>
          </div>
        </Card>

        <Card title="Notifications">
          <div className="azals-settings__option">
            <label htmlFor="setting-notif-email">Notifications par email</label>
            <input id="setting-notif-email" type="checkbox" className="azals-checkbox" defaultChecked />
          </div>
          <div className="azals-settings__option">
            <label htmlFor="setting-notif-push">Notifications push</label>
            <input id="setting-notif-push" type="checkbox" className="azals-checkbox" defaultChecked />
          </div>
          <div className="azals-settings__option">
            <label htmlFor="setting-alert-red">Alertes RED uniquement</label>
            <input id="setting-alert-red" type="checkbox" className="azals-checkbox" />
          </div>
        </Card>

        <Card title="Langue et région">
          <div className="azals-settings__option">
            <label htmlFor="setting-lang">Langue</label>
            <select id="setting-lang" className="azals-select" defaultValue="fr">
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>
          </div>
          <div className="azals-settings__option">
            <label htmlFor="setting-timezone">Fuseau horaire</label>
            <select id="setting-timezone" className="azals-select" defaultValue="Europe/Paris">
              <option value="Europe/Paris">Europe/Paris (UTC+1)</option>
              <option value="UTC">UTC</option>
            </select>
          </div>
        </Card>

        <Card title="Données">
          <p className="azals-text--muted">Gérez vos préférences de données et exportations.</p>
          <div className="azals-mt-4">
            <Button variant="secondary">Exporter mes données</Button>
          </div>
        </Card>
      </Grid>
    </PageWrapper>
  );
};

export default SettingsPage;
