/**
 * AZALSCORE - Page Documentation
 * Centre de ressources et documentation
 */

import React from 'react';
import {
  ArrowRight,
  BookOpen,
  Play,
  FileText,
  HelpCircle,
  Code,
  Zap,
  MessageSquare,
  ExternalLink,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { StructuredData } from '../../components/StructuredData';
import '../../styles/landing.css';

const resources = [
  {
    icon: <BookOpen size={32} />,
    title: 'Guide de demarrage',
    description: 'Apprenez les bases d\'Azalscore en quelques minutes',
    link: '#getting-started',
    badge: 'Populaire',
  },
  {
    icon: <Play size={32} />,
    title: 'Tutoriels video',
    description: 'Regardez nos guides pas-a-pas en video',
    link: '#videos',
    badge: null,
  },
  {
    icon: <FileText size={32} />,
    title: 'Documentation modules',
    description: 'Documentation detaillee de chaque module',
    link: '#modules',
    badge: null,
  },
  {
    icon: <Code size={32} />,
    title: 'API Reference',
    description: 'Documentation technique de l\'API REST',
    link: '/api/docs',
    badge: 'Developpeurs',
  },
  {
    icon: <HelpCircle size={32} />,
    title: 'FAQ',
    description: 'Reponses aux questions les plus frequentes',
    link: '/#faq',
    badge: null,
  },
  {
    icon: <MessageSquare size={32} />,
    title: 'Support',
    description: 'Contactez notre equipe de support',
    link: '/contact',
    badge: null,
  },
];

const quickGuides = [
  {
    title: 'Creer votre premiere facture',
    duration: '5 min',
    category: 'Facturation',
  },
  {
    title: 'Importer vos contacts existants',
    duration: '10 min',
    category: 'CRM',
  },
  {
    title: 'Configurer votre plan comptable',
    duration: '15 min',
    category: 'Comptabilite',
  },
  {
    title: 'Gerer votre inventaire',
    duration: '10 min',
    category: 'Stock',
  },
  {
    title: 'Planifier des interventions',
    duration: '8 min',
    category: 'Interventions',
  },
  {
    title: 'Connecter votre compte bancaire',
    duration: '5 min',
    category: 'Tresorerie',
  },
];

const DocsPage: React.FC = () => {
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
            Centre de documentation
          </h1>
          <p className="landing-hero-subtitle">
            Tout ce dont vous avez besoin pour maitriser Azalscore.
            Guides, tutoriels et documentation technique.
          </p>
        </div>
      </section>

      {/* Resources Grid */}
      <section className="landing-section" style={{ background: '#f8faff', paddingTop: '40px' }}>
        <div className="landing-container">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            {resources.map((resource, idx) => (
              <Link
                key={idx}
                to={resource.link}
                style={{
                  display: 'block',
                  padding: '28px',
                  background: 'white',
                  borderRadius: '16px',
                  border: '1px solid #e5e7eb',
                  textDecoration: 'none',
                  transition: 'all 0.2s ease',
                  position: 'relative',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 12px 24px rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                {resource.badge && (
                  <span style={{
                    position: 'absolute',
                    top: '16px',
                    right: '16px',
                    background: '#1E6EFF',
                    color: 'white',
                    padding: '4px 10px',
                    borderRadius: '20px',
                    fontSize: '0.75rem',
                    fontWeight: 600,
                  }}>
                    {resource.badge}
                  </span>
                )}
                <span style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  width: '56px',
                  height: '56px',
                  background: '#e8f0fe',
                  borderRadius: '12px',
                  color: '#1E6EFF',
                  marginBottom: '16px',
                }}>
                  {resource.icon}
                </span>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 700, color: '#1a1a2e', marginBottom: '8px' }}>
                  {resource.title}
                </h3>
                <p style={{ color: '#4a5568', margin: 0 }}>
                  {resource.description}
                </p>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Quick Guides */}
      <section className="landing-section" id="getting-started">
        <div className="landing-container">
          <h2 className="landing-section-title">Guides rapides</h2>
          <p style={{ textAlign: 'center', color: '#64748b', marginTop: '-32px', marginBottom: '40px' }}>
            Maitrisez les fonctionnalites essentielles en quelques minutes
          </p>
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            {quickGuides.map((guide, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '20px 24px',
                  background: idx % 2 === 0 ? '#f8faff' : 'white',
                  borderRadius: idx === 0 ? '12px 12px 0 0' : idx === quickGuides.length - 1 ? '0 0 12px 12px' : 0,
                  border: '1px solid #e5e7eb',
                  borderTop: idx === 0 ? '1px solid #e5e7eb' : 'none',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                  <Zap size={20} style={{ color: '#1E6EFF' }} />
                  <div>
                    <h4 style={{ margin: 0, fontWeight: 600, color: '#1a1a2e' }}>{guide.title}</h4>
                    <span style={{ fontSize: '0.875rem', color: '#64748b' }}>{guide.category}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <span style={{ fontSize: '0.875rem', color: '#64748b' }}>{guide.duration}</span>
                  <ExternalLink size={16} style={{ color: '#1E6EFF' }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* API Section */}
      <section className="landing-section" style={{ background: '#1a1a2e', color: 'white' }} id="api">
        <div className="landing-container">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '32px' }}>
            <div>
              <h2 style={{ fontSize: '2rem', fontWeight: 700, marginBottom: '16px' }}>API REST</h2>
              <p style={{ opacity: 0.8, maxWidth: '500px', margin: 0 }}>
                Integrez Azalscore avec vos outils grace a notre API complete et documentee.
                Specification OpenAPI 3.1 disponible.
              </p>
            </div>
            <a
              href="/api/v2/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="landing-btn landing-btn-primary"
            >
              Voir la documentation API
              <ExternalLink size={16} />
            </a>
          </div>
        </div>
      </section>

      {/* Support CTA */}
      <section className="landing-section">
        <div className="landing-container">
          <div style={{ textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
            <h2 className="landing-section-title">Besoin d'aide ?</h2>
            <p style={{ color: '#4a5568', marginBottom: '32px' }}>
              Notre equipe de support est disponible pour repondre a vos questions
              et vous accompagner dans l'utilisation d'Azalscore.
            </p>
            <Link to="/contact" className="landing-btn landing-btn-primary landing-btn-lg">
              Contacter le support
              <ArrowRight size={20} />
            </Link>
          </div>
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

export default DocsPage;
