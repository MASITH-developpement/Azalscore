/**
 * AZALSCORE - Route Guards (AZA-FE-ENF)
 * ======================================
 * Vérifie module existant/actif/UI contract
 * Journalisation obligatoire des violations
 */

import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { moduleRegistry, ModuleMeta } from '@/modules/registry';

// ============================================================
// TYPES
// ============================================================

interface RouteGuardProps {
  moduleCode: string;
  children: React.ReactNode;
}

type ViolationType =
  | 'MODULE_NOT_FOUND'
  | 'MODULE_INACTIVE'
  | 'NO_UI_CONTRACT'
  | 'NON_COMPLIANT';

// ============================================================
// VIOLATION LOGGING
// ============================================================

function logViolation(type: ViolationType, moduleCode: string): void {
  // Journalisation obligatoire AZA-FE-ENF
  const violation = {
    type,
    moduleCode,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
    url: window.location.href,
  };

  // Log en console pour debug
  console.error(`[AZA-FE-ENF] Violation: ${type} - Module: ${moduleCode}`, violation);

  // Envoi au backend (si disponible)
  if (typeof window !== 'undefined') {
    fetch('/api/frontend-violations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(violation),
    }).catch((error) => {
      // Ne pas bloquer si l'endpoint n'existe pas encore
    });
  }

  // Stockage local pour analytics
  try {
    const violations = JSON.parse(localStorage.getItem('azalscore_violations') || '[]');
    violations.push(violation);
    // Garder seulement les 100 dernières
    localStorage.setItem(
      'azalscore_violations',
      JSON.stringify(violations.slice(-100))
    );
  } catch (error) {
  }
}

// ============================================================
// ERROR PAGES
// ============================================================

const ErrorPage: React.FC<{
  title: string;
  message: string;
  icon: string;
}> = ({ title, message, icon }) => {
  const navigate = useNavigate();

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        padding: '2rem',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>{icon}</div>
      <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#e53e3e' }}>
        {title}
      </h1>
      <p style={{ fontSize: '1.125rem', marginBottom: '2rem', color: '#4a5568' }}>
        {message}
      </p>
      <button
        onClick={() => navigate('/')}
        style={{
          padding: '0.75rem 1.5rem',
          fontSize: '1rem',
          backgroundColor: '#3182ce',
          color: 'white',
          border: 'none',
          borderRadius: '0.375rem',
          cursor: 'pointer',
        }}
      >
        Retour à l'accueil
      </button>
    </div>
  );
};

const ModuleNotFoundPage: React.FC = () => (
  <ErrorPage
    icon="🚫"
    title="Module Introuvable"
    message="Le module demandé n'existe pas dans le système AZALSCORE."
  />
);

const ModuleInactivePage: React.FC = () => (
  <ErrorPage
    icon="⚠️"
    title="Module Inactif"
    message="Ce module est temporairement désactivé."
  />
);

const NoUIContractPage: React.FC = () => (
  <ErrorPage
    icon="🔧"
    title="Interface Non Disponible"
    message="Ce module n'a pas encore d'interface utilisateur."
  />
);

// ============================================================
// NON-COMPLIANT WARNING BANNER
// ============================================================

const NonCompliantBanner: React.FC<{ moduleCode: string }> = ({ moduleCode }) => {
  return (
    <div
      style={{
        backgroundColor: '#fef3c7',
        border: '1px solid #f59e0b',
        padding: '1rem',
        marginBottom: '1rem',
        borderRadius: '0.375rem',
        display: 'flex',
        alignItems: 'center',
        gap: '0.5rem',
      }}
    >
      <span style={{ fontSize: '1.25rem' }}>⚠️</span>
      <div>
        <strong>Module Non Conforme AZA-FE</strong>
        <p style={{ margin: 0, fontSize: '0.875rem' }}>
          Le module "{moduleCode}" ne respecte pas entièrement les normes AZALSCORE.
          Certaines fonctionnalités peuvent être limitées.
        </p>
      </div>
    </div>
  );
};

// ============================================================
// ROUTE GUARD COMPONENT
// ============================================================

export const RouteGuard: React.FC<RouteGuardProps> = ({ moduleCode, children }) => {
  const navigate = useNavigate();
  const meta: ModuleMeta | undefined = moduleRegistry[moduleCode];
  const [showNonCompliantWarning, setShowNonCompliantWarning] = React.useState(false);

  useEffect(() => {
    // Vérification 1: Module existe
    if (!meta) {
      console.error(`[AZA-FE-ENF] Module ${moduleCode} inexistant`);
      logViolation('MODULE_NOT_FOUND', moduleCode);
      navigate('/error/module-not-found');
      return;
    }

    // Vérification 2: Module actif
    if (meta.status === 'inactive') {
      console.error(`[AZA-FE-ENF] Module ${moduleCode} inactif`);
      logViolation('MODULE_INACTIVE', moduleCode);
      navigate('/error/module-inactive');
      return;
    }

    // Vérification 3: UI contract
    if (!meta.frontend.hasUI) {
      console.error(`[AZA-FE-ENF] Module ${moduleCode} sans UI`);
      logViolation('NO_UI_CONTRACT', moduleCode);
      navigate('/error/no-ui');
      return;
    }

    // Vérification 4: Conformité AZA-FE (warning seulement)
    if (!meta.frontend.compliance) {
      logViolation('NON_COMPLIANT', moduleCode);
      setShowNonCompliantWarning(true);
    }
  }, [moduleCode, meta, navigate]);

  // Si module inexistant, inactif, ou sans UI: ne rien render (redirection en cours)
  if (!meta || meta.status === 'inactive' || !meta.frontend.hasUI) {
    return null;
  }

  // Si module existe et actif: render avec warning si non conforme
  return (
    <>
      {showNonCompliantWarning && <NonCompliantBanner moduleCode={moduleCode} />}
      {children}
    </>
  );
};

// ============================================================
// ERROR ROUTE COMPONENTS (pour routing)
// ============================================================

export { ModuleNotFoundPage, ModuleInactivePage, NoUIContractPage };

// ============================================================
// HOOK UTILITAIRE
// ============================================================

export function useModuleGuard(moduleCode: string): {
  isAllowed: boolean;
  meta: ModuleMeta | undefined;
} {
  const meta = moduleRegistry[moduleCode];

  const isAllowed =
    !!meta && meta.status !== 'inactive' && meta.frontend.hasUI;

  return { isAllowed, meta };
}
