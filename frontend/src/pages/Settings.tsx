/**
 * AZALSCORE - Page Paramètres
 */

import React from 'react';
import { useUIStore } from '@ui/states';
import { PageWrapper, Card, Grid } from '@ui/layout';
import { Button } from '@ui/actions';

const SettingsPage: React.FC = () => {
  const { theme, setTheme } = useUIStore();

  return (
    <PageWrapper title="Paramètres">
      <Grid cols={2} gap="md">
        <Card title="Apparence">
          <div className="azals-settings__option">
            <label>Thème</label>
            <select
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
            <label>Notifications par email</label>
            <input type="checkbox" className="azals-checkbox" defaultChecked />
          </div>
          <div className="azals-settings__option">
            <label>Notifications push</label>
            <input type="checkbox" className="azals-checkbox" defaultChecked />
          </div>
          <div className="azals-settings__option">
            <label>Alertes RED uniquement</label>
            <input type="checkbox" className="azals-checkbox" />
          </div>
        </Card>

        <Card title="Langue et région">
          <div className="azals-settings__option">
            <label>Langue</label>
            <select className="azals-select" defaultValue="fr">
              <option value="fr">Français</option>
              <option value="en">English</option>
            </select>
          </div>
          <div className="azals-settings__option">
            <label>Fuseau horaire</label>
            <select className="azals-select" defaultValue="Europe/Paris">
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
