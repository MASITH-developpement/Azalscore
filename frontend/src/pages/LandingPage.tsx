/**
 * AZALSCORE - Landing Page Publique
 * Page d'accueil optimisee pour la conversion et le SEO
 */

import React, { useState } from 'react';
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
  ChevronDown,
  Star,
  Lock,
  Server,
  CheckCircle,
  Factory,
  ShoppingBag,
  Wrench,
  BookOpen,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { COLORS } from '@core/design-tokens';
import DemoVideo from '../components/DemoVideo';
import { StructuredData } from '../components/StructuredData';
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

// Composant FAQ Item
const FAQItem: React.FC<{
  question: string;
  answer: string;
  isOpen: boolean;
  onClick: () => void;
}> = ({ question, answer, isOpen, onClick }) => (
  <div className={`landing-faq-item ${isOpen ? 'open' : ''}`}>
    <div className="landing-faq-question" onClick={onClick}>
      <span>{question}</span>
      <ChevronDown size={20} />
    </div>
    <div className="landing-faq-answer">
      <p>{answer}</p>
    </div>
  </div>
);

// Composant Testimonial Card
const TestimonialCard: React.FC<{
  text: string;
  name: string;
  role: string;
  company: string;
  rating: number;
}> = ({ text, name, role, company, rating }) => (
  <div className="landing-testimonial-card">
    <span className="landing-testimonial-quote">"</span>
    <div className="landing-testimonial-rating">
      {[...Array(5)].map((_, i) => (
        <Star key={i} size={16} fill={i < rating ? '#fbbf24' : 'none'} />
      ))}
    </div>
    <p className="landing-testimonial-text">{text}</p>
    <div className="landing-testimonial-author">
      <div className="landing-testimonial-avatar">
        {name.split(' ').map(n => n[0]).join('')}
      </div>
      <div className="landing-testimonial-info">
        <span className="landing-testimonial-name">{name}</span>
        <span className="landing-testimonial-role">{role}, {company}</span>
      </div>
    </div>
  </div>
);

// Données FAQ
const faqData = [
  {
    question: "Qu'est-ce qu'Azalscore ERP ?",
    answer: "Azalscore est un ERP SaaS français complet pour les PME. Il intègre la gestion commerciale (CRM, devis, factures), la comptabilité, la gestion de stock, les ressources humaines, la trésorerie et bien plus. Solution 100% française, hébergée en France et conforme RGPD."
  },
  {
    question: "Azalscore est-il conforme à la facturation électronique 2026 ?",
    answer: "Oui, Azalscore est entièrement conforme aux exigences de la facturation électronique 2026 en France. Le logiciel supporte les formats Factur-X, l'envoi via PDP (Plateforme de Dématérialisation Partenaire) et l'archivage légal des factures."
  },
  {
    question: "Combien coûte Azalscore ?",
    answer: "Azalscore propose 3 formules : Starter à 29 euros/mois HT pour les TPE (1-3 utilisateurs), Business à 79 euros/mois HT pour les PME en croissance (5-15 utilisateurs), et Enterprise sur devis pour les grandes structures. Un essai gratuit de 30 jours est disponible."
  },
  {
    question: "Mes données sont-elles sécurisées ?",
    answer: "Absolument. Vos données sont hébergées exclusivement en France, chiffrées avec AES-256, et l'accès est protégé par authentification 2FA. Nous sommes conformes RGPD et nos systèmes sont audités régulièrement. Chaque client bénéficie d'une isolation complète de ses données."
  },
  {
    question: "Puis-je importer mes données existantes ?",
    answer: "Oui, Azalscore permet l'import de données depuis Excel, CSV et d'autres ERP. Notre équipe peut vous accompagner dans la migration de vos données clients, produits, factures et historiques."
  },
  {
    question: "Y a-t-il une API pour intégrer Azalscore ?",
    answer: "Oui, Azalscore dispose d'une API REST complète et documentée (OpenAPI/Swagger). Vous pouvez intégrer l'ERP avec vos outils existants, votre site e-commerce, ou développer des automatisations personnalisées."
  },
  {
    question: "Le support est-il inclus ?",
    answer: "Oui, tous les plans incluent un support par email. Les plans Business et Enterprise bénéficient d'un support prioritaire avec des temps de réponse garantis. Le plan Enterprise inclut un support 24/7 dédié."
  },
  {
    question: "Puis-je annuler mon abonnement à tout moment ?",
    answer: "Oui, Azalscore fonctionne sans engagement. Vous pouvez annuler votre abonnement à tout moment depuis votre espace client. Vos données restent accessibles pendant 30 jours après l'annulation pour vous permettre de les exporter."
  }
];

// Données Témoignages
const testimonialData = [
  {
    text: "Depuis que nous utilisons Azalscore, notre gestion administrative a été divisée par deux. L'interface est intuitive et le support est très réactif. Je recommande vivement.",
    name: "Corinne Vangheluwe",
    role: "Dirigeante",
    company: "Vangheluwe Services",
    rating: 5
  },
  {
    text: "La conformité à la facturation électronique 2026 était notre priorité. Azalscore nous a permis d'être prêts bien avant l'échéance. Le module comptabilité est très complet.",
    name: "Sofia Bermejo",
    role: "Expert-Comptable",
    company: "Cabinet Bermejo & Associés",
    rating: 5
  },
  {
    text: "Nous avons migré depuis un ERP complexe et coûteux. Azalscore offre les mêmes fonctionnalités à une fraction du prix. L'équipe nous a accompagnés tout au long de la migration.",
    name: "Stéphane Moreau",
    role: "DAF",
    company: "Moreau Industries",
    rating: 5
  },
  {
    text: "Un ERP complet et accessible pour les PME. La prise en main est rapide et l'équipe technique est toujours disponible pour nous accompagner.",
    name: "Christophe Moreau",
    role: "Gérant",
    company: "Moreau Consulting",
    rating: 5
  }
];

export const LandingPage: React.FC = () => {
  const [demoEmail, setDemoEmail] = useState('');
  const [demoSent, setDemoSent] = useState(false);
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Fermer le menu mobile lors du scroll ou redimensionnement
  React.useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth > 768) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Bloquer le scroll quand le menu mobile est ouvert
  React.useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [mobileMenuOpen]);

  const handleDemoRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!demoEmail) return;

    try {
      await fetch('/api/website/leads', {
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
      {/* Structured Data for SEO */}
      <StructuredData />

      {/* Header */}
      <header className="landing-header" role="banner">
        <div className="landing-header-content">
          <Link to="/" className="landing-logo" aria-label="Azalscore - Accueil">
            <AzalscoreLogo size={36} />
            <span className="landing-logo-text">AZALSCORE</span>
          </Link>

          {/* Navigation Desktop */}
          <nav className="landing-nav" aria-label="Navigation principale">
            <a href="#modules">Modules</a>
            <a href="#pricing">Tarifs</a>

            {/* Dropdown Ressources */}
            <div className="landing-nav-dropdown">
              <button className="landing-nav-dropdown-trigger">
                Ressources <ChevronDown size={14} />
              </button>
              <div className="landing-nav-dropdown-menu">
                <div className="landing-nav-dropdown-section">
                  <span className="landing-nav-dropdown-label">Guides</span>
                  <Link to="/blog/erp-pme-guide-complet">Guide ERP PME</Link>
                  <Link to="/blog/facturation-electronique-2026">Facturation 2026</Link>
                  <Link to="/blog/digitalisation-pme-guide">Digitalisation PME</Link>
                  <Link to="/blog/choix-logiciel-comptabilite-pme">Choisir son logiciel compta</Link>
                </div>
                <div className="landing-nav-dropdown-section">
                  <span className="landing-nav-dropdown-label">Articles</span>
                  <Link to="/blog/erp-vs-excel-pourquoi-migrer">ERP vs Excel</Link>
                  <Link to="/blog/gestion-devis-factures">Gestion Devis & Factures</Link>
                  <Link to="/blog/gestion-tresorerie-pme">Gestion Trésorerie</Link>
                  <Link to="/blog">Tous les articles →</Link>
                </div>
              </div>
            </div>

            {/* Dropdown Comparatifs */}
            <div className="landing-nav-dropdown">
              <button className="landing-nav-dropdown-trigger">
                Comparatifs <ChevronDown size={14} />
              </button>
              <div className="landing-nav-dropdown-menu landing-nav-dropdown-menu--small">
                <Link to="/comparatif/pennylane">vs Pennylane</Link>
                <Link to="/comparatif/odoo">vs Odoo</Link>
                <Link to="/comparatif/sage">vs Sage</Link>
                <Link to="/comparatif/ebp">vs EBP</Link>
                <Link to="/comparatif" className="landing-nav-dropdown-all">Tous les comparatifs →</Link>
              </div>
            </div>

            {/* Dropdown Secteurs */}
            <div className="landing-nav-dropdown">
              <button className="landing-nav-dropdown-trigger">
                Secteurs <ChevronDown size={14} />
              </button>
              <div className="landing-nav-dropdown-menu landing-nav-dropdown-menu--small">
                <Link to="/secteurs/commerce">Commerce & Retail</Link>
                <Link to="/secteurs/services">Services & Consulting</Link>
                <Link to="/secteurs/industrie">Industrie & Production</Link>
              </div>
            </div>

            <Link to="/login" className="landing-btn landing-btn-outline">
              Connexion
            </Link>
            <Link to="/essai-gratuit" className="landing-btn landing-btn-primary">
              Essai gratuit
              <ArrowRight size={16} />
            </Link>
          </nav>

          {/* Bouton Menu Mobile */}
          <button
            className={`landing-menu-toggle ${mobileMenuOpen ? 'active' : ''}`}
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label={mobileMenuOpen ? 'Fermer le menu' : 'Ouvrir le menu'}
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
        </div>

        {/* Navigation Mobile */}
        <nav
          id="mobile-nav"
          className={`landing-mobile-nav ${mobileMenuOpen ? 'active' : ''}`}
          aria-label="Navigation mobile"
        >
          <a href="#modules" onClick={() => setMobileMenuOpen(false)}>Modules</a>
          <a href="#pricing" onClick={() => setMobileMenuOpen(false)}>Tarifs</a>

          <div className="landing-mobile-section">
            <span className="landing-mobile-section-title">Ressources</span>
            <Link to="/blog/erp-pme-guide-complet" onClick={() => setMobileMenuOpen(false)}>Guide ERP PME</Link>
            <Link to="/blog/facturation-electronique-2026" onClick={() => setMobileMenuOpen(false)}>Facturation 2026</Link>
            <Link to="/blog/digitalisation-pme-guide" onClick={() => setMobileMenuOpen(false)}>Digitalisation PME</Link>
            <Link to="/blog/erp-vs-excel-pourquoi-migrer" onClick={() => setMobileMenuOpen(false)}>ERP vs Excel</Link>
            <Link to="/blog" onClick={() => setMobileMenuOpen(false)}>Tous les articles →</Link>
          </div>

          <div className="landing-mobile-section">
            <span className="landing-mobile-section-title">Comparatifs</span>
            <Link to="/comparatif/pennylane" onClick={() => setMobileMenuOpen(false)}>vs Pennylane</Link>
            <Link to="/comparatif/odoo" onClick={() => setMobileMenuOpen(false)}>vs Odoo</Link>
            <Link to="/comparatif/sage" onClick={() => setMobileMenuOpen(false)}>vs Sage</Link>
            <Link to="/comparatif/ebp" onClick={() => setMobileMenuOpen(false)}>vs EBP</Link>
          </div>

          <div className="landing-mobile-section">
            <span className="landing-mobile-section-title">Secteurs</span>
            <Link to="/secteurs/commerce" onClick={() => setMobileMenuOpen(false)}>Commerce & Retail</Link>
            <Link to="/secteurs/services" onClick={() => setMobileMenuOpen(false)}>Services</Link>
            <Link to="/secteurs/industrie" onClick={() => setMobileMenuOpen(false)}>Industrie</Link>
          </div>

          <Link
            to="/login"
            className="landing-btn landing-btn-outline"
            onClick={() => setMobileMenuOpen(false)}
          >
            Connexion
          </Link>
          <Link
            to="/essai-gratuit"
            className="landing-btn landing-btn-primary"
            onClick={() => setMobileMenuOpen(false)}
          >
            Essai gratuit 30 jours
            <ArrowRight size={16} />
          </Link>
        </nav>
      </header>

      {/* Hero Section */}
      <section className="landing-hero" aria-labelledby="hero-title">
        <div className="landing-hero-grid">
          <div className="landing-hero-content">
            <h1 id="hero-title" className="landing-hero-title">
              L'ERP complet pour les PME modernes
            </h1>
            <p className="landing-hero-subtitle">
              Gérez votre entreprise de A à Z : CRM, Facturation, Comptabilité,
              Stock, RH, Trésorerie. Une solution SaaS française, simple et
              puissante.
            </p>
            <div className="landing-hero-actions">
              <Link to="/essai-gratuit" className="landing-btn landing-btn-primary landing-btn-lg">
                Essai gratuit 30 jours
                <ArrowRight size={20} />
              </Link>
              <a href="#demo" className="landing-btn landing-btn-outline landing-btn-lg">
                Demander une demo
              </a>
            </div>
            <div className="landing-hero-stats" role="list" aria-label="Chiffres clés Azalscore">
              <div className="landing-stat" role="listitem">
                <span className="landing-stat-value">100%</span>
                <span className="landing-stat-label">Français</span>
              </div>
              <div className="landing-stat" role="listitem">
                <span className="landing-stat-value">90+</span>
                <span className="landing-stat-label">Modules</span>
              </div>
              <div className="landing-stat" role="listitem">
                <span className="landing-stat-value">RGPD</span>
                <span className="landing-stat-label">Conforme</span>
              </div>
              <div className="landing-stat" role="listitem">
                <span className="landing-stat-value">2026</span>
                <span className="landing-stat-label">E-Facture</span>
              </div>
            </div>
          </div>
          <div className="landing-hero-image">
            <picture>
              <source srcSet="/screenshots/mockup-dashboard.webp" type="image/webp" />
              <img
                src="/screenshots/mockup-dashboard.png"
                alt="Interface AZALSCORE - Tableau de bord ERP avec CRM, Facturation et Gestion"
                loading="eager"
                width="800"
                height="500"
              />
            </picture>
          </div>
        </div>
      </section>

      {/* Trust Badges */}
      <section className="landing-trust-section">
        <div className="landing-container">
          <div className="landing-trust-badges">
            <div className="landing-trust-badge">
              <Shield size={20} />
              <span>Heberge en France</span>
            </div>
            <div className="landing-trust-badge">
              <Lock size={20} />
              <span>Chiffrement AES-256</span>
            </div>
            <div className="landing-trust-badge">
              <CheckCircle size={20} />
              <span>Conforme RGPD</span>
            </div>
            <div className="landing-trust-badge">
              <Server size={20} />
              <span>SLA 99.9%</span>
            </div>
          </div>
        </div>
      </section>

      {/* Demo Video Section */}
      <section id="demo" className="landing-demo-section">
        <div className="landing-container">
          <h2 className="landing-section-title">Découvrez AZALSCORE en action</h2>
          <DemoVideo />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="landing-section landing-features" aria-labelledby="features-title">
        <div className="landing-container">
          <h2 id="features-title" className="landing-section-title">Pourquoi choisir AZALSCORE ?</h2>
          <div className="landing-features-grid">
            <FeatureCard
              icon={<Zap size={28} />}
              title="Simple et rapide"
              description="Interface intuitive, prise en main immédiate. Pas de formation nécessaire."
            />
            <FeatureCard
              icon={<Shield size={28} />}
              title="Sécurisé"
              description="Données hébergées en France, chiffrement AES-256, authentification 2FA."
            />
            <FeatureCard
              icon={<Globe size={28} />}
              title="Multi-tenant"
              description="Isolation complète des données par entreprise. Conformité RGPD."
            />
            <FeatureCard
              icon={<Clock size={28} />}
              title="Temps réel"
              description="Tableaux de bord actualisés en temps réel. Décisions éclairées."
            />
            <FeatureCard
              icon={<HeadphonesIcon size={28} />}
              title="Support réactif"
              description="Équipe française disponible par chat, email et téléphone."
            />
            <FeatureCard
              icon={<CreditCard size={28} />}
              title="Sans engagement"
              description="Abonnement mensuel flexible. Annulez à tout moment."
            />
          </div>
        </div>
      </section>

      {/* Modules Section */}
      <section id="modules" className="landing-section landing-modules" aria-labelledby="modules-title">
        <div className="landing-container">
          <h2 id="modules-title" className="landing-section-title">Tous les modules dont vous avez besoin</h2>
          <div className="landing-modules-grid">
            <ModuleCard
              icon={<Users size={24} />}
              title="CRM"
              features={[
                'Gestion des clients et prospects',
                'Pipeline commercial',
                'Historique des échanges',
              ]}
            />
            <ModuleCard
              icon={<FileText size={24} />}
              title="Facturation"
              features={[
                'Devis et factures',
                'Factures électroniques 2026',
                'Relances automatiques',
              ]}
            />
            <ModuleCard
              icon={<Package size={24} />}
              title="Stock"
              features={[
                'Gestion des articles',
                'Inventaire en temps réel',
                'Alertes de réapprovisionnement',
              ]}
            />
            <ModuleCard
              icon={<BarChart3 size={24} />}
              title="Comptabilité"
              features={[
                'Plan comptable français',
                'Export FEC',
                'Rapprochement bancaire',
              ]}
            />
            <ModuleCard
              icon={<CreditCard size={24} />}
              title="Trésorerie"
              features={[
                'Suivi des encaissements',
                'Prévisions de trésorerie',
                'Multi-devises',
              ]}
            />
            <ModuleCard
              icon={<Users size={24} />}
              title="RH"
              features={[
                'Gestion des employés',
                'Congés et absences',
                'Bulletins de paie',
              ]}
            />
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="landing-section landing-testimonials">
        <div className="landing-container">
          <h2 className="landing-section-title">Ce que nos clients disent</h2>
          <div className="landing-testimonials-grid">
            {testimonialData.map((testimonial, idx) => (
              <TestimonialCard key={idx} {...testimonial} />
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="landing-section landing-pricing" aria-labelledby="pricing-title">
        <div className="landing-container">
          <h2 id="pricing-title" className="landing-section-title">Tarifs simples et transparents</h2>
          <p className="landing-section-subtitle">
            Sans engagement. Annulez à tout moment. Essai gratuit 30 jours.
          </p>
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
                <li><Check size={16} /> 1-3 utilisateurs</li>
                <li><Check size={16} /> Modules essentiels</li>
                <li><Check size={16} /> Facturation électronique</li>
                <li><Check size={16} /> Support email</li>
                <li><Check size={16} /> Mises à jour incluses</li>
              </ul>
              <Link to="/essai-gratuit" className="landing-btn landing-btn-outline landing-btn-block">
                Essayer gratuitement
              </Link>
            </div>

            {/* Business - Recommended */}
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
                <li><Check size={16} /> 5-15 utilisateurs</li>
                <li><Check size={16} /> Tous les modules</li>
                <li><Check size={16} /> Facturation électronique</li>
                <li><Check size={16} /> Support prioritaire</li>
                <li><Check size={16} /> API v3 & intégrations</li>
                <li><Check size={16} /> Rapports avancés</li>
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
                <li><Check size={16} /> Utilisateurs illimités</li>
                <li><Check size={16} /> Tous les modules</li>
                <li><Check size={16} /> Facturation électronique</li>
                <li><Check size={16} /> Support 24/7 dédié</li>
                <li><Check size={16} /> SLA garanti 99.9%</li>
                <li><Check size={16} /> Formation sur site</li>
                <li><Check size={16} /> Personnalisations</li>
              </ul>
              <Link to="/contact" className="landing-btn landing-btn-outline landing-btn-block">
                Nous contacter
              </Link>
            </div>
          </div>
          <p className="landing-pricing-note">
            Tous les plans incluent : hébergement sécurisé en France, conformité RGPD,
            sauvegardes automatiques, chiffrement AES-256.
          </p>
        </div>
      </section>

      {/* Secteurs Section - Internal Linking */}
      <section className="landing-section landing-secteurs" aria-labelledby="secteurs-title">
        <div className="landing-container">
          <h2 id="secteurs-title" className="landing-section-title">Solutions par secteur d'activité</h2>
          <p className="landing-section-subtitle">
            AZALSCORE s'adapte à votre métier avec des fonctionnalités dédiées
          </p>
          <div className="landing-secteurs-grid">
            <Link to="/secteurs/commerce" className="landing-secteur-card">
              <ShoppingBag size={32} className="landing-secteur-icon" />
              <h3>Commerce & Retail</h3>
              <p>Caisse, stock, fidélité client, e-commerce intégré</p>
              <span className="landing-secteur-link">Découvrir <ArrowRight size={14} /></span>
            </Link>
            <Link to="/secteurs/industrie" className="landing-secteur-card">
              <Factory size={32} className="landing-secteur-icon" />
              <h3>Industrie & Production</h3>
              <p>GPAO, qualité, maintenance GMAO, traçabilité</p>
              <span className="landing-secteur-link">Découvrir <ArrowRight size={14} /></span>
            </Link>
            <Link to="/secteurs/services" className="landing-secteur-card">
              <Wrench size={32} className="landing-secteur-icon" />
              <h3>Services & Interventions</h3>
              <p>Planning terrain, devis, facturation, suivi GPS</p>
              <span className="landing-secteur-link">Découvrir <ArrowRight size={14} /></span>
            </Link>
          </div>
        </div>
      </section>

      {/* Blog Section - Internal Linking */}
      <section className="landing-section landing-blog" aria-labelledby="blog-title">
        <div className="landing-container">
          <h2 id="blog-title" className="landing-section-title">Derniers articles</h2>
          <p className="landing-section-subtitle">
            Conseils et actualités pour optimiser votre gestion d'entreprise
          </p>
          <div className="landing-blog-grid">
            <Link to="/blog/erp-vs-excel-pourquoi-migrer" className="landing-blog-card">
              <div className="landing-blog-card-icon"><BarChart3 size={24} /></div>
              <h3>ERP vs Excel : Pourquoi Migrer ?</h3>
              <p>Comparatif complet et guide de transition pour les PME</p>
              <span className="landing-blog-meta">15 min de lecture</span>
            </Link>
            <Link to="/blog/facturation-electronique-2026" className="landing-blog-card">
              <div className="landing-blog-card-icon"><FileText size={24} /></div>
              <h3>Facturation Électronique 2026</h3>
              <p>Guide complet sur les obligations et comment s'y préparer</p>
              <span className="landing-blog-meta">12 min de lecture</span>
            </Link>
            <Link to="/blog/gestion-devis-factures" className="landing-blog-card">
              <div className="landing-blog-card-icon"><CreditCard size={24} /></div>
              <h3>Gestion Devis et Factures</h3>
              <p>Bonnes pratiques pour optimiser votre cycle commercial</p>
              <span className="landing-blog-meta">13 min de lecture</span>
            </Link>
          </div>
          <div className="landing-blog-cta">
            <Link to="/blog" className="landing-btn landing-btn-outline">
              Voir tous les articles
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="landing-section landing-faq" aria-labelledby="faq-title">
        <div className="landing-container">
          <h2 id="faq-title" className="landing-section-title">Questions fréquentes</h2>
          <div className="landing-faq-grid">
            {faqData.map((faq, idx) => (
              <FAQItem
                key={idx}
                question={faq.question}
                answer={faq.answer}
                isOpen={openFaq === idx}
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* Demo Request Section */}
      <section id="demo-request" className="landing-section landing-demo" aria-labelledby="demo-request-title">
        <div className="landing-container">
          <div className="landing-demo-card">
            <h2 id="demo-request-title">Demandez une démonstration personnalisée</h2>
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
      <section className="landing-section landing-cta" aria-labelledby="cta-title">
        <div className="landing-container">
          <h2 id="cta-title">Prêt à simplifier votre gestion ?</h2>
          <p>Rejoignez les entreprises qui font confiance à AZALSCORE.</p>
          <Link to="/essai-gratuit" className="landing-btn landing-btn-primary landing-btn-lg">
            Commencer maintenant - Essai gratuit
            <ArrowRight size={20} />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer" role="contentinfo">
        <div className="landing-container">
          <div className="landing-footer-grid">
            <div className="landing-footer-brand">
              <AzalscoreLogo size={32} />
              <span>AZALSCORE</span>
              <p className="landing-footer-tagline">
                L'ERP français pour les PME modernes
              </p>
            </div>

            <div className="landing-footer-col">
              <h4>Produit</h4>
              <nav aria-label="Liens produit">
                <Link to="/features">Fonctionnalités</Link>
                <Link to="/pricing">Tarifs</Link>
                <Link to="/essai-gratuit">Essai gratuit</Link>
                <Link to="/demo">Demander une démo</Link>
              </nav>
            </div>

            <div className="landing-footer-col">
              <h4>Secteurs</h4>
              <nav aria-label="Liens secteurs">
                <Link to="/secteurs/commerce">Commerce & Retail</Link>
                <Link to="/secteurs/industrie">Industrie</Link>
                <Link to="/secteurs/services">Services</Link>
              </nav>
            </div>

            <div className="landing-footer-col">
              <h4>Ressources</h4>
              <nav aria-label="Liens ressources">
                <Link to="/blog">Blog</Link>
                <Link to="/blog/facturation-electronique-2026">Facturation 2026</Link>
                <Link to="/blog/erp-pme-guide-complet">Guide ERP</Link>
                <Link to="/comparatif">Comparatif ERP</Link>
              </nav>
            </div>

            <div className="landing-footer-col">
              <h4>Entreprise</h4>
              <nav aria-label="Liens légaux">
                <Link to="/contact">Contact</Link>
                <Link to="/mentions-legales">Mentions légales</Link>
                <Link to="/confidentialite">Confidentialité</Link>
                <Link to="/cgv">CGV</Link>
              </nav>
            </div>
          </div>

          <div className="landing-footer-bottom">
            <p className="landing-footer-copy">
              &copy; 2026 AZALSCORE - MASITH Développement. Tous droits réservés.
            </p>
            <p className="landing-footer-badges">
              ERP SaaS français • Hébergé en France • Conforme RGPD • Facturation 2026
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
