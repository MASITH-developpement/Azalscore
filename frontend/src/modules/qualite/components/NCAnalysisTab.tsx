/**
 * AZALSCORE Module - Qualite - NC Analysis Tab
 * Onglet analyse et actions correctives
 */

import React from 'react';
import {
  Search, CheckCircle, Shield, AlertTriangle, Target
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { NonConformance } from '../types';

/**
 * NCAnalysisTab - Analyse et actions
 */
export const NCAnalysisTab: React.FC<TabContentProps<NonConformance>> = ({ data: nc }) => {
  const hasAnalysis = nc.root_cause || nc.corrective_action || nc.preventive_action;

  if (!hasAnalysis && nc.status === 'OPEN') {
    return (
      <div className="azals-std-tab-content">
        <div className="azals-empty">
          <Search size={48} className="text-muted" />
          <h3>Analyse en attente</h3>
          <p className="text-muted">
            L'analyse de cette non-conformite n'a pas encore commence.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="azals-std-tab-content">
      {/* Cause racine */}
      <Card title="Cause racine" icon={<Search size={18} />} className="mb-4">
        {nc.root_cause ? (
          <div className="azals-analysis-content">
            <p>{nc.root_cause}</p>
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Search size={32} className="text-muted" />
            <p className="text-muted">Cause racine non identifiee</p>
            <p className="text-sm text-muted">
              Utilisez la methode des 5 pourquoi ou un diagramme d'Ishikawa.
            </p>
          </div>
        )}
      </Card>

      <Grid cols={2} gap="lg">
        {/* Action corrective */}
        <Card title="Action corrective" icon={<CheckCircle size={18} />}>
          {nc.corrective_action ? (
            <div className="azals-analysis-content">
              <p>{nc.corrective_action}</p>
              <div className="azals-analysis-status mt-4">
                <span className="azals-badge azals-badge--green">
                  <CheckCircle size={12} className="mr-1" />
                  Definie
                </span>
              </div>
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <CheckCircle size={32} className="text-muted" />
              <p className="text-muted">Aucune action corrective</p>
              <p className="text-sm text-muted">
                Action pour corriger le probleme detecte.
              </p>
            </div>
          )}
        </Card>

        {/* Action preventive */}
        <Card title="Action preventive" icon={<Shield size={18} />}>
          {nc.preventive_action ? (
            <div className="azals-analysis-content">
              <p>{nc.preventive_action}</p>
              <div className="azals-analysis-status mt-4">
                <span className="azals-badge azals-badge--blue">
                  <Shield size={12} className="mr-1" />
                  Definie
                </span>
              </div>
            </div>
          ) : (
            <div className="azals-empty azals-empty--sm">
              <Shield size={32} className="text-muted" />
              <p className="text-muted">Aucune action preventive</p>
              <p className="text-sm text-muted">
                Action pour eviter la recurrence.
              </p>
            </div>
          )}
        </Card>
      </Grid>

      {/* Guide methodologique (ERP only) */}
      <Card
        title="Guide methodologique"
        icon={<Target size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <div className="azals-methodology-guide">
          <div className="azals-methodology-step">
            <div className="azals-methodology-step__number">1</div>
            <div className="azals-methodology-step__content">
              <h4>Identifier la cause racine</h4>
              <p className="text-sm text-muted">
                Utilisez la methode des 5 pourquoi ou un diagramme d'Ishikawa (causes-effets).
              </p>
            </div>
            {nc.root_cause && <CheckCircle size={20} className="text-success" />}
          </div>

          <div className="azals-methodology-step">
            <div className="azals-methodology-step__number">2</div>
            <div className="azals-methodology-step__content">
              <h4>Definir l'action corrective</h4>
              <p className="text-sm text-muted">
                Action immediate pour corriger le probleme detecte et traiter les effets.
              </p>
            </div>
            {nc.corrective_action && <CheckCircle size={20} className="text-success" />}
          </div>

          <div className="azals-methodology-step">
            <div className="azals-methodology-step__number">3</div>
            <div className="azals-methodology-step__content">
              <h4>Definir l'action preventive</h4>
              <p className="text-sm text-muted">
                Action pour eviter que le probleme ne se reproduise (modification de processus, formation, etc.).
              </p>
            </div>
            {nc.preventive_action && <CheckCircle size={20} className="text-success" />}
          </div>

          <div className="azals-methodology-step">
            <div className="azals-methodology-step__number">4</div>
            <div className="azals-methodology-step__content">
              <h4>Verifier l'efficacite</h4>
              <p className="text-sm text-muted">
                Controler que les actions mises en place sont efficaces et cloturer la NC.
              </p>
            </div>
            {nc.status === 'CLOSED' && <CheckCircle size={20} className="text-success" />}
          </div>
        </div>
      </Card>

      {/* Alerte si pas d'action */}
      {nc.status !== 'CLOSED' && nc.status !== 'CANCELLED' && !nc.corrective_action && (
        <div className="azals-alert azals-alert--warning mt-4">
          <AlertTriangle size={18} />
          <div>
            <strong>Action requise</strong>
            <p className="text-sm">
              Une action corrective doit etre definie pour pouvoir cloturer cette non-conformite.
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default NCAnalysisTab;
