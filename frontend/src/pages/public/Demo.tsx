/**
 * AZALSCORE - Page Demo
 * Demande de demonstration personnalisee
 */

import React, { useState } from 'react';
import { ArrowRight, Check, Calendar, Users, Clock, Phone } from 'lucide-react';
import { Link } from 'react-router-dom';
import { StructuredData } from '../../components/StructuredData';
import '../../styles/landing.css';

const DemoPage: React.FC = () => {
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phone: '',
    company: '',
    employees: '',
    message: '',
  });
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      await fetch('/api/website/leads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          full_name: `${formData.firstName} ${formData.lastName}`,
          email: formData.email,
          phone: formData.phone,
          company: formData.company,
          source: 'demo_request',
          message: `Taille: ${formData.employees} employes. ${formData.message}`,
        }),
      });
      setSubmitted(true);
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setLoading(false);
    }
  };

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
            Demandez une demonstration personnalisee
          </h1>
          <p className="landing-hero-subtitle">
            Un expert Azalscore vous presente la solution en fonction de vos besoins specifiques.
          </p>
        </div>
      </section>

      {/* Demo Form */}
      <section className="landing-section" style={{ paddingTop: '20px' }}>
        <div className="landing-container">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '64px', maxWidth: '1000px', margin: '0 auto' }}>

            {/* Benefits */}
            <div>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '24px', color: '#1a1a2e' }}>
                Ce que vous obtiendrez
              </h2>
              <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                {[
                  { icon: <Calendar size={24} />, text: 'Une demonstration de 30 minutes adaptee a votre secteur' },
                  { icon: <Users size={24} />, text: 'Les conseils d\'un expert pour optimiser votre gestion' },
                  { icon: <Clock size={24} />, text: 'Des reponses a toutes vos questions techniques' },
                  { icon: <Phone size={24} />, text: 'Un suivi personnalise apres la demo' },
                ].map((item, idx) => (
                  <li key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '20px' }}>
                    <span style={{ color: '#1E6EFF', flexShrink: 0 }}>{item.icon}</span>
                    <span style={{ color: '#4a5568', fontSize: '1rem' }}>{item.text}</span>
                  </li>
                ))}
              </ul>

              <div style={{ marginTop: '40px', padding: '24px', background: '#f8faff', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <p style={{ margin: 0, color: '#4a5568', fontStyle: 'italic' }}>
                  "La demonstration nous a convaincu. L'expert a pris le temps de comprendre nos processus
                  et nous a montre exactement comment Azalscore pouvait nous aider."
                </p>
                <p style={{ margin: '12px 0 0', fontWeight: 600, color: '#1a1a2e' }}>
                  - Sophie L., Directrice Generale
                </p>
              </div>
            </div>

            {/* Form */}
            <div>
              {submitted ? (
                <div style={{ padding: '48px', textAlign: 'center', background: '#f0fdf4', borderRadius: '16px', border: '1px solid #86efac' }}>
                  <Check size={48} style={{ color: '#22c55e', marginBottom: '16px' }} />
                  <h3 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#1a1a2e', marginBottom: '12px' }}>
                    Demande envoyee
                  </h3>
                  <p style={{ color: '#4a5568' }}>
                    Notre equipe vous contactera sous 24h pour planifier votre demonstration.
                  </p>
                </div>
              ) : (
                <form onSubmit={handleSubmit} style={{ background: 'white', padding: '32px', borderRadius: '16px', border: '1px solid #e2e8f0' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>Prenom *</label>
                      <input
                        type="text"
                        required
                        value={formData.firstName}
                        onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                        style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '1rem' }}
                      />
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>Nom *</label>
                      <input
                        type="text"
                        required
                        value={formData.lastName}
                        onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                        style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '1rem' }}
                      />
                    </div>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>Email professionnel *</label>
                    <input
                      type="email"
                      required
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '1rem' }}
                    />
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>Telephone</label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '1rem' }}
                    />
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>Entreprise *</label>
                    <input
                      type="text"
                      required
                      value={formData.company}
                      onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                      style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '1rem' }}
                    />
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>Nombre d'employes</label>
                    <select
                      value={formData.employees}
                      onChange={(e) => setFormData({ ...formData, employees: e.target.value })}
                      style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '1rem' }}
                    >
                      <option value="">Selectionnez</option>
                      <option value="1-5">1-5</option>
                      <option value="6-10">6-10</option>
                      <option value="11-50">11-50</option>
                      <option value="51-200">51-200</option>
                      <option value="200+">200+</option>
                    </select>
                  </div>

                  <div style={{ marginBottom: '24px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: 500, color: '#374151' }}>Message (optionnel)</label>
                    <textarea
                      value={formData.message}
                      onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                      rows={3}
                      placeholder="Decrivez vos besoins..."
                      style={{ width: '100%', padding: '12px', border: '1px solid #d1d5db', borderRadius: '8px', fontSize: '1rem', resize: 'vertical' }}
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={loading}
                    className="landing-btn landing-btn-primary landing-btn-block"
                    style={{ opacity: loading ? 0.7 : 1 }}
                  >
                    {loading ? 'Envoi en cours...' : 'Demander ma demonstration'}
                    <ArrowRight size={16} />
                  </button>
                </form>
              )}
            </div>
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

export default DemoPage;
