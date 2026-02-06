/**
 * AZALSCORE - Step 3: Pricing Reminder
 * Rappel de l'essai gratuit et des tarifs apres essai
 */

import React from 'react';
import { ArrowRight, ArrowLeft, Check, Clock, CreditCard, Shield } from 'lucide-react';
import { usePricing } from '../api';

interface StepPricingReminderProps {
  onNext: () => void;
  onBack: () => void;
}

export const StepPricingReminder: React.FC<StepPricingReminderProps> = ({
  onNext,
  onBack,
}) => {
  const { data: pricing, isLoading } = usePricing();

  return (
    <div className="trial-form">
      <div className="trial-form-header">
        <h2>Votre essai gratuit de 30 jours</h2>
        <p>Profitez de toutes les fonctionnalites sans engagement.</p>
      </div>

      {/* Trial Benefits */}
      <div className="trial-pricing-benefits">
        <div className="trial-pricing-benefit">
          <div className="trial-pricing-benefit-icon">
            <Clock size={24} />
          </div>
          <div>
            <h4>30 jours gratuits</h4>
            <p>Testez toutes les fonctionnalites pendant 30 jours, sans frais.</p>
          </div>
        </div>

        <div className="trial-pricing-benefit">
          <div className="trial-pricing-benefit-icon">
            <Shield size={24} />
          </div>
          <div>
            <h4>Aucun engagement</h4>
            <p>Annulez a tout moment. Votre compte sera simplement suspendu.</p>
          </div>
        </div>

        <div className="trial-pricing-benefit">
          <div className="trial-pricing-benefit-icon">
            <CreditCard size={24} />
          </div>
          <div>
            <h4>Carte bancaire requise</h4>
            <p>Pour securiser votre compte. Aucun prelevement pendant l'essai.</p>
          </div>
        </div>
      </div>

      {/* Pricing Plans */}
      <div className="trial-pricing-section">
        <h3>Apres votre essai gratuit</h3>
        <p className="trial-pricing-subtitle">
          Choisissez le plan qui correspond a vos besoins.
          Votre compte sera suspendu si vous ne selectionnez pas un plan.
        </p>

        {isLoading ? (
          <div className="trial-pricing-loading">Chargement des tarifs...</div>
        ) : pricing ? (
          <div className="trial-pricing-grid">
            {pricing.plans.map((plan) => (
              <div
                key={plan.code}
                className={`trial-pricing-card ${
                  plan.is_popular ? 'trial-pricing-card--popular' : ''
                }`}
              >
                {plan.is_popular && (
                  <div className="trial-pricing-badge">Populaire</div>
                )}
                <h4>{plan.name}</h4>
                <div className="trial-pricing-price">
                  <span className="trial-pricing-amount">{plan.monthly_price}</span>
                  <span className="trial-pricing-currency">EUR</span>
                  <span className="trial-pricing-period">/mois HT</span>
                </div>
                <ul className="trial-pricing-features">
                  <li>
                    <Check size={14} />
                    {plan.max_users} utilisateurs
                  </li>
                  <li>
                    <Check size={14} />
                    {plan.max_storage_gb} Go de stockage
                  </li>
                  {plan.features.slice(0, 3).map((feature, idx) => (
                    <li key={idx}>
                      <Check size={14} />
                      {feature}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        ) : (
          <div className="trial-pricing-grid">
            {/* Fallback static pricing */}
            <div className="trial-pricing-card">
              <h4>Starter</h4>
              <div className="trial-pricing-price">
                <span className="trial-pricing-amount">29</span>
                <span className="trial-pricing-currency">EUR</span>
                <span className="trial-pricing-period">/mois HT</span>
              </div>
              <ul className="trial-pricing-features">
                <li><Check size={14} /> 1-3 utilisateurs</li>
                <li><Check size={14} /> Modules essentiels</li>
                <li><Check size={14} /> Support email</li>
              </ul>
            </div>
            <div className="trial-pricing-card trial-pricing-card--popular">
              <div className="trial-pricing-badge">Populaire</div>
              <h4>Business</h4>
              <div className="trial-pricing-price">
                <span className="trial-pricing-amount">79</span>
                <span className="trial-pricing-currency">EUR</span>
                <span className="trial-pricing-period">/mois HT</span>
              </div>
              <ul className="trial-pricing-features">
                <li><Check size={14} /> 5-15 utilisateurs</li>
                <li><Check size={14} /> Tous les modules</li>
                <li><Check size={14} /> Support prioritaire</li>
              </ul>
            </div>
            <div className="trial-pricing-card">
              <h4>Enterprise</h4>
              <div className="trial-pricing-price">
                <span className="trial-pricing-amount">Sur devis</span>
              </div>
              <ul className="trial-pricing-features">
                <li><Check size={14} /> Utilisateurs illimites</li>
                <li><Check size={14} /> SLA garanti</li>
                <li><Check size={14} /> Support dedie 24/7</li>
              </ul>
            </div>
          </div>
        )}
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
        <button
          type="button"
          className="trial-btn trial-btn-primary"
          onClick={onNext}
        >
          J'ai compris, continuer
          <ArrowRight size={18} />
        </button>
      </div>
    </div>
  );
};

export default StepPricingReminder;
