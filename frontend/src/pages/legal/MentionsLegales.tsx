/**
 * AZALSCORE - Mentions Légales
 * Page des mentions légales obligatoires
 */

import React from 'react';
import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import '../styles/legal.css';

const MentionsLegales: React.FC = () => {
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
        <h1>Mentions Légales</h1>
        <p className="legal-updated">Dernière mise à jour : Février 2026</p>

        <section className="legal-section">
          <h2>1. Éditeur du site</h2>
          <p>
            Le site <strong>azalscore.com</strong> est édité par :
          </p>
          <address>
            <strong>MASITH Développement</strong><br />
            Société par Actions Simplifiée (SAS)<br />
            Capital social : 10 000 €<br />
            Siège social : Paris, France<br />
            RCS Paris : [Numéro à compléter]<br />
            SIRET : [Numéro à compléter]<br />
            TVA Intracommunautaire : FR [Numéro à compléter]
          </address>
        </section>

        <section className="legal-section">
          <h2>2. Directeur de la publication</h2>
          <p>
            Le directeur de la publication est le représentant légal de MASITH Développement.
          </p>
        </section>

        <section className="legal-section">
          <h2>3. Hébergement</h2>
          <p>
            Le site est hébergé par :
          </p>
          <address>
            <strong>OVHcloud</strong><br />
            2 rue Kellermann<br />
            59100 Roubaix, France<br />
            Téléphone : +33 9 72 10 10 07
          </address>
        </section>

        <section className="legal-section">
          <h2>4. Propriété intellectuelle</h2>
          <p>
            L'ensemble du contenu du site azalscore.com (textes, images, vidéos, logos,
            icônes, sons, logiciels, base de données, etc.) est protégé par le droit
            d'auteur et le droit des marques.
          </p>
          <p>
            AZALSCORE est une marque déposée de MASITH Développement. Toute reproduction,
            représentation, modification, publication, adaptation de tout ou partie des
            éléments du site est interdite, sauf autorisation écrite préalable.
          </p>
          <p>
            AZALSCORE ERP est un logiciel propriétaire. Toute reproduction, copie,
            distribution ou utilisation non autorisée du code source est strictement
            interdite et constitue une contrefaçon sanctionnée par le Code de la
            propriété intellectuelle.
          </p>
        </section>

        <section className="legal-section">
          <h2>5. Données personnelles</h2>
          <p>
            Les informations concernant la collecte et le traitement des données
            personnelles sont détaillées dans notre{' '}
            <Link to="/confidentialite">Politique de Confidentialité</Link>.
          </p>
          <p>
            Conformément au Règlement Général sur la Protection des Données (RGPD)
            et à la loi Informatique et Libertés, vous disposez d'un droit d'accès,
            de rectification, de suppression et de portabilité de vos données.
          </p>
        </section>

        <section className="legal-section">
          <h2>6. Cookies</h2>
          <p>
            Le site utilise des cookies pour améliorer l'expérience utilisateur et
            analyser le trafic. Vous pouvez paramétrer votre navigateur pour refuser
            les cookies. Pour plus d'informations, consultez notre{' '}
            <Link to="/confidentialite">Politique de Confidentialité</Link>.
          </p>
        </section>

        <section className="legal-section">
          <h2>7. Limitation de responsabilité</h2>
          <p>
            MASITH Développement s'efforce d'assurer l'exactitude et la mise à jour
            des informations diffusées sur ce site, dont elle se réserve le droit de
            corriger le contenu à tout moment et sans préavis.
          </p>
          <p>
            MASITH Développement décline toute responsabilité en cas d'interruption
            ou d'inaccessibilité du site, de survenance de bugs ou de tout dommage
            résultant d'une intrusion frauduleuse d'un tiers.
          </p>
        </section>

        <section className="legal-section">
          <h2>8. Droit applicable</h2>
          <p>
            Les présentes mentions légales sont régies par le droit français.
            En cas de litige, les tribunaux français seront seuls compétents.
          </p>
        </section>

        <section className="legal-section">
          <h2>9. Contact</h2>
          <p>
            Pour toute question concernant ces mentions légales, vous pouvez nous
            contacter via notre <Link to="/contact">formulaire de contact</Link> ou
            par email à : <a href="mailto:legal@azalscore.com">legal@azalscore.com</a>
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

export default MentionsLegales;
