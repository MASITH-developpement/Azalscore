/**
 * AZALSCORE - Page Fonctionnalites
 * Liste des modules et fonctionnalites de l'ERP
 */

import React from 'react';
import {
  ArrowRight,
  Check,
  Users,
  FileText,
  Package,
  BarChart3,
  CreditCard,
  Briefcase,
  Wrench,
  ShoppingCart,
  Shield,
  Zap,
  Globe,
  Smartphone,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { StructuredData } from '../../components/StructuredData';
import '../../styles/landing.css';

const modules = [
  {
    icon: <Users size={32} />,
    title: 'CRM',
    description: 'Gestion de la relation client complete',
    features: [
      'Gestion des contacts et entreprises',
      'Pipeline de ventes visuel',
      'Historique des interactions',
      'Segmentation et tags',
      'Automatisation des relances',
    ],
  },
  {
    icon: <FileText size={32} />,
    title: 'Facturation',
    description: 'Devis et factures conformes',
    features: [
      'Devis et factures professionnels',
      'Facturation electronique 2026 (Factur-X)',
      'Relances automatiques',
      'Multi-devises',
      'Export PDF et envoi par email',
    ],
  },
  {
    icon: <BarChart3 size={32} />,
    title: 'Comptabilite',
    description: 'Comptabilite en partie double',
    features: [
      'Plan comptable francais',
      'Saisie assistee des ecritures',
      'Export FEC',
      'Rapprochement bancaire',
      'Bilan et compte de resultat',
    ],
  },
  {
    icon: <Package size={32} />,
    title: 'Inventaire',
    description: 'Gestion de stock en temps reel',
    features: [
      'Multi-entrepots',
      'Mouvements de stock automatiques',
      'Alertes de reapprovisionnement',
      'Inventaire physique',
      'Codes-barres et QR codes',
    ],
  },
  {
    icon: <CreditCard size={32} />,
    title: 'Tresorerie',
    description: 'Suivi de la tresorerie',
    features: [
      'Suivi des encaissements',
      'Previsions de tresorerie',
      'Rapprochement bancaire automatique',
      'Multi-comptes bancaires',
      'Export comptable',
    ],
  },
  {
    icon: <Briefcase size={32} />,
    title: 'Ressources Humaines',
    description: 'Gestion du personnel',
    features: [
      'Fiches employes',
      'Gestion des conges et absences',
      'Suivi du temps de travail',
      'Documents RH',
      'Organigramme',
    ],
  },
  {
    icon: <Wrench size={32} />,
    title: 'Interventions',
    description: 'Gestion du service terrain',
    features: [
      'Planification des interventions',
      'Application mobile techniciens',
      'Rapports d\'intervention',
      'Geolocalisation',
      'Pieces detachees',
    ],
  },
  {
    icon: <ShoppingCart size={32} />,
    title: 'Point de Vente',
    description: 'Caisse et retail',
    features: [
      'Caisse tactile',
      'Gestion des tickets',
      'Paiements multiples',
      'Fidelite clients',
      'Integration stock temps reel',
    ],
  },
];

const FeaturesPage: React.FC = () => {
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
      <section className="landing-hero" style={{ paddingBottom: '60px' }}>
        <div className="landing-hero-content">
          <h1 className="landing-hero-title">
            Toutes les fonctionnalites dont vous avez besoin
          </h1>
          <p className="landing-hero-subtitle">
            Azalscore reunit tous les outils de gestion d'entreprise dans une seule plateforme
            intuitive et puissante.
          </p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="landing-section" style={{ background: '#f8faff' }}>
        <div className="landing-container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(350px, 1fr))', gap: '32px' }}>
            {modules.map((module, idx) => (
              <div key={idx} className="landing-module-card" style={{ padding: '32px' }}>
                <div className="landing-module-header" style={{ marginBottom: '20px' }}>
                  <span className="landing-module-icon" style={{ width: '56px', height: '56px' }}>
                    {module.icon}
                  </span>
                  <div>
                    <h3 className="landing-module-title" style={{ fontSize: '1.5rem' }}>{module.title}</h3>
                    <p style={{ color: '#64748b', margin: 0, fontSize: '0.9rem' }}>{module.description}</p>
                  </div>
                </div>
                <ul className="landing-module-features">
                  {module.features.map((feature, fidx) => (
                    <li key={fidx}>
                      <Check size={16} />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Technical Features */}
      <section className="landing-section">
        <div className="landing-container">
          <h2 className="landing-section-title">Avantages techniques</h2>
          <div className="landing-features-grid">
            <div className="landing-feature-card">
              <div className="landing-feature-icon"><Shield size={28} /></div>
              <h3 className="landing-feature-title">Securite maximale</h3>
              <p className="landing-feature-description">
                Chiffrement AES-256, authentification 2FA, hebergement en France, conformite RGPD.
              </p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon"><Zap size={28} /></div>
              <h3 className="landing-feature-title">API REST complete</h3>
              <p className="landing-feature-description">
                Integrez Azalscore avec vos outils existants grace a notre API documentee (OpenAPI).
              </p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon"><Globe size={28} /></div>
              <h3 className="landing-feature-title">Multi-tenant</h3>
              <p className="landing-feature-description">
                Isolation complete des donnees par entreprise. Chaque client a son espace dedie.
              </p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon"><Smartphone size={28} /></div>
              <h3 className="landing-feature-title">Mobile-first</h3>
              <p className="landing-feature-description">
                Interface responsive et PWA pour travailler depuis n'importe quel appareil.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="landing-section landing-cta">
        <div className="landing-container">
          <h2>Pret a decouvrir Azalscore ?</h2>
          <p>Testez gratuitement pendant 30 jours, sans engagement.</p>
          <Link to="/essai-gratuit" className="landing-btn landing-btn-primary landing-btn-lg">
            Commencer l'essai gratuit
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

export default FeaturesPage;
