/**
 * AZALSCORE Module - Country Packs France - Dashboard View
 * Vue d'ensemble avec statistiques et actions rapides
 */

import React from 'react';
import { BookOpen, FileText, Euro, Users, Shield, AlertTriangle, Clock, FileSearch } from 'lucide-react';
import { Button } from '@ui/actions';
import { LoadingState } from '@ui/components/StateViews';
import { StatCard } from '@ui/dashboards';
import { Card, Grid } from '@ui/layout';
import { useFrancePackStats } from '../hooks';
import { Badge } from './LocalComponents';

interface DashboardViewProps {
  onNavigate: (view: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const { data: stats, isLoading } = useFrancePackStats();

  if (isLoading) {
    return <LoadingState message="Chargement des statistiques..." />;
  }

  return (
    <div className="space-y-4">
      <Grid cols={4}>
        <StatCard
          title="Comptes PCG"
          value={String(stats?.pcg_accounts_count || 0)}
          icon={<BookOpen size={20} />}
          variant="default"
          onClick={() => onNavigate('pcg')}
        />
        <StatCard
          title="Declarations TVA en attente"
          value={String(stats?.vat_declarations_pending || 0)}
          icon={<Clock size={20} />}
          variant={stats?.vat_declarations_pending ? 'warning' : 'success'}
        />
        <StatCard
          title="FEC (exercice)"
          value={String(stats?.fec_exports_this_year || 0)}
          icon={<FileText size={20} />}
          variant="default"
          onClick={() => onNavigate('fec')}
        />
        <StatCard
          title="Demandes RGPD en attente"
          value={String(stats?.rgpd_requests_pending || 0)}
          icon={<FileSearch size={20} />}
          variant={stats?.rgpd_requests_pending ? 'warning' : 'success'}
        />
      </Grid>

      <Grid cols={4}>
        <StatCard
          title="Derniere DSN"
          value={stats?.dsn_last_submitted ? new Date(stats.dsn_last_submitted).toLocaleDateString('fr-FR') : 'Aucune'}
          icon={<Users size={20} />}
          variant="default"
          onClick={() => onNavigate('dsn')}
        />
        <StatCard
          title="Violations RGPD ouvertes"
          value={String(stats?.rgpd_breaches_open || 0)}
          icon={<AlertTriangle size={20} />}
          variant={stats?.rgpd_breaches_open ? 'danger' : 'success'}
        />
        <StatCard
          title="TVA"
          value="5 taux"
          icon={<Euro size={20} />}
          variant="default"
          onClick={() => onNavigate('tva')}
        />
        <StatCard
          title="RGPD"
          value="Conforme"
          icon={<Shield size={20} />}
          variant="success"
          onClick={() => onNavigate('rgpd')}
        />
      </Grid>

      <Grid cols={2}>
        <Card>
          <h3 className="text-lg font-semibold mb-4">Conformite France</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span>Plan Comptable General (PCG 2024)</span>
              <Badge color="green">Active</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>TVA francaise</span>
              <Badge color="green">5 taux configures</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>FEC (Article L47 A-I du LPF)</span>
              <Badge color="green">Conforme</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>DSN (Declaration Sociale Nominative)</span>
              <Badge color="green">Active</Badge>
            </div>
            <div className="flex justify-between items-center">
              <span>RGPD (Reglement General sur la Protection des Donnees)</span>
              <Badge color="green">Conforme</Badge>
            </div>
          </div>
        </Card>

        <Card>
          <h3 className="text-lg font-semibold mb-4">Actions rapides</h3>
          <div className="space-y-2">
            <Button className="w-full justify-start" variant="secondary" onClick={() => onNavigate('fec')}>
              <FileText size={16} className="mr-2" />
              Generer un FEC
            </Button>
            <Button className="w-full justify-start" variant="secondary" onClick={() => onNavigate('tva')}>
              <Euro size={16} className="mr-2" />
              Nouvelle declaration TVA
            </Button>
            <Button className="w-full justify-start" variant="secondary" onClick={() => onNavigate('dsn')}>
              <Users size={16} className="mr-2" />
              Preparer la DSN mensuelle
            </Button>
            <Button className="w-full justify-start" variant="secondary" onClick={() => onNavigate('rgpd')}>
              <Shield size={16} className="mr-2" />
              Gerer les demandes RGPD
            </Button>
          </div>
        </Card>
      </Grid>
    </div>
  );
};

export default DashboardView;
