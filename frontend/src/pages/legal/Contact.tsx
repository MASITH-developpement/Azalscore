/**
 * AZALSCORE - Page Contact
 * Formulaire de contact avec intégration API tracking
 */

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowLeft,
  Send,
  Mail,
  Phone,
  MapPin,
  MessageSquare,
  Building,
  User,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import '../styles/legal.css';

interface ContactForm {
  name: string;
  email: string;
  company: string;
  phone: string;
  subject: string;
  message: string;
}

const Contact: React.FC = () => {
  const [form, setForm] = useState<ContactForm>({
    name: '',
    email: '',
    company: '',
    phone: '',
    subject: 'general',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [errorMessage, setErrorMessage] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setForm(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setSubmitStatus('idle');
    setErrorMessage('');

    try {
      const response = await fetch('/api/v3/website/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          full_name: form.name,
          email: form.email,
          company: form.company || undefined,
          phone: form.phone || undefined,
          subject: form.subject,
          message: form.message
        }),
      });

      if (response.ok) {
        setSubmitStatus('success');
        setForm({
          name: '',
          email: '',
          company: '',
          phone: '',
          subject: 'general',
          message: ''
        });
      } else {
        const data = await response.json();
        throw new Error(data.detail || 'Erreur lors de l\'envoi');
      }
    } catch (error) {
      setSubmitStatus('error');
      setErrorMessage(error instanceof Error ? error.message : 'Une erreur est survenue');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="legal-page contact-page">
      <header className="legal-header">
        <div className="legal-header-content">
          <Link to="/" className="legal-back-link">
            <ArrowLeft size={20} />
            Retour à l'accueil
          </Link>
          <Link to="/" className="legal-logo">
            <span className="logo-azal">AZAL</span>
            <span className="logo-score">SCORE</span>
          </Link>
        </div>
      </header>

      <main className="legal-content contact-content">
        <h1>Contactez-nous</h1>
        <p className="contact-intro">
          Une question sur AZALSCORE ? Besoin d'informations sur nos offres ?
          Notre équipe est à votre disposition.
        </p>

        <div className="contact-grid">
          {/* Formulaire de contact */}
          <div className="contact-form-section">
            <h2>
              <MessageSquare size={24} />
              Envoyez-nous un message
            </h2>

            {submitStatus === 'success' ? (
              <div className="contact-success">
                <CheckCircle size={48} />
                <h3>Message envoyé !</h3>
                <p>
                  Merci pour votre message. Notre équipe vous répondra
                  dans les meilleurs délais (généralement sous 24h ouvrées).
                </p>
                <button
                  type="button"
                  className="contact-btn-secondary"
                  onClick={() => setSubmitStatus('idle')}
                >
                  Envoyer un autre message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="contact-form">
                {submitStatus === 'error' && (
                  <div className="contact-error">
                    <AlertCircle size={20} />
                    <span>{errorMessage || 'Une erreur est survenue. Veuillez réessayer.'}</span>
                  </div>
                )}

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="name">
                      <User size={16} />
                      Nom complet *
                    </label>
                    <input
                      type="text"
                      id="name"
                      name="name"
                      value={form.name}
                      onChange={handleChange}
                      required
                      placeholder="Jean Dupont"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="email">
                      <Mail size={16} />
                      Email professionnel *
                    </label>
                    <input
                      type="email"
                      id="email"
                      name="email"
                      value={form.email}
                      onChange={handleChange}
                      required
                      placeholder="jean.dupont@entreprise.com"
                    />
                  </div>
                </div>

                <div className="form-row">
                  <div className="form-group">
                    <label htmlFor="company">
                      <Building size={16} />
                      Entreprise
                    </label>
                    <input
                      type="text"
                      id="company"
                      name="company"
                      value={form.company}
                      onChange={handleChange}
                      placeholder="Nom de votre entreprise"
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="phone">
                      <Phone size={16} />
                      Téléphone
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={form.phone}
                      onChange={handleChange}
                      placeholder="+33 1 23 45 67 89"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label htmlFor="subject">Sujet *</label>
                  <select
                    id="subject"
                    name="subject"
                    value={form.subject}
                    onChange={handleChange}
                    required
                  >
                    <option value="general">Question générale</option>
                    <option value="demo">Demande de démonstration</option>
                    <option value="pricing">Informations tarifaires</option>
                    <option value="support">Support technique</option>
                    <option value="partnership">Partenariat</option>
                    <option value="other">Autre</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="message">Message *</label>
                  <textarea
                    id="message"
                    name="message"
                    value={form.message}
                    onChange={handleChange}
                    required
                    rows={6}
                    placeholder="Décrivez votre demande en détail..."
                  />
                </div>

                <div className="form-consent">
                  <p>
                    En soumettant ce formulaire, vous acceptez notre{' '}
                    <Link to="/confidentialite">Politique de Confidentialité</Link>.
                    Vos données seront utilisées uniquement pour répondre à votre demande.
                  </p>
                </div>

                <button
                  type="submit"
                  className="contact-submit"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <span className="spinner" />
                      Envoi en cours...
                    </>
                  ) : (
                    <>
                      <Send size={20} />
                      Envoyer le message
                    </>
                  )}
                </button>
              </form>
            )}
          </div>

          {/* Informations de contact */}
          <div className="contact-info-section">
            <h2>Autres moyens de nous joindre</h2>

            <div className="contact-info-card">
              <div className="contact-info-icon">
                <Mail size={24} />
              </div>
              <div className="contact-info-content">
                <h3>Email</h3>
                <p>
                  <a href="mailto:contact@azalscore.com">contact@azalscore.com</a>
                </p>
                <p className="contact-info-note">Réponse sous 24h ouvrées</p>
              </div>
            </div>

            <div className="contact-info-card">
              <div className="contact-info-icon">
                <Phone size={24} />
              </div>
              <div className="contact-info-content">
                <h3>Téléphone</h3>
                <p>
                  <a href="tel:+33123456789">+33 1 23 45 67 89</a>
                </p>
                <p className="contact-info-note">Lun-Ven : 9h-18h (CET)</p>
              </div>
            </div>

            <div className="contact-info-card">
              <div className="contact-info-icon">
                <MapPin size={24} />
              </div>
              <div className="contact-info-content">
                <h3>Adresse</h3>
                <address>
                  MASITH Développement<br />
                  Paris, France
                </address>
              </div>
            </div>

            <div className="contact-support-box">
              <h3>Support client</h3>
              <p>
                Vous êtes déjà client AZALSCORE ? Accédez à votre espace
                support pour une assistance prioritaire.
              </p>
              <Link to="/login" className="contact-support-link">
                Accéder au support →
              </Link>
            </div>

            <div className="contact-demo-box">
              <h3>Découvrir AZALSCORE</h3>
              <p>
                Vous souhaitez voir AZALSCORE en action ? Demandez une
                démonstration personnalisée gratuite.
              </p>
              <Link to="/#demo" className="contact-demo-link">
                Demander une démo →
              </Link>
            </div>
          </div>
        </div>
      </main>

      <footer className="legal-footer">
        <div className="legal-footer-content">
          <p>&copy; {new Date().getFullYear()} AZALSCORE - MASITH Développement. Tous droits réservés.</p>
          <nav className="legal-footer-nav">
            <Link to="/mentions-legales">Mentions légales</Link>
            <Link to="/confidentialite">Confidentialité</Link>
            <Link to="/cgv">CGV</Link>
            <Link to="/contact">Contact</Link>
          </nav>
        </div>
      </footer>
    </div>
  );
};

export default Contact;
