/**
 * AZALSCORE - Step 6: Payment
 * Enregistrement carte bancaire via Stripe SetupIntent
 */

import React, { useEffect, useState } from 'react';
import {
  Elements,
  PaymentElement,
  useStripe,
  useElements,
} from '@stripe/react-stripe-js';
import { loadStripe, type Stripe } from '@stripe/stripe-js';
import {
  ArrowLeft,
  CreditCard,
  Shield,
  Lock,
  AlertCircle,
  Loader2,
  Check,
  Clock,
 Gift } from 'lucide-react';
import { usePaymentSetup, useCompleteRegistration, useApplyPromoCode } from '../api';
import type { TrialCompleteResponse } from '../types';

// Stripe appearance customization
const stripeAppearance = {
  theme: 'stripe' as const,
  variables: {
    colorPrimary: '#1E6EFF',
    colorBackground: '#ffffff',
    colorText: '#1a1a2e',
    colorDanger: '#ef4444',
    fontFamily: 'Inter, system-ui, sans-serif',
    borderRadius: '8px',
    spacingUnit: '4px',
  },
};

interface PaymentFormProps {
  registrationId: string;
  setupIntentId: string;
  onSuccess: (result: TrialCompleteResponse) => void;
  onBack: () => void;
}

const PaymentForm: React.FC<PaymentFormProps> = ({
  registrationId,
  setupIntentId,
  onSuccess,
  onBack,
}) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const completeRegistration = useCompleteRegistration();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsProcessing(true);
    setError(null);

    try {
      // Confirm the SetupIntent
      const { error: stripeError, setupIntent } = await stripe.confirmSetup({
        elements,
        confirmParams: {
          return_url: window.location.href,
        },
        redirect: 'if_required',
      });

      if (stripeError) {
        setError(stripeError.message || 'Une erreur est survenue lors du paiement');
        setIsProcessing(false);
        return;
      }

      if (setupIntent && setupIntent.status === 'succeeded') {
        // Complete the registration
        const result = await completeRegistration.mutateAsync({
          registration_id: registrationId,
          setup_intent_id: setupIntentId,
        });
        onSuccess(result);
      } else {
        setError('La verification de la carte a echoue. Veuillez reessayer.');
        setIsProcessing(false);
      }
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Une erreur inattendue est survenue';
      setError(errorMessage);
      setIsProcessing(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="trial-payment-form">
      {/* Security badges */}
      <div className="trial-payment-badges">
        <div className="trial-payment-badge">
          <Lock size={14} />
          <span>Paiement securise</span>
        </div>
        <div className="trial-payment-badge">
          <Shield size={14} />
          <span>Chiffrement SSL</span>
        </div>
      </div>

      {/* Info banner */}
      <div className="trial-payment-info">
        <CreditCard size={20} />
        <div>
          <strong>Aucun prelevement aujourd'hui</strong>
          <p>
            Votre carte sera enregistree pour securiser votre compte.
            Aucun prelevement ne sera effectue pendant la periode d'essai de 30 jours.
          </p>
        </div>
      </div>

      {/* Error display */}
      {error && (
        <div className="trial-form-error-banner">
          <AlertCircle size={20} />
          <span>{error}</span>
        </div>
      )}

      {/* Stripe Payment Element */}
      <div className="trial-payment-element">
        <PaymentElement
          options={{
            layout: 'tabs',
          }}
        />
      </div>

      <div className="trial-form-actions">
        <button
          type="button"
          className="trial-btn trial-btn-outline"
          onClick={onBack}
          disabled={isProcessing}
        >
          <ArrowLeft size={18} />
          Retour
        </button>
        <button
          type="submit"
          className="trial-btn trial-btn-primary"
          disabled={!stripe || isProcessing}
        >
          {isProcessing ? (
            <>
              <Loader2 size={18} className="spinning" />
              Verification...
            </>
          ) : (
            <>
              Enregistrer ma carte
              <Check size={18} />
            </>
          )}
        </button>
      </div>
    </form>
  );
};

interface StepPaymentProps {
  registrationId: string;
  onSuccess: (result: TrialCompleteResponse) => void;
  onBack: () => void;
}

export const StepPayment: React.FC<StepPaymentProps> = ({
  registrationId,
  onSuccess,
  onBack,
}) => {
  const [stripePromise, setStripePromise] = useState<Promise<Stripe | null> | null>(null);
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [setupIntentId, setSetupIntentId] = useState<string | null>(null);
  const [showPromoCode, setShowPromoCode] = useState(false);
  const [promoCode, setPromoCode] = useState('');
  const [promoError, setPromoError] = useState<string | null>(null);
  const [promoPendingApproval, setPromoPendingApproval] = useState(false);
  const [promoMessage, setPromoMessage] = useState<string | null>(null);

  const paymentSetup = usePaymentSetup();
  const applyPromoCode = useApplyPromoCode();

  const handleApplyPromoCode = async () => {
    if (!promoCode.trim()) {
      setPromoError('Veuillez entrer un code promo');
      return;
    }
    setPromoError(null);
    try {
      const result = await applyPromoCode.mutateAsync({
        registration_id: registrationId,
        promo_code: promoCode.trim(),
      });
      // Promo code always requires admin approval
      setPromoPendingApproval(true);
      setPromoMessage(result.message);
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Code promo invalide';
      setPromoError(errorMessage);
    }
  };

  // Initialize Stripe and get SetupIntent
  useEffect(() => {
    paymentSetup.mutate(
      { registration_id: registrationId },
      {
        onSuccess: (data) => {
          setStripePromise(loadStripe(data.publishable_key));
          setClientSecret(data.client_secret);
          setSetupIntentId(data.setup_intent_id);
        },
      }
    );
  }, [registrationId]);

  // Pending promo approval state
  if (promoPendingApproval) {
    return (
      <div className="trial-form">
        <div className="trial-form-header">
          <h2>Demande en cours de traitement</h2>
        </div>
        <div className="trial-promo-pending">
          <div className="trial-promo-pending-icon">
            <Clock size={64} />
          </div>
          <h3>En attente d'approbation</h3>
          <p>{promoMessage || 'Votre demande a été envoyée et est en attente de validation.'}</p>
          <p className="trial-promo-pending-info">
            Vous recevrez un email à l'adresse indiquée lors de votre inscription
            dès que votre demande aura été traitée.
          </p>
        </div>
      </div>
    );
  }

  if (paymentSetup.isPending || !stripePromise || !clientSecret) {
    return (
      <div className="trial-form">
        <div className="trial-form-header">
          <h2>Configuration du paiement</h2>
          <p>Preparation de l'interface de paiement securisee...</p>
        </div>
        <div className="trial-payment-loading">
          <Loader2 size={48} className="spinning" />
          <p>Chargement de Stripe...</p>
        </div>
      </div>
    );
  }

  if (paymentSetup.error) {
    return (
      <div className="trial-form">
        <div className="trial-form-header">
          <h2>Erreur</h2>
        </div>
        <div className="trial-form-error-banner">
          <AlertCircle size={20} />
          <span>{paymentSetup.error.message}</span>
        </div>
        <div className="trial-form-actions">
          <button
            type="button"
            className="trial-btn trial-btn-outline"
            onClick={onBack}
          >
            <ArrowLeft size={18} />
            Retour
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="trial-form">
      <div className="trial-form-header">
        <h2>Enregistrement de votre carte</h2>
        <p>Securisez votre compte en enregistrant un moyen de paiement.</p>
      </div>

      <Elements
        stripe={stripePromise}
        options={{
          clientSecret,
          appearance: stripeAppearance,
          locale: 'fr',
        }}
      >
        <PaymentForm
          registrationId={registrationId}
          setupIntentId={setupIntentId!}
          onSuccess={onSuccess}
          onBack={onBack}
        />
      </Elements>

      {/* Promo code section */}
      <div className="trial-promo-section">
        <button
          type="button"
          className="trial-promo-toggle"
          onClick={() => setShowPromoCode(!showPromoCode)}
        >
          <Gift size={16} />
          {showPromoCode ? 'Masquer' : 'J\'ai un code promo'}
        </button>

        {showPromoCode && (
          <div className="trial-promo-form">
            <div className="trial-promo-input-group">
              <input
                type="text"
                className="trial-form-input"
                placeholder="Entrez votre code promo"
                value={promoCode}
                onChange={(e) => setPromoCode(e.target.value)}
                disabled={applyPromoCode.isPending}
              />
              <button
                type="button"
                className="trial-btn trial-btn-secondary"
                onClick={handleApplyPromoCode}
                disabled={applyPromoCode.isPending || !promoCode.trim()}
              >
                {applyPromoCode.isPending ? (
                  <Loader2 size={16} className="spinning" />
                ) : (
                  'Appliquer'
                )}
              </button>
            </div>
            {promoError && (
              <div className="trial-promo-error">
                <AlertCircle size={14} />
                <span>{promoError}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StepPayment;
