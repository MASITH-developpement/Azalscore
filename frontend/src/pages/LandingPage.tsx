/**
 * AZALSCORE - Landing Page Publique
 * Page d'accueil accessible sans authentification
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Check,
  BarChart3,
  Users,
  Package,
  FileText,
  CreditCard,
  Shield,
  Zap,
  Globe,
  Clock,
  HeadphonesIcon,
} from 'lucide-react';
import { COLORS } from '@core/design-tokens';
import '../styles/landing.css';

// Logo AZALSCORE
const AzalscoreLogo: React.FC<{ size?: number }> = ({ size = 40 }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
    <rect width="100" height="100" rx="20" fill={COLORS.primary} />
    <path
      d="M25 70L50 25L75 70H60L50 50L40 70H25Z"
      fill="white"
      stroke="white"
      strokeWidth="2"
      strokeLinejoin="round"
    />
    <circle cx="50" cy="65" r="8" fill="white" />
  </svg>
);

// Composant Feature Card
const FeatureCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  description: string;
}> = ({ icon, title, description }) => (
  <div className="landing-feature-card">
    <div className="landing-feature-icon">{icon}</div>
    <h3 className="landing-feature-title">{title}</h3>
    <p className="landing-feature-description">{description}</p>
  </div>
);

// Composant Module Card
const ModuleCard: React.FC<{
  icon: React.ReactNode;
  title: string;
  features: string[];
}> = ({ icon, title, features }) => (
  <div className="landing-module-card">
    <div className="landing-module-header">
      <span className="landing-module-icon">{icon}</span>
      <h3 className="landing-module-title">{title}</h3>
    </div>
    <ul className="landing-module-features">
      {features.map((feature, idx) => (
        <li key={idx}>
          <Check size={14} />
          <span>{feature}</span>
        </li>
      ))}
    </ul>
  </div>
);

export const LandingPage: React.FC = () => {
  const [demoEmail, setDemoEmail] = useState('');
  const [demoSent, setDemoSent] = useState(false);

  const handleDemoRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!demoEmail) return;

    try {
      await fetch('/api/v2/website/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: 'Demande Landing',
          email: demoEmail,
          source: 'website_form',
          message: 'Demande de demo depuis landing page',
        }),
      });
      setDemoSent(true);
    } catch (error) {
      console.error('Erreur envoi demo:', error);
    }
  };

  return (
    <div className="landing-page">
      {/* Header */}
      <header className="landing-header">
        <div className="landing-header-content">
          <Link to="/" className="landing-logo">
            <AzalscoreLogo size={36} />
            <span className="landing-logo-text">AZALSCORE</span>
          </Link>
          <nav className="landing-nav">
            <a href="#modules">Modules</a>
            <a href="#features">Fonctionnalites</a>
            <a href="#pricing">Tarifs</a>
            <Link to="/login" className="landing-btn landing-btn-outline">
              Connexion
            </Link>
            <Link to="/login" className="landing-btn landing-btn-primary">
              Essai gratuit
              <ArrowRight size={16} />
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero Section */}
      <section className="landing-hero">
        <div className="landing-hero-content">
          <h1 className="landing-hero-title">
            L'ERP complet pour les PME modernes
          </h1>
          <p className="landing-hero-subtitle">
            Gerez votre entreprise de A a Z : CRM, Facturation, Comptabilite,
            Stock, RH, Tresorerie. Une solution SaaS francaise, simple et
            puissante.
          </p>
          <div className="landing-hero-actions">
            <Link to="/login" className="landing-btn landing-btn-primary landing-btn-lg">
              Commencer gratuitement
              <ArrowRight size={20} />
            </Link>
            <a href="#demo" className="landing-btn landing-btn-outline landing-btn-lg">
              Demander une demo
            </a>
          </div>
          <div className="landing-hero-stats">
            <div className="landing-stat">
              <span className="landing-stat-value">100%</span>
              <span className="landing-stat-label">Francais</span>
            </div>
            <div className="landing-stat">
              <span className="landing-stat-value">20+</span>
              <span className="landing-stat-label">Modules</span>
            </div>
            <div className="landing-stat">
              <span className="landing-stat-value">RGPD</span>
              <span className="landing-stat-label">Conforme</span>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="landing-section landing-features">
        <div className="landing-container">
          <h2 className="landing-section-title">Pourquoi choisir AZALSCORE ?</h2>
          <div className="landing-features-grid">
            <FeatureCard
              icon={<Zap size={28} />}
              title="Simple et rapide"
              description="Interface intuitive, prise en main immediate. Pas de formation necessaire."
            />
            <FeatureCard
              icon={<Shield size={28} />}
              title="Securise"
              description="Donnees hebergees en France, chiffrement AES-256, authentification 2FA."
            />
            <FeatureCard
              icon={<Globe size={28} />}
              title="Multi-tenant"
              description="Isolation complete des donnees par entreprise. Conformite RGPD."
            />
            <FeatureCard
              icon={<Clock size={28} />}
              title="Temps reel"
              description="Tableaux de bord actualises en temps reel. Decisions eclairees."
            />
            <FeatureCard
              icon={<HeadphonesIcon size={28} />}
              title="Support reactif"
              description="Equipe francaise disponible par chat, email et telephone."
            />
            <FeatureCard
              icon={<CreditCard size={28} />}
              title="Sans engagement"
              description="Abonnement mensuel flexible. Annulez a tout moment."
            />
          </div>
        </div>
      </section>

      {/* Modules Section */}
      <section id="modules" className="landing-section landing-modules">
        <div className="landing-container">
          <h2 className="landing-section-title">Tous les modules dont vous avez besoin</h2>
          <div className="landing-modules-grid">
            <ModuleCard
              icon={<Users size={24} />}
              title="CRM"
              features={[
                'Gestion des clients et prospects',
                'Pipeline commercial',
                'Historique des echanges',
              ]}
            />
            <ModuleCard
              icon={<FileText size={24} />}
              title="Facturation"
              features={[
                'Devis et factures',
                'Factures electroniques',
                'Relances automatiques',
              ]}
            />
            <ModuleCard
              icon={<Package size={24} />}
              title="Stock"
              features={[
                'Gestion des articles',
                'Inventaire en temps reel',
                'Alertes de reapprovisionnement',
              ]}
            />
            <ModuleCard
              icon={<BarChart3 size={24} />}
              title="Comptabilite"
              features={[
                'Plan comptable francais',
                'FEC export',
                'Rapprochement bancaire',
              ]}
            />
            <ModuleCard
              icon={<CreditCard size={24} />}
              title="Tresorerie"
              features={[
                'Suivi des encaissements',
                'Previsions de tresorerie',
                'Multi-devises',
              ]}
            />
            <ModuleCard
              icon={<Users size={24} />}
              title="RH"
              features={[
                'Gestion des employes',
                'Conges et absences',
                'Bulletins de paie',
              ]}
            />
          </div>
        </div>
      </section>

      {/* Demo Request Section */}
      <section id="demo" className="landing-section landing-demo">
        <div className="landing-container">
          <div className="landing-demo-card">
            <h2>Demandez une demonstration personnalisee</h2>
            <p>
              Un expert vous montrera comment AZALSCORE peut transformer votre
              gestion d'entreprise.
            </p>
            {demoSent ? (
              <div className="landing-demo-success">
                <Check size={24} />
                <span>Merci ! Nous vous contacterons sous 24h.</span>
              </div>
            ) : (
              <form onSubmit={handleDemoRequest} className="landing-demo-form">
                <input
                  type="email"
                  placeholder="Votre email professionnel"
                  value={demoEmail}
                  onChange={(e) => setDemoEmail(e.target.value)}
                  required
                />
                <button type="submit" className="landing-btn landing-btn-primary">
                  Demander une demo
                  <ArrowRight size={16} />
                </button>
              </form>
            )}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="landing-section landing-cta">
        <div className="landing-container">
          <h2>Pret a simplifier votre gestion ?</h2>
          <p>Rejoignez les entreprises qui font confiance a AZALSCORE.</p>
          <Link to="/login" className="landing-btn landing-btn-primary landing-btn-lg">
            Commencer maintenant
            <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="landing-container">
          <div className="landing-footer-content">
            <div className="landing-footer-brand">
              <AzalscoreLogo size={32} />
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

export default LandingPage;
