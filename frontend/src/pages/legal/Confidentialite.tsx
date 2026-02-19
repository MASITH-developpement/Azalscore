/**
 * AZALSCORE - Politique de Confidentialité
 * Page de politique de confidentialité RGPD compliant
 */

import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import '../styles/legal.css';

const Confidentialite: React.FC = () => {
  return (
    <div className="legal-page">
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

      <main className="legal-content">
        <h1>Politique de Confidentialité</h1>
        <p className="legal-updated">Dernière mise à jour : Février 2026</p>

        <section className="legal-section">
          <h2>1. Introduction</h2>
          <p>
            MASITH Développement, éditeur d'AZALSCORE, s'engage à protéger la vie privée
            des utilisateurs de ses services. Cette politique de confidentialité décrit
            comment nous collectons, utilisons et protégeons vos données personnelles
            conformément au Règlement Général sur la Protection des Données (RGPD).
          </p>
        </section>

        <section className="legal-section">
          <h2>2. Responsable du traitement</h2>
          <address>
            <strong>MASITH Développement</strong><br />
            Siège social : Paris, France<br />
            Email : <a href="mailto:dpo@azalscore.com">dpo@azalscore.com</a>
          </address>
        </section>

        <section className="legal-section">
          <h2>3. Données collectées</h2>
          <p>Nous collectons les catégories de données suivantes :</p>

          <h3>3.1 Données d'identification</h3>
          <ul>
            <li>Nom et prénom</li>
            <li>Adresse email professionnelle</li>
            <li>Numéro de téléphone</li>
            <li>Nom de l'entreprise et fonction</li>
          </ul>

          <h3>3.2 Données de connexion</h3>
          <ul>
            <li>Adresse IP</li>
            <li>Type de navigateur et système d'exploitation</li>
            <li>Pages visitées et durée de visite</li>
            <li>Date et heure de connexion</li>
          </ul>

          <h3>3.3 Données d'utilisation (pour les utilisateurs ERP)</h3>
          <ul>
            <li>Données métier saisies dans l'application</li>
            <li>Historique des actions et modifications</li>
            <li>Préférences de configuration</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>4. Finalités du traitement</h2>
          <p>Vos données sont traitées pour les finalités suivantes :</p>
          <ul>
            <li><strong>Fourniture du service</strong> : création et gestion de compte, accès à l'ERP</li>
            <li><strong>Communication</strong> : réponse aux demandes, notifications de service</li>
            <li><strong>Amélioration</strong> : analyse d'usage pour améliorer nos services</li>
            <li><strong>Marketing</strong> : envoi d'informations commerciales (avec consentement)</li>
            <li><strong>Obligations légales</strong> : conformité fiscale et légale</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>5. Base légale du traitement</h2>
          <p>Le traitement de vos données repose sur :</p>
          <ul>
            <li><strong>L'exécution du contrat</strong> : pour la fourniture des services AZALSCORE</li>
            <li><strong>Le consentement</strong> : pour les communications marketing</li>
            <li><strong>L'intérêt légitime</strong> : pour l'amélioration de nos services</li>
            <li><strong>Les obligations légales</strong> : conservation des données comptables</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>6. Durée de conservation</h2>
          <ul>
            <li><strong>Données de compte</strong> : durée de la relation contractuelle + 3 ans</li>
            <li><strong>Données de navigation</strong> : 13 mois maximum</li>
            <li><strong>Données comptables</strong> : 10 ans (obligation légale)</li>
            <li><strong>Demandes de contact</strong> : 3 ans après le dernier contact</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>7. Destinataires des données</h2>
          <p>Vos données peuvent être transmises à :</p>
          <ul>
            <li>Nos équipes internes (support, technique, commercial)</li>
            <li>Nos sous-traitants techniques (hébergement, email)</li>
            <li>Les autorités compétentes en cas d'obligation légale</li>
          </ul>
          <p>
            Nous ne vendons jamais vos données à des tiers. Tous nos sous-traitants
            sont soumis à des obligations contractuelles de confidentialité.
          </p>
        </section>

        <section className="legal-section">
          <h2>8. Transferts hors UE</h2>
          <p>
            Vos données sont hébergées en France/Union Européenne. En cas de transfert
            vers des pays tiers, nous veillons à ce que des garanties appropriées
            soient en place (clauses contractuelles types, décision d'adéquation).
          </p>
        </section>

        <section className="legal-section">
          <h2>9. Sécurité des données</h2>
          <p>Nous mettons en œuvre les mesures de sécurité suivantes :</p>
          <ul>
            <li>Chiffrement des données en transit (HTTPS/TLS)</li>
            <li>Chiffrement des données sensibles au repos</li>
            <li>Authentification forte et gestion des accès</li>
            <li>Sauvegardes régulières et tests de restauration</li>
            <li>Surveillance et détection des intrusions</li>
            <li>Formation de nos équipes à la sécurité</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>10. Cookies</h2>
          <p>Notre site utilise des cookies :</p>
          <ul>
            <li><strong>Cookies essentiels</strong> : fonctionnement du site (session, authentification)</li>
            <li><strong>Cookies analytiques</strong> : mesure d'audience (avec consentement)</li>
            <li><strong>Cookies de préférence</strong> : mémorisation de vos choix</li>
          </ul>
          <p>
            Vous pouvez gérer vos préférences de cookies via les paramètres de votre
            navigateur ou notre bandeau de consentement.
          </p>
        </section>

        <section className="legal-section">
          <h2>11. Vos droits</h2>
          <p>Conformément au RGPD, vous disposez des droits suivants :</p>
          <ul>
            <li><strong>Droit d'accès</strong> : obtenir une copie de vos données</li>
            <li><strong>Droit de rectification</strong> : corriger vos données</li>
            <li><strong>Droit à l'effacement</strong> : demander la suppression de vos données</li>
            <li><strong>Droit à la portabilité</strong> : recevoir vos données dans un format structuré</li>
            <li><strong>Droit d'opposition</strong> : vous opposer au traitement</li>
            <li><strong>Droit à la limitation</strong> : limiter le traitement</li>
            <li><strong>Droit de retrait du consentement</strong> : à tout moment</li>
          </ul>
          <p>
            Pour exercer ces droits, contactez-nous à{' '}
            <a href="mailto:dpo@azalscore.com">dpo@azalscore.com</a> ou via notre{' '}
            <Link to="/contact">formulaire de contact</Link>.
          </p>
        </section>

        <section className="legal-section">
          <h2>12. Réclamation</h2>
          <p>
            Si vous estimez que le traitement de vos données ne respecte pas la
            réglementation, vous pouvez introduire une réclamation auprès de la CNIL :
          </p>
          <address>
            <strong>CNIL - Commission Nationale de l'Informatique et des Libertés</strong><br />
            3 Place de Fontenoy, TSA 80715<br />
            75334 Paris Cedex 07<br />
            Site : <a href="https://www.cnil.fr" target="_blank" rel="noopener noreferrer">www.cnil.fr</a>
          </address>
        </section>

        <section className="legal-section">
          <h2>13. Modifications</h2>
          <p>
            Cette politique de confidentialité peut être modifiée pour refléter
            les évolutions légales ou de nos pratiques. La date de mise à jour
            est indiquée en haut de page. Nous vous informerons des modifications
            significatives par email ou notification.
          </p>
        </section>
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

export default Confidentialite;
