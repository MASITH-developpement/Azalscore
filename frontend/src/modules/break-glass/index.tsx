/**
 * AZALSCORE Module - Break-Glass Souverain (Option A)
 *
 * MÉCANISME D'URGENCE SOUVERAIN
 *
 * RÈGLES ABSOLUES:
 * - Accessible UNIQUEMENT si capacité backend `admin.root.break_glass` présente
 * - Invisible pour tous les autres utilisateurs
 * - Non listé dans les menus standards
 * - Jamais activable par automatisation
 * - L'UI ne journalise RIEN localement
 * - L'UI n'expose AUCUN détail sur le périmètre ou les données
 *
 * FLUX À 3 NIVEAUX:
 * - Niveau 1: Intention explicite
 * - Niveau 2: Confirmation humaine (phrase complète)
 * - Niveau 3: Confirmation forte (ré-authentification + compte à rebours)
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { AlertTriangle, Shield, Clock, Key, ArrowLeft, Check, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { trackBreakGlassEvent } from '@core/audit-ui';
import { useCanBreakGlass } from '@core/capabilities';
import { Button } from '@ui/actions';
import { PageWrapper } from '@ui/layout';
import { ErrorState } from '../../ui-engine/components/StateViews';
import {
  breakGlassApi,
  type BreakGlassScope,
  type BreakGlassChallenge,
  type BreakGlassRequest,
  type TenantOption,
  type ModuleOption,
} from './api';

// ============================================================
// TYPES
// ============================================================

type BreakGlassStep = 'intention' | 'confirmation' | 'authentication' | 'executing' | 'complete';

// ============================================================
// API HOOKS
// ============================================================

const useBreakGlassChallenge = () => {
  return useMutation({
    mutationFn: async (scope: BreakGlassScope) => {
      const response = await breakGlassApi.requestChallenge(scope);
      return response.data;
    },
  });
};

const useExecuteBreakGlass = () => {
  return useMutation({
    mutationFn: async (request: BreakGlassRequest) => {
      await breakGlassApi.execute(request);
    },
  });
};

const useTenantsList = () => {
  return useQuery({
    queryKey: ['break-glass', 'tenants'],
    queryFn: async () => {
      const response = await breakGlassApi.listTenants();
      return response.data.items;
    },
  });
};

const useModulesList = () => {
  return useQuery({
    queryKey: ['break-glass', 'modules'],
    queryFn: async () => {
      const response = await breakGlassApi.listModules();
      return response.data.items;
    },
  });
};

// ============================================================
// LEVEL 1: INTENTION EXPLICITE
// ============================================================

interface Level1Props {
  onProceed: () => void;
  onCancel: () => void;
}

const Level1Intention: React.FC<Level1Props> = ({ onProceed, onCancel }) => {
  return (
    <div className="azals-break-glass__level azals-break-glass__level--1">
      <div className="azals-break-glass__icon azals-break-glass__icon--warning">
        <AlertTriangle size={48} />
      </div>

      <h2 className="azals-break-glass__title">Break-Glass Souverain</h2>

      <div className="azals-break-glass__warning-box">
        <p className="azals-break-glass__warning-text">
          <strong>AVERTISSEMENT CRITIQUE</strong>
        </p>
        <p>
          Vous êtes sur le point d'initier une procédure Break-Glass.
          Cette procédure est réservée aux situations d'urgence absolue
          nécessitant un accès exceptionnel aux données ou fonctionnalités protégées.
        </p>
        <p>
          <strong>Cette action est irréversible et sera enregistrée dans un journal externe inviolable.</strong>
        </p>
        <p>
          En continuant, vous engagez votre responsabilité personnelle
          et professionnelle sur l'utilisation de cette procédure.
        </p>
      </div>

      <div className="azals-break-glass__rules">
        <h3>Règles d'utilisation</h3>
        <ul>
          <li>Utilisation uniquement en cas d'urgence absolue</li>
          <li>Justification obligatoire de l'accès</li>
          <li>Traçabilité complète et inviolable</li>
          <li>Audit externe automatique</li>
          <li>Responsabilité personnelle engagée</li>
        </ul>
      </div>

      <div className="azals-break-glass__actions">
        <Button variant="ghost" onClick={onCancel} leftIcon={<ArrowLeft size={16} />}>
          Annuler et quitter
        </Button>
        <Button variant="danger" onClick={onProceed}>
          Déclencher une procédure Break-Glass
        </Button>
      </div>
    </div>
  );
};

// ============================================================
// LEVEL 2: CONFIRMATION HUMAINE
// ============================================================

interface Level2Props {
  challenge: BreakGlassChallenge | null;
  scope: BreakGlassScope;
  onScopeChange: (scope: BreakGlassScope) => void;
  onRequestChallenge: () => void;
  typedPhrase: string;
  onTypedPhraseChange: (value: string) => void;
  reason: string;
  onReasonChange: (value: string) => void;
  onProceed: () => void;
  onCancel: () => void;
  isLoadingChallenge: boolean;
}

const Level2Confirmation: React.FC<Level2Props> = ({
  challenge,
  scope,
  onScopeChange,
  onRequestChallenge,
  typedPhrase,
  onTypedPhraseChange,
  reason,
  onReasonChange,
  onProceed,
  onCancel,
  isLoadingChallenge,
}) => {
  const { data: tenants, error: tenantsError, refetch: refetchTenants } = useTenantsList();
  const { data: modules, error: modulesError, refetch: refetchModules } = useModulesList();

  const isPhraseCorrect = challenge && typedPhrase.trim() === challenge.confirmation_phrase;

  return (
    <div className="azals-break-glass__level azals-break-glass__level--2">
      <div className="azals-break-glass__icon">
        <Shield size={48} />
      </div>

      <h2 className="azals-break-glass__title">Confirmation Humaine Requise</h2>

      {/* Sélection du périmètre */}
      <div className="azals-break-glass__section">
        <h3>Périmètre d'intervention</h3>

        {(tenantsError || modulesError) && (
          <ErrorState
            message={
              tenantsError instanceof Error
                ? tenantsError.message
                : modulesError instanceof Error
                ? modulesError.message
                : 'Impossible de charger les options de périmètre.'
            }
            onRetry={() => { refetchTenants(); refetchModules(); }}
          />
        )}

        <div className="azals-break-glass__form-group">
          <label>Client (tenant)</label>
          <select
            value={scope.tenant_id || ''}
            onChange={(e) => onScopeChange({ ...scope, tenant_id: e.target.value || undefined })}
            className="azals-select"
          >
            <option value="">Tous les clients</option>
            {tenants?.map((t) => (
              <option key={t.id} value={t.id}>{t.name}</option>
            ))}
          </select>
        </div>

        <div className="azals-break-glass__form-group">
          <label>Module</label>
          <select
            value={scope.module || ''}
            onChange={(e) => onScopeChange({ ...scope, module: e.target.value || undefined })}
            className="azals-select"
          >
            <option value="">Tous les modules</option>
            {modules?.map((m) => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>

        <div className="azals-break-glass__form-row">
          <div className="azals-break-glass__form-group">
            <label>Date début</label>
            <input
              type="date"
              value={scope.start_date || ''}
              onChange={(e) => onScopeChange({ ...scope, start_date: e.target.value || undefined })}
              className="azals-input"
            />
          </div>
          <div className="azals-break-glass__form-group">
            <label>Date fin</label>
            <input
              type="date"
              value={scope.end_date || ''}
              onChange={(e) => onScopeChange({ ...scope, end_date: e.target.value || undefined })}
              className="azals-input"
            />
          </div>
        </div>

        {!challenge && (
          <Button
            variant="secondary"
            onClick={onRequestChallenge}
            isLoading={isLoadingChallenge}
          >
            Obtenir la phrase de confirmation
          </Button>
        )}
      </div>

      {/* Phrase de confirmation */}
      {challenge && (
        <div className="azals-break-glass__section azals-break-glass__section--confirmation">
          <h3>Confirmation manuelle obligatoire</h3>
          <p className="azals-break-glass__instruction">
            Pour continuer, vous devez taper <strong>exactement</strong> la phrase suivante :
          </p>

          <div className="azals-break-glass__phrase-box">
            <code>{challenge.confirmation_phrase}</code>
          </div>

          <div className="azals-break-glass__form-group">
            <label>Tapez la phrase ci-dessus</label>
            <input
              type="text"
              value={typedPhrase}
              onChange={(e) => onTypedPhraseChange(e.target.value)}
              className={`azals-input azals-input--lg ${
                typedPhrase && (isPhraseCorrect ? 'azals-input--success' : 'azals-input--error')
              }`}
              placeholder="Tapez la phrase exactement..."
              autoComplete="off"
              autoCorrect="off"
              spellCheck={false}
            />
            {typedPhrase && (
              <span className={`azals-break-glass__phrase-status ${isPhraseCorrect ? 'azals-text--success' : 'azals-text--danger'}`}>
                {isPhraseCorrect ? (
                  <><Check size={16} /> Phrase correcte</>
                ) : (
                  <><X size={16} /> Phrase incorrecte</>
                )}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Motif (facultatif) */}
      {challenge && isPhraseCorrect && (
        <div className="azals-break-glass__section">
          <h3>Motif (facultatif)</h3>
          <textarea
            value={reason}
            onChange={(e) => onReasonChange(e.target.value)}
            className="azals-textarea"
            rows={3}
            placeholder="Décrivez brièvement la raison de cette intervention..."
          />
        </div>
      )}

      <div className="azals-break-glass__actions">
        <Button variant="ghost" onClick={onCancel} leftIcon={<ArrowLeft size={16} />}>
          Annuler
        </Button>
        <Button
          variant="danger"
          onClick={onProceed}
          isDisabled={!isPhraseCorrect}
        >
          Continuer
        </Button>
      </div>
    </div>
  );
};

// ============================================================
// LEVEL 3: CONFIRMATION FORTE
// ============================================================

interface Level3Props {
  password: string;
  onPasswordChange: (value: string) => void;
  totpCode: string;
  onTotpCodeChange: (value: string) => void;
  requires2FA: boolean;
  countdown: number;
  canExecute: boolean;
  onExecute: () => void;
  onCancel: () => void;
  isExecuting: boolean;
}

const Level3Authentication: React.FC<Level3Props> = ({
  password,
  onPasswordChange,
  totpCode,
  onTotpCodeChange,
  requires2FA,
  countdown,
  canExecute,
  onExecute,
  onCancel,
  isExecuting,
}) => {
  return (
    <div className="azals-break-glass__level azals-break-glass__level--3">
      <div className="azals-break-glass__icon azals-break-glass__icon--critical">
        <Key size={48} />
      </div>

      <h2 className="azals-break-glass__title">Ré-authentification Requise</h2>

      <div className="azals-break-glass__final-warning">
        <AlertTriangle size={24} />
        <p>
          <strong>Cette action est irréversible et engage votre responsabilité.</strong>
        </p>
      </div>

      {/* Ré-authentification */}
      <div className="azals-break-glass__section">
        <div className="azals-break-glass__form-group">
          <label>Mot de passe</label>
          <input
            type="password"
            value={password}
            onChange={(e) => onPasswordChange(e.target.value)}
            className="azals-input"
            placeholder="Entrez votre mot de passe"
            autoComplete="current-password"
          />
        </div>

        {requires2FA && (
          <div className="azals-break-glass__form-group">
            <label>Code 2FA</label>
            <input
              type="text"
              value={totpCode}
              onChange={(e) => onTotpCodeChange(e.target.value)}
              className="azals-input"
              placeholder="Code à 6 chiffres"
              maxLength={6}
              autoComplete="one-time-code"
            />
          </div>
        )}
      </div>

      {/* Compte à rebours */}
      <div className="azals-break-glass__countdown">
        <Clock size={24} />
        <div className="azals-break-glass__countdown-timer">
          {countdown > 0 ? (
            <>
              <span className="azals-break-glass__countdown-value">{countdown}</span>
              <span className="azals-break-glass__countdown-label">secondes avant activation possible</span>
            </>
          ) : (
            <span className="azals-break-glass__countdown-ready">Prêt pour exécution</span>
          )}
        </div>
      </div>

      <div className="azals-break-glass__actions">
        <Button variant="ghost" onClick={onCancel} leftIcon={<ArrowLeft size={16} />}>
          Annuler
        </Button>
        <Button
          variant="danger"
          onClick={onExecute}
          isDisabled={!canExecute || countdown > 0 || !password}
          isLoading={isExecuting}
        >
          Exécuter la procédure Break-Glass
        </Button>
      </div>
    </div>
  );
};

// ============================================================
// EXECUTION COMPLETE
// ============================================================

const ExecutionComplete: React.FC<{ onClose: () => void }> = ({ onClose }) => {
  const navigate = useNavigate();

  useEffect(() => {
    const timer = setTimeout(() => {
      navigate('/admin');
    }, 5000);
    return () => clearTimeout(timer);
  }, [navigate]);

  return (
    <div className="azals-break-glass__level azals-break-glass__level--complete">
      <div className="azals-break-glass__icon azals-break-glass__icon--complete">
        <Check size={48} />
      </div>

      <h2 className="azals-break-glass__title">Procédure Break-Glass exécutée</h2>

      <p className="azals-break-glass__complete-message">
        La procédure a été exécutée avec succès.
        Vous allez être redirigé vers le tableau de bord administrateur.
      </p>

      <Button variant="secondary" onClick={onClose}>
        Retour au tableau de bord
      </Button>
    </div>
  );
};

// ============================================================
// MAIN BREAK-GLASS COMPONENT
// ============================================================

export const BreakGlassPage: React.FC = () => {
  const navigate = useNavigate();
  const canBreakGlass = useCanBreakGlass();

  // State
  const [step, setStep] = useState<BreakGlassStep>('intention');
  const [scope, setScope] = useState<BreakGlassScope>({});
  const [challenge, setChallenge] = useState<BreakGlassChallenge | null>(null);
  const [typedPhrase, setTypedPhrase] = useState('');
  const [reason, setReason] = useState('');
  const [password, setPassword] = useState('');
  const [totpCode, setTotpCode] = useState('');
  const [countdown, setCountdown] = useState(30);
  const countdownRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // API mutations
  const requestChallenge = useBreakGlassChallenge();
  const executeBreakGlass = useExecuteBreakGlass();

  // Redirect if no capability
  useEffect(() => {
    if (!canBreakGlass) {
      navigate('/admin');
    }
  }, [canBreakGlass, navigate]);

  // Track initiation
  useEffect(() => {
    if (step === 'intention') {
      trackBreakGlassEvent('initiated');
    }
  }, [step]);

  // Countdown timer
  useEffect(() => {
    if (step === 'authentication' && countdown > 0) {
      countdownRef.current = setInterval(() => {
        setCountdown((prev) => {
          if (prev <= 1) {
            if (countdownRef.current) {
              clearInterval(countdownRef.current);
            }
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }

    return () => {
      if (countdownRef.current) {
        clearInterval(countdownRef.current);
      }
    };
  }, [step]);

  // Handlers
  const handleCancel = useCallback(() => {
    trackBreakGlassEvent('cancelled');
    navigate('/admin');
  }, [navigate]);

  const handleLevel1Proceed = useCallback(() => {
    setStep('confirmation');
  }, []);

  const handleRequestChallenge = useCallback(async () => {
    try {
      const result = await requestChallenge.mutateAsync(scope);
      setChallenge(result);
    } catch {
      // Error handled by mutation
    }
  }, [scope, requestChallenge]);

  const handleLevel2Proceed = useCallback(() => {
    trackBreakGlassEvent('confirmed');
    setCountdown(30);
    setStep('authentication');
  }, []);

  const handleExecute = useCallback(async () => {
    if (!challenge) return;

    setStep('executing');

    try {
      await executeBreakGlass.mutateAsync({
        scope,
        confirmation_phrase: typedPhrase,
        reason: reason || undefined,
        password,
        totp_code: totpCode || undefined,
      });

      trackBreakGlassEvent('executed');
      setStep('complete');
    } catch {
      setStep('authentication');
    }
  }, [challenge, scope, typedPhrase, reason, password, totpCode, executeBreakGlass]);

  const handleComplete = useCallback(() => {
    navigate('/admin');
  }, [navigate]);

  // Don't render if no capability
  if (!canBreakGlass) {
    return null;
  }

  return (
    <PageWrapper title="">
      <div className="azals-break-glass">
        {step === 'intention' && (
          <Level1Intention onProceed={handleLevel1Proceed} onCancel={handleCancel} />
        )}

        {step === 'confirmation' && (
          <Level2Confirmation
            challenge={challenge}
            scope={scope}
            onScopeChange={setScope}
            onRequestChallenge={handleRequestChallenge}
            typedPhrase={typedPhrase}
            onTypedPhraseChange={setTypedPhrase}
            reason={reason}
            onReasonChange={setReason}
            onProceed={handleLevel2Proceed}
            onCancel={handleCancel}
            isLoadingChallenge={requestChallenge.isPending}
          />
        )}

        {step === 'authentication' && (
          <Level3Authentication
            password={password}
            onPasswordChange={setPassword}
            totpCode={totpCode}
            onTotpCodeChange={setTotpCode}
            requires2FA={true}
            countdown={countdown}
            canExecute={!!password && countdown === 0}
            onExecute={handleExecute}
            onCancel={handleCancel}
            isExecuting={executeBreakGlass.isPending}
          />
        )}

        {step === 'executing' && (
          <div className="azals-break-glass__level azals-break-glass__level--executing">
            <div className="azals-spinner azals-spinner--lg" />
            <p>Exécution en cours...</p>
          </div>
        )}

        {step === 'complete' && <ExecutionComplete onClose={handleComplete} />}
      </div>
    </PageWrapper>
  );
};

export default BreakGlassPage;
