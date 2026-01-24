/**
 * AZALSCORE - Dashboard de Santé Frontend (AZA-FE-DASH)
 * ======================================================
 * Surface de gouvernance pour dirigeants/product/auditeurs
 *
 * Indicateurs obligatoires:
 * - Globaux: total modules, exposés, conformes, dégradés, bloqués
 * - Par module: statut backend/frontend, pages, routes, erreurs, conformité
 *
 * États normatifs:
 * - 🟢 Conforme
 * - 🟠 Dégradé
 * - 🔴 Non conforme
 */

import React, { useMemo } from 'react';
import { moduleRegistry, ModuleMeta } from '@/modules/registry';

// ============================================================
// TYPES
// ============================================================

type ModuleStatus = 'compliant' | 'degraded' | 'non_compliant';

interface DashboardMetrics {
  totalModules: number;
  exposedFrontend: number;
  compliant: number;
  degraded: number;
  blocked: number;
}

// ============================================================
// HELPER FUNCTIONS
// ============================================================

function getModuleStatus(meta: ModuleMeta): ModuleStatus {
  if (meta.frontend.compliance && meta.status === 'active') {
    return 'compliant';
  }
  if (meta.status === 'degraded') {
    return 'degraded';
  }
  return 'non_compliant';
}

function getStatusBadge(status: ModuleStatus): React.ReactElement {
  switch (status) {
    case 'compliant':
      return (
        <span
          style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            fontWeight: 500,
            backgroundColor: '#d1fae5',
            color: '#065f46',
          }}
        >
          🟢 Conforme
        </span>
      );
    case 'degraded':
      return (
        <span
          style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            fontWeight: 500,
            backgroundColor: '#fed7aa',
            color: '#92400e',
          }}
        >
          🟠 Dégradé
        </span>
      );
    case 'non_compliant':
      return (
        <span
          style={{
            padding: '0.25rem 0.75rem',
            borderRadius: '0.375rem',
            fontSize: '0.875rem',
            fontWeight: 500,
            backgroundColor: '#fecaca',
            color: '#991b1b',
          }}
        >
          🔴 Non conforme
        </span>
      );
  }
}

function getBooleanBadge(value: boolean): React.ReactElement {
  if (value) {
    return (
      <span
        style={{
          padding: '0.25rem 0.5rem',
          borderRadius: '0.25rem',
          fontSize: '0.75rem',
          fontWeight: 500,
          backgroundColor: '#d1fae5',
          color: '#065f46',
        }}
      >
        ✓
      </span>
    );
  }
  return (
    <span
      style={{
        padding: '0.25rem 0.5rem',
        borderRadius: '0.25rem',
        fontSize: '0.75rem',
        fontWeight: 500,
        backgroundColor: '#fecaca',
        color: '#991b1b',
      }}
    >
      ✗
    </span>
  );
}

// ============================================================
// METRIC CARD COMPONENT
// ============================================================

const MetricCard: React.FC<{
  title: string;
  value: number;
  color?: string;
}> = ({ title, value, color = '#3b82f6' }) => {
  return (
    <div
      style={{
        backgroundColor: 'white',
        borderRadius: '0.5rem',
        padding: '1.5rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        border: '1px solid #e5e7eb',
      }}
    >
      <div
        style={{
          fontSize: '0.875rem',
          fontWeight: 500,
          color: '#6b7280',
          marginBottom: '0.5rem',
        }}
      >
        {title}
      </div>
      <div
        style={{
          fontSize: '2.5rem',
          fontWeight: 700,
          color,
        }}
      >
        {value}
      </div>
    </div>
  );
};

// ============================================================
// MAIN DASHBOARD COMPONENT
// ============================================================

export const FrontendHealthDashboard: React.FC = () => {
  const metrics = useMemo((): DashboardMetrics => {
    const modules = Object.values(moduleRegistry);

    return {
      totalModules: modules.length,
      exposedFrontend: modules.filter((m) => m.frontend.hasUI).length,
      compliant: modules.filter(
        (m) => m.frontend.compliance && m.status === 'active'
      ).length,
      degraded: modules.filter((m) => m.status === 'degraded').length,
      blocked: modules.filter(
        (m) => !m.frontend.compliance || m.status === 'inactive'
      ).length,
    };
  }, []);

  const moduleEntries = useMemo(() => {
    return Object.entries(moduleRegistry).sort(([, a], [, b]) => {
      // Trier par statut puis par nom
      const statusA = getModuleStatus(a);
      const statusB = getModuleStatus(b);
      if (statusA !== statusB) {
        const order = { compliant: 0, degraded: 1, non_compliant: 2 };
        return order[statusA] - order[statusB];
      }
      return a.name.localeCompare(b.name);
    });
  }, []);

  return (
    <div style={{ padding: '2rem', backgroundColor: '#f9fafb', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ marginBottom: '2rem' }}>
        <h1
          style={{
            fontSize: '2rem',
            fontWeight: 700,
            color: '#111827',
            marginBottom: '0.5rem',
          }}
        >
          Dashboard de Santé Frontend
        </h1>
        <p style={{ fontSize: '1rem', color: '#6b7280' }}>
          Conformité AZA-FE-DASH • Mise à jour: {new Date().toLocaleString('fr-FR')}
        </p>
      </div>

      {/* Indicateurs globaux */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1.5rem',
          marginBottom: '2rem',
        }}
      >
        <MetricCard title="Total Modules" value={metrics.totalModules} color="#3b82f6" />
        <MetricCard
          title="Exposés Frontend"
          value={metrics.exposedFrontend}
          color="#8b5cf6"
        />
        <MetricCard title="Conformes AZA-FE" value={metrics.compliant} color="#10b981" />
        <MetricCard title="Dégradés" value={metrics.degraded} color="#f59e0b" />
        <MetricCard title="Bloqués" value={metrics.blocked} color="#ef4444" />
      </div>

      {/* État des modules */}
      <div
        style={{
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
          border: '1px solid #e5e7eb',
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid #e5e7eb',
          }}
        >
          <h2
            style={{
              fontSize: '1.25rem',
              fontWeight: 600,
              color: '#111827',
              margin: 0,
            }}
          >
            État des Modules
          </h2>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f9fafb' }}>
                <th style={tableHeaderStyle}>Module</th>
                <th style={tableHeaderStyle}>Backend</th>
                <th style={tableHeaderStyle}>Frontend</th>
                <th style={tableHeaderStyle}>Pages</th>
                <th style={tableHeaderStyle}>Routes</th>
                <th style={tableHeaderStyle}>Erreurs</th>
                <th style={tableHeaderStyle}>Conformité AZA-FE</th>
                <th style={tableHeaderStyle}>État</th>
                <th style={tableHeaderStyle}>Propriétaire</th>
                <th style={tableHeaderStyle}>Dernier Audit</th>
              </tr>
            </thead>
            <tbody>
              {moduleEntries.length === 0 ? (
                <tr>
                  <td colSpan={10} style={{ textAlign: 'center', padding: '3rem' }}>
                    <p style={{ color: '#9ca3af', fontSize: '0.875rem' }}>
                      Aucun module enregistré. Exécutez le script de génération meta.ts.
                    </p>
                  </td>
                </tr>
              ) : (
                moduleEntries.map(([code, meta]) => (
                  <tr key={code} style={{ borderBottom: '1px solid #e5e7eb' }}>
                    <td style={tableCellStyle}>
                      <strong>{meta.name}</strong>
                      <br />
                      <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>
                        {code}
                      </span>
                    </td>
                    <td style={tableCellStyle}>
                      {getBooleanBadge(meta.backend.apiAvailable)}
                    </td>
                    <td style={tableCellStyle}>
                      {getBooleanBadge(meta.frontend.hasUI)}
                    </td>
                    <td style={tableCellStyle}>{meta.frontend.pagesCount || 0}</td>
                    <td style={tableCellStyle}>{meta.frontend.routesCount || 0}</td>
                    <td style={tableCellStyle}>
                      {meta.frontend.errorsCount && meta.frontend.errorsCount > 0 ? (
                        <span style={{ color: '#ef4444', fontWeight: 600 }}>
                          {meta.frontend.errorsCount}
                        </span>
                      ) : (
                        <span style={{ color: '#10b981' }}>0</span>
                      )}
                    </td>
                    <td style={tableCellStyle}>
                      {getBooleanBadge(meta.frontend.compliance)}
                    </td>
                    <td style={tableCellStyle}>{getStatusBadge(getModuleStatus(meta))}</td>
                    <td style={tableCellStyle}>
                      <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                        {meta.owner}
                      </span>
                    </td>
                    <td style={tableCellStyle}>
                      <span style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                        {meta.frontend.lastAudit}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer */}
      <div
        style={{
          marginTop: '2rem',
          padding: '1rem',
          textAlign: 'center',
          color: '#9ca3af',
          fontSize: '0.875rem',
        }}
      >
        <p>Norme: AZA-FE-DASH</p>
        <p>Accessible: Dirigeants • Product • Auditeurs</p>
      </div>
    </div>
  );
};

// ============================================================
// STYLES
// ============================================================

const tableHeaderStyle: React.CSSProperties = {
  padding: '0.75rem 1rem',
  textAlign: 'left',
  fontSize: '0.75rem',
  fontWeight: 600,
  textTransform: 'uppercase',
  letterSpacing: '0.05em',
  color: '#6b7280',
};

const tableCellStyle: React.CSSProperties = {
  padding: '1rem',
  fontSize: '0.875rem',
  color: '#374151',
};

export default FrontendHealthDashboard;
