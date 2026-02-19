/**
 * AZALSCORE - Page Tarifs
 * Grille tarifaire de l'ERP
 */

import React from 'react';
import { ArrowRight, Check } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StructuredData } from '../../components/StructuredData';
import '../../styles/landing.css';

const PricingPage: React.FC = () => {
  return (
    <div className="landing-page">
      <StructuredData />

      {/* Header */}
      <header className="landing-header">
        <div className="landing-header-content">
          <Link to="/" className="landing-logo">
            <span className="landing-logo-text">AZALSCORE</span>
          </Link>
          <nav className="landing-nav">
            <Link to="/features">Fonctionnalites</Link>
            <Link to="/pricing">Tarifs</Link>
            <Link to="/contact">Contact</Link>
            <Link to="/login" className="landing-btn landing-btn-outline">
              Connexion
            </Link>
            <Link to="/essai-gratuit" className="landing-btn landing-btn-primary">
              Essai gratuit
              <ArrowRight size={16} />
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="landing-hero" style={{ paddingBottom: '40px' }}>
        <div className="landing-hero-content">
          <h1 className="landing-hero-title">
            Tarifs simples et transparents
          </h1>
          <p className="landing-hero-subtitle">
            Sans engagement. Annulez a tout moment. Essai gratuit 30 jours inclus.
          </p>
        </div>
      </section>

      {/* Pricing Grid */}
      <section className="landing-section landing-pricing" style={{ paddingTop: '40px' }}>
        <div className="landing-container">
          <div className="landing-pricing-grid">
            {/* Starter */}
            <div className="landing-pricing-card">
              <div className="landing-pricing-header">
                <h3>Starter</h3>
                <p className="landing-pricing-desc">Pour les TPE et independants</p>
              </div>
              <div className="landing-pricing-price">
                <span className="landing-pricing-amount">29</span>
                <span className="landing-pricing-currency">€</span>
                <span className="landing-pricing-period">/mois HT</span>
              </div>
              <ul className="landing-pricing-features">
                <li><Check size={16} /> 1 a 3 utilisateurs</li>
                <li><Check size={16} /> Modules essentiels (CRM, Facturation, Stock)</li>
                <li><Check size={16} /> Facturation electronique 2026</li>
                <li><Check size={16} /> Export FEC</li>
                <li><Check size={16} /> Support email</li>
                <li><Check size={16} /> Mises a jour incluses</li>
                <li><Check size={16} /> Hebergement France</li>
              </ul>
              <Link to="/essai-gratuit" className="landing-btn landing-btn-outline landing-btn-block">
                Essayer gratuitement
              </Link>
            </div>

            {/* Business */}
            <div className="landing-pricing-card landing-pricing-card--popular">
              <div className="landing-pricing-badge">Populaire</div>
              <div className="landing-pricing-header">
                <h3>Business</h3>
                <p className="landing-pricing-desc">Pour les PME en croissance</p>
              </div>
              <div className="landing-pricing-price">
                <span className="landing-pricing-amount">79</span>
                <span className="landing-pricing-currency">€</span>
                <span className="landing-pricing-period">/mois HT</span>
              </div>
              <ul className="landing-pricing-features">
                <li><Check size={16} /> 5 a 15 utilisateurs</li>
                <li><Check size={16} /> Tous les modules</li>
                <li><Check size={16} /> Facturation electronique 2026</li>
                <li><Check size={16} /> Comptabilite complete</li>
                <li><Check size={16} /> Support prioritaire</li>
                <li><Check size={16} /> API & integrations</li>
                <li><Check size={16} /> Rapports avances</li>
                <li><Check size={16} /> Multi-devises</li>
              </ul>
              <Link to="/essai-gratuit" className="landing-btn landing-btn-primary landing-btn-block">
                Essayer gratuitement
              </Link>
            </div>

            {/* Enterprise */}
            <div className="landing-pricing-card">
              <div className="landing-pricing-header">
                <h3>Enterprise</h3>
                <p className="landing-pricing-desc">Pour les grandes structures</p>
              </div>
              <div className="landing-pricing-price">
                <span className="landing-pricing-amount">Sur devis</span>
              </div>
              <ul className="landing-pricing-features">
                <li><Check size={16} /> Utilisateurs illimites</li>
                <li><Check size={16} /> Tous les modules</li>
                <li><Check size={16} /> Support 24/7 dedie</li>
                <li><Check size={16} /> SLA garanti 99.9%</li>
                <li><Check size={16} /> Formation sur site</li>
                <li><Check size={16} /> Personnalisations</li>
                <li><Check size={16} /> Migration assistee</li>
                <li><Check size={16} /> Account manager dedie</li>
              </ul>
              <Link to="/contact" className="landing-btn landing-btn-outline landing-btn-block">
                Nous contacter
              </Link>
            </div>
          </div>

          <p className="landing-pricing-note">
            Tous les plans incluent : hebergement securise en France, conformite RGPD,
            sauvegardes automatiques quotidiennes, chiffrement AES-256, authentification 2FA.
          </p>
        </div>
      </section>

      {/* FAQ Pricing */}
      <section className="landing-section" style={{ background: '#f8faff' }}>
        <div className="landing-container">
          <h2 className="landing-section-title">Questions sur les tarifs</h2>
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <div style={{ marginBottom: '24px', padding: '24px', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <h3 style={{ margin: '0 0 12px', color: '#1a1a2e' }}>Puis-je changer de formule ?</h3>
              <p style={{ margin: 0, color: '#4a5568' }}>
                Oui, vous pouvez upgrader ou downgrader a tout moment. Le changement prend effet au prochain cycle de facturation.
              </p>
            </div>
            <div style={{ marginBottom: '24px', padding: '24px', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <h3 style={{ margin: '0 0 12px', color: '#1a1a2e' }}>L'essai gratuit est-il vraiment sans engagement ?</h3>
              <p style={{ margin: 0, color: '#4a5568' }}>
                Absolument. Vous avez 30 jours pour tester toutes les fonctionnalites. Aucune carte bancaire n'est requise pour commencer. Vous pouvez annuler a tout moment.
              </p>
            </div>
            <div style={{ marginBottom: '24px', padding: '24px', background: 'white', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
              <h3 style={{ margin: '0 0 12px', color: '#1a1a2e' }}>Y a-t-il des frais caches ?</h3>
              <p style={{ margin: 0, color: '#4a5568' }}>
                Non. Le prix affiche est le prix que vous payez. Pas de frais de mise en service, pas de frais de support, pas de surprises.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="landing-section landing-cta">
        <div className="landing-container">
          <h2>Pret a simplifier votre gestion ?</h2>
          <p>Commencez votre essai gratuit de 30 jours maintenant.</p>
          <Link to="/essai-gratuit" className="landing-btn landing-btn-primary landing-btn-lg">
            Commencer gratuitement
            <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-container">
          <div className="landing-footer-content">
            <div className="landing-footer-brand">
              <span>AZALSCORE</span>
            </div>
            <div className="landing-footer-links">
              <Link to="/mentions-legales">Mentions legales</Link>
              <Link to="/confidentialite">Confidentialite</Link>
              <Link to="/cgv">CGV</Link>
              <Link to="/contact">Contact</Link>
            </div>
            <p className="landing-footer-copy">
              &copy; 2026 AZALSCORE - MASITH Developpement. Tous droits reserves.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PricingPage;
