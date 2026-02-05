/**
 * AZALSCORE - Conditions Générales de Vente
 * Page CGV pour les services AZALSCORE ERP SaaS
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import '../styles/legal.css';

const CGV: React.FC = () => {
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
        <h1>Conditions Générales de Vente</h1>
        <p className="legal-updated">Dernière mise à jour : Février 2026</p>

        <section className="legal-section">
          <h2>1. Objet et champ d'application</h2>
          <p>
            Les présentes Conditions Générales de Vente (CGV) régissent les relations
            contractuelles entre MASITH Développement, éditeur de la solution AZALSCORE ERP,
            et tout client professionnel (ci-après "le Client") souscrivant aux services.
          </p>
          <p>
            Toute souscription implique l'acceptation sans réserve des présentes CGV.
          </p>
        </section>

        <section className="legal-section">
          <h2>2. Description des services</h2>
          <p>AZALSCORE propose une solution ERP SaaS comprenant :</p>
          <ul>
            <li>Modules de gestion : CRM, Comptabilité, Facturation, Inventaire, RH, POS</li>
            <li>Hébergement cloud sécurisé multi-tenant</li>
            <li>Mises à jour et maintenance incluses</li>
            <li>Support technique selon la formule choisie</li>
            <li>Sauvegardes automatiques quotidiennes</li>
            <li>API pour intégrations tierces</li>
          </ul>
        </section>

        <section className="legal-section">
          <h2>3. Offres et tarification</h2>

          <h3>3.1 Formules d'abonnement</h3>
          <table className="legal-table">
            <thead>
              <tr>
                <th>Formule</th>
                <th>Utilisateurs</th>
                <th>Modules</th>
                <th>Support</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Starter</td>
                <td>1-5</td>
                <td>Essentiels</td>
                <td>Email</td>
              </tr>
              <tr>
                <td>Business</td>
                <td>6-25</td>
                <td>Tous</td>
                <td>Email + Chat</td>
              </tr>
              <tr>
                <td>Enterprise</td>
                <td>Illimité</td>
                <td>Tous + API avancée</td>
                <td>Prioritaire 24/7</td>
              </tr>
            </tbody>
          </table>

          <h3>3.2 Tarifs</h3>
          <p>
            Les tarifs en vigueur sont consultables sur notre site. Ils sont exprimés
            en euros hors taxes (HT). La TVA applicable sera ajoutée au moment de la facturation.
          </p>

          <h3>3.3 Révision des prix</h3>
          <p>
            MASITH Développement se réserve le droit de réviser ses tarifs annuellement.
            Le Client sera informé par email 30 jours avant l'application des nouveaux tarifs.
          </p>
        </section>

        <section className="legal-section">
          <h2>4. Souscription et accès</h2>

          <h3>4.1 Inscription</h3>
          <p>
            La souscription s'effectue en ligne via notre site. Le Client doit fournir
            des informations exactes et complètes. Un compte administrateur est créé
            pour gérer l'espace de travail.
          </p>

          <h3>4.2 Période d'essai</h3>
          <p>
            Une période d'essai gratuite de 14 jours est proposée pour la formule
            Business. À l'issue de cette période, le Client peut choisir de souscrire
            un abonnement ou voir son accès désactivé.
          </p>

          <h3>4.3 Identifiants</h3>
          <p>
            Le Client est responsable de la confidentialité de ses identifiants
            de connexion. Toute utilisation des identifiants est réputée faite par le Client.
          </p>
        </section>

        <section className="legal-section">
          <h2>5. Modalités de paiement</h2>

          <h3>5.1 Facturation</h3>
          <p>
            La facturation est mensuelle ou annuelle selon l'option choisie.
            Les factures sont émises et envoyées par email au début de chaque période.
          </p>

          <h3>5.2 Moyens de paiement</h3>
          <ul>
            <li>Carte bancaire (Visa, Mastercard)</li>
            <li>Prélèvement SEPA</li>
            <li>Virement bancaire (Enterprise uniquement)</li>
          </ul>

          <h3>5.3 Retard de paiement</h3>
          <p>
            En cas de retard de paiement, des pénalités de retard seront appliquées
            au taux BCE majoré de 10 points, ainsi qu'une indemnité forfaitaire de 40€
            pour frais de recouvrement. L'accès au service pourra être suspendu après
            15 jours de retard.
          </p>
        </section>

        <section className="legal-section">
          <h2>6. Durée et résiliation</h2>

          <h3>6.1 Durée</h3>
          <p>
            L'abonnement est conclu pour une durée d'un mois ou d'un an selon l'option
            choisie. Il est renouvelé tacitement pour une durée identique sauf résiliation.
          </p>

          <h3>6.2 Résiliation par le Client</h3>
          <p>
            Le Client peut résilier à tout moment depuis son espace de gestion.
            La résiliation prend effet à la fin de la période en cours.
            Aucun remboursement prorata temporis n'est effectué.
          </p>

          <h3>6.3 Résiliation par MASITH Développement</h3>
          <p>
            MASITH Développement peut résilier le contrat en cas de :
          </p>
          <ul>
            <li>Non-paiement après mise en demeure restée infructueuse</li>
            <li>Violation des présentes CGV ou des CGU</li>
            <li>Utilisation frauduleuse ou illégale du service</li>
          </ul>

          <h3>6.4 Portabilité des données</h3>
          <p>
            À la résiliation, le Client dispose de 30 jours pour exporter ses données
            via les outils fournis. Passé ce délai, les données seront supprimées.
          </p>
        </section>

        <section className="legal-section">
          <h2>7. Niveau de service (SLA)</h2>

          <h3>7.1 Disponibilité</h3>
          <p>
            MASITH Développement s'engage sur une disponibilité de 99,5% du service
            sur une base mensuelle, hors maintenance planifiée.
          </p>

          <h3>7.2 Maintenance</h3>
          <p>
            Les maintenances planifiées sont annoncées 48h à l'avance par email
            et sont programmées en dehors des heures de bureau (20h-6h CET).
          </p>

          <h3>7.3 Compensation</h3>
          <p>
            En cas de non-respect du SLA, le Client peut demander un avoir
            proportionnel à l'indisponibilité constatée.
          </p>
        </section>

        <section className="legal-section">
          <h2>8. Propriété intellectuelle</h2>

          <h3>8.1 Licence d'utilisation</h3>
          <p>
            MASITH Développement concède au Client un droit d'utilisation non exclusif,
            non transférable et non cessible de la solution AZALSCORE pour la durée
            de l'abonnement.
          </p>

          <h3>8.2 Données du Client</h3>
          <p>
            Le Client reste propriétaire de toutes les données qu'il saisit dans
            l'application. MASITH Développement ne revendique aucun droit sur ces données.
          </p>

          <h3>8.3 Open Source</h3>
          <p>
            Certains composants d'AZALSCORE sont distribués sous licence open source.
            Les conditions spécifiques sont détaillées dans les fichiers LICENSE
            correspondants.
          </p>
        </section>

        <section className="legal-section">
          <h2>9. Protection des données</h2>
          <p>
            Le traitement des données personnelles est effectué conformément à notre{' '}
            <Link to="/confidentialite">Politique de Confidentialité</Link> et au RGPD.
          </p>
          <p>
            Un contrat de sous-traitance (DPA) est disponible sur demande pour
            les clients Enterprise.
          </p>
        </section>

        <section className="legal-section">
          <h2>10. Responsabilité</h2>

          <h3>10.1 Obligations de moyens</h3>
          <p>
            MASITH Développement est soumis à une obligation de moyens.
            Elle s'engage à mettre en œuvre tous les moyens nécessaires
            pour assurer le bon fonctionnement du service.
          </p>

          <h3>10.2 Limitation de responsabilité</h3>
          <p>
            En aucun cas la responsabilité de MASITH Développement ne pourra excéder
            le montant des sommes effectivement versées par le Client au cours des
            12 derniers mois précédant le fait générateur.
          </p>

          <h3>10.3 Exclusions</h3>
          <p>
            MASITH Développement ne saurait être tenue responsable des dommages
            indirects, pertes de données dues à une manipulation du Client,
            ou interruptions causées par des tiers.
          </p>
        </section>

        <section className="legal-section">
          <h2>11. Force majeure</h2>
          <p>
            MASITH Développement ne pourra être tenue responsable en cas de force
            majeure, incluant notamment : catastrophes naturelles, actes de guerre,
            grèves, pannes de réseaux de télécommunication, décisions gouvernementales.
          </p>
        </section>

        <section className="legal-section">
          <h2>12. Modifications des CGV</h2>
          <p>
            MASITH Développement se réserve le droit de modifier les présentes CGV.
            Le Client sera informé par email 30 jours avant l'entrée en vigueur
            des nouvelles conditions. La poursuite de l'utilisation vaut acceptation.
          </p>
        </section>

        <section className="legal-section">
          <h2>13. Droit applicable et litiges</h2>
          <p>
            Les présentes CGV sont régies par le droit français. En cas de litige,
            les parties s'efforceront de trouver une solution amiable. À défaut,
            le litige sera porté devant les tribunaux compétents de Paris.
          </p>
        </section>

        <section className="legal-section">
          <h2>14. Contact</h2>
          <p>
            Pour toute question relative aux présentes CGV :<br />
            Email : <a href="mailto:commercial@azalscore.com">commercial@azalscore.com</a><br />
            Formulaire : <Link to="/contact">Page Contact</Link>
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

export default CGV;
