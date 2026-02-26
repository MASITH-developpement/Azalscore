/**
 * AZALSCORE - Page A propos
 * Presentation de l'entreprise et de la solution
 */

import React from 'react';
import { ArrowRight, Shield, Globe, Zap, Users } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StructuredData } from '../../components/StructuredData';
import '../../styles/landing.css';

const AboutPage: React.FC = () => {
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
      <section className="landing-hero">
        <div className="landing-hero-content">
          <h1 className="landing-hero-title">
            A propos d'Azalscore
          </h1>
          <p className="landing-hero-subtitle">
            Une solution ERP francaise conçue pour simplifier la gestion des PME.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section className="landing-section">
        <div className="landing-container">
          <div style={{ maxWidth: '800px', margin: '0 auto', textAlign: 'center' }}>
            <h2 className="landing-section-title">Notre mission</h2>
            <p style={{ fontSize: '1.25rem', color: '#4a5568', lineHeight: 1.8 }}>
              Chez Azalscore, nous croyons que la gestion d'entreprise ne devrait pas etre compliquee.
              Notre mission est de fournir aux PME francaises un outil simple, puissant et abordable
              pour gerer l'ensemble de leurs activites : de la relation client a la comptabilite,
              en passant par la facturation et la gestion de stock.
            </p>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="landing-section" style={{ background: '#f8faff' }}>
        <div className="landing-container">
          <h2 className="landing-section-title">Nos valeurs</h2>
          <div className="landing-features-grid">
            <div className="landing-feature-card">
              <div className="landing-feature-icon"><Shield size={28} /></div>
              <h3 className="landing-feature-title">Souverainete des donnees</h3>
              <p className="landing-feature-description">
                Vos donnees restent en France. Nous garantissons un hebergement securise
                et conforme aux reglementations europeennes (RGPD).
              </p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon"><Zap size={28} /></div>
              <h3 className="landing-feature-title">Simplicite</h3>
              <p className="landing-feature-description">
                Nous concevons des interfaces intuitives qui ne necessitent pas de formation.
                Vous etes productif des le premier jour.
              </p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon"><Globe size={28} /></div>
              <h3 className="landing-feature-title">Innovation</h3>
              <p className="landing-feature-description">
                Nous integrons les dernieres technologies (IA, automatisation) pour vous faire
                gagner du temps au quotidien.
              </p>
            </div>
            <div className="landing-feature-card">
              <div className="landing-feature-icon"><Users size={28} /></div>
              <h3 className="landing-feature-title">Proximite</h3>
              <p className="landing-feature-description">
                Notre equipe de support est francaise et reactive. Nous sommes la pour vous
                accompagner dans votre croissance.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Company */}
      <section className="landing-section">
        <div className="landing-container">
          <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h2 className="landing-section-title">MASITH Developpement</h2>
            <p style={{ fontSize: '1.1rem', color: '#4a5568', lineHeight: 1.8, textAlign: 'center' }}>
              Azalscore est developpe par MASITH Developpement, une entreprise francaise specialisee
              dans les solutions logicielles pour entreprises. Notre equipe d'ingenieurs et de
              designers travaille chaque jour pour ameliorer la plateforme et repondre aux besoins
              de nos clients.
            </p>
            <div style={{ display: 'flex', justifyContent: 'center', gap: '48px', marginTop: '48px' }}>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '2.5rem', fontWeight: 700, color: '#1E6EFF' }}>2024</span>
                <p style={{ color: '#64748b', marginTop: '8px' }}>Fondation</p>
              </div>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '2.5rem', fontWeight: 700, color: '#1E6EFF' }}>100%</span>
                <p style={{ color: '#64748b', marginTop: '8px' }}>Francais</p>
              </div>
              <div style={{ textAlign: 'center' }}>
                <span style={{ fontSize: '2.5rem', fontWeight: 700, color: '#1E6EFF' }}>20+</span>
                <p style={{ color: '#64748b', marginTop: '8px' }}>Modules</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="landing-section landing-cta">
        <div className="landing-container">
          <h2>Envie d'en savoir plus ?</h2>
          <p>Contactez-nous ou testez gratuitement Azalscore.</p>
          <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/contact" className="landing-btn landing-btn-outline landing-btn-lg">
              Nous contacter
            </Link>
            <Link to="/essai-gratuit" className="landing-btn landing-btn-primary landing-btn-lg">
              Essai gratuit
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

export default AboutPage;
