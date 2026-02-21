/**
 * AZALSCORE - Article Blog : Facturation Électronique 2026
 * Article SEO complet sur les obligations de facturation électronique
 */

import React from 'react';
import { Calendar, Clock, ArrowLeft, ArrowRight, Share2, Bookmark, CheckCircle, AlertTriangle, Info } from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';

// Composant pour les callouts
const Callout: React.FC<{ type: 'info' | 'warning' | 'success'; title: string; children: React.ReactNode }> = ({
  type,
  title,
  children,
}) => {
  const icons = {
    info: <Info size={20} />,
    warning: <AlertTriangle size={20} />,
    success: <CheckCircle size={20} />,
  };

  return (
    <div className={`blog-callout blog-callout--${type}`}>
      <div className="blog-callout-icon">{icons[type]}</div>
      <div className="blog-callout-content">
        <strong>{title}</strong>
        <div>{children}</div>
      </div>
    </div>
  );
};

export const FacturationElectronique2026: React.FC = () => {
  const articleData = {
    title: 'Facturation Électronique 2026 : Guide Complet pour les PME',
    description: 'Tout ce que vous devez savoir sur les obligations de facturation électronique en France. Calendrier, formats Factur-X, PPF/PDP, et comment vous préparer.',
    date: '2026-02-15',
    readTime: '12 min',
    author: 'Équipe Azalscore',
    category: 'Conformité',
  };

  // Schema.org Article
  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: articleData.title,
    description: articleData.description,
    datePublished: articleData.date,
    dateModified: articleData.date,
    author: {
      '@type': 'Organization',
      name: 'Azalscore',
      url: 'https://azalscore.com',
    },
    publisher: {
      '@type': 'Organization',
      name: 'Azalscore',
      logo: {
        '@type': 'ImageObject',
        url: 'https://azalscore.com/pwa-512x512.png',
      },
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': 'https://azalscore.com/blog/facturation-electronique-2026',
    },
  };

  return (
    <>
      <Helmet>
        <title>{articleData.title} | Blog Azalscore</title>
        <meta name="description" content={articleData.description} />
        <meta name="keywords" content="facturation électronique 2026, Factur-X, PPF, PDP, obligation facturation, PME, France, e-invoicing" />
        <link rel="canonical" href="https://azalscore.com/blog/facturation-electronique-2026" />

        {/* Open Graph */}
        <meta property="og:title" content={articleData.title} />
        <meta property="og:description" content={articleData.description} />
        <meta property="og:url" content="https://azalscore.com/blog/facturation-electronique-2026" />
        <meta property="og:type" content="article" />
        <meta property="og:image" content="https://azalscore.com/screenshots/real-facturation.png" />
        <meta property="article:published_time" content={articleData.date} />
        <meta property="article:author" content="Azalscore" />
        <meta property="article:section" content={articleData.category} />

        {/* Twitter */}
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content={articleData.title} />
        <meta name="twitter:description" content={articleData.description} />

        {/* Schema.org */}
        <script type="application/ld+json">{JSON.stringify(articleSchema)}</script>
      </Helmet>

      <article className="blog-article" itemScope itemType="https://schema.org/Article">
        {/* Header */}
        <header className="blog-article-header">
          <div className="blog-container">
            <nav className="blog-breadcrumb" aria-label="Fil d'Ariane">
              <Link to="/">Accueil</Link>
              <span>/</span>
              <Link to="/blog">Blog</Link>
              <span>/</span>
              <span>Facturation Électronique 2026</span>
            </nav>

            <div className="blog-article-meta">
              <span className="blog-article-category">{articleData.category}</span>
              <span className="blog-article-date">
                <Calendar size={14} />
                <time dateTime={articleData.date} itemProp="datePublished">
                  {new Date(articleData.date).toLocaleDateString('fr-FR', {
                    day: 'numeric',
                    month: 'long',
                    year: 'numeric',
                  })}
                </time>
              </span>
              <span className="blog-article-read-time">
                <Clock size={14} />
                {articleData.readTime} de lecture
              </span>
            </div>

            <h1 className="blog-article-title" itemProp="headline">
              {articleData.title}
            </h1>

            <p className="blog-article-excerpt" itemProp="description">
              {articleData.description}
            </p>

            <div className="blog-article-actions">
              <button className="blog-action-btn" aria-label="Partager">
                <Share2 size={18} />
                Partager
              </button>
              <button className="blog-action-btn" aria-label="Sauvegarder">
                <Bookmark size={18} />
                Sauvegarder
              </button>
            </div>
          </div>
        </header>

        {/* Image principale */}
        <figure className="blog-article-hero">
          <img
            src="/screenshots/real-facturation.png"
            alt="Interface de facturation électronique Azalscore"
            width={1200}
            height={600}
            itemProp="image"
          />
          <figcaption>Interface de facturation électronique Azalscore - Conforme 2026</figcaption>
        </figure>

        {/* Contenu */}
        <div className="blog-article-content" itemProp="articleBody">
          <div className="blog-container blog-container--narrow">

            {/* Table des matières */}
            <nav className="blog-toc" aria-label="Sommaire">
              <h2>Sommaire</h2>
              <ol>
                <li><a href="#introduction">Introduction</a></li>
                <li><a href="#calendrier">Calendrier des obligations</a></li>
                <li><a href="#formats">Formats de factures acceptés</a></li>
                <li><a href="#ppf-pdp">PPF et PDP : Quelle différence ?</a></li>
                <li><a href="#preparation">Comment se préparer</a></li>
                <li><a href="#azalscore">Solution Azalscore</a></li>
                <li><a href="#faq">Questions fréquentes</a></li>
              </ol>
            </nav>

            {/* Introduction */}
            <section id="introduction">
              <h2>Introduction : Qu'est-ce que la facturation électronique ?</h2>
              <p>
                La <strong>facturation électronique</strong> (ou e-invoicing) est l'émission, la transmission et la réception de factures sous format numérique structuré. Contrairement à une facture PDF simple, une facture électronique contient des données exploitables automatiquement par les systèmes informatiques.
              </p>
              <p>
                En France, la <strong>réforme de la facturation électronique 2026</strong> impose à toutes les entreprises assujetties à la TVA d'émettre et de recevoir des factures au format électronique pour leurs transactions B2B (business-to-business).
              </p>

              <Callout type="info" title="Objectifs de la réforme">
                <ul>
                  <li>Lutter contre la fraude à la TVA (estimée à 15 milliards € par an)</li>
                  <li>Simplifier les déclarations fiscales grâce au pré-remplissage</li>
                  <li>Moderniser les échanges entre entreprises</li>
                  <li>Améliorer la compétitivité des entreprises françaises</li>
                </ul>
              </Callout>
            </section>

            {/* Calendrier */}
            <section id="calendrier">
              <h2>Calendrier des obligations 2026-2027</h2>
              <p>
                La mise en place de la facturation électronique obligatoire se fait progressivement selon la taille de l'entreprise :
              </p>

              <div className="blog-table-wrapper">
                <table className="blog-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Obligation de réception</th>
                      <th>Obligation d'émission</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td><strong>1er septembre 2026</strong></td>
                      <td>Toutes les entreprises</td>
                      <td>Grandes entreprises et ETI</td>
                    </tr>
                    <tr>
                      <td><strong>1er septembre 2027</strong></td>
                      <td>Toutes les entreprises</td>
                      <td>PME et micro-entreprises</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              <Callout type="warning" title="Attention">
                Même si vous êtes une PME, vous devez être prêt à <strong>recevoir</strong> des factures électroniques dès septembre 2026. Anticipez !
              </Callout>
            </section>

            {/* Formats */}
            <section id="formats">
              <h2>Formats de factures acceptés</h2>
              <p>
                La réglementation française accepte trois formats principaux de factures électroniques :
              </p>

              <h3>1. Factur-X (recommandé)</h3>
              <p>
                <strong>Factur-X</strong> est le format hybride franco-allemand qui combine un fichier PDF lisible par l'humain et des données XML structurées. C'est le format le plus flexible et le plus adopté en France.
              </p>
              <ul>
                <li>✅ Lisible par tous (PDF visuel)</li>
                <li>✅ Données structurées pour l'automatisation</li>
                <li>✅ 5 profils : Minimum, Basic WL, Basic, EN16931, Extended</li>
                <li>✅ Compatible avec les normes européennes</li>
              </ul>

              <h3>2. UBL (Universal Business Language)</h3>
              <p>
                Format XML standard utilisé dans de nombreux pays européens. Plus technique, il est adapté aux grandes entreprises avec des systèmes d'information avancés.
              </p>

              <h3>3. CII (Cross Industry Invoice)</h3>
              <p>
                Format XML basé sur la norme UN/CEFACT. Utilisé principalement dans l'industrie et le commerce international.
              </p>

              <Callout type="success" title="Recommandation Azalscore">
                Nous recommandons le format <strong>Factur-X profil EN16931</strong> pour la plupart des PME. C'est le meilleur compromis entre conformité, lisibilité et interopérabilité.
              </Callout>
            </section>

            {/* PPF et PDP */}
            <section id="ppf-pdp">
              <h2>PPF et PDP : Quelle différence ?</h2>

              <h3>Le Portail Public de Facturation (PPF)</h3>
              <p>
                Le <strong>PPF</strong> est la plateforme publique gratuite mise à disposition par l'État. Elle permet :
              </p>
              <ul>
                <li>L'émission et la réception de factures électroniques</li>
                <li>La transmission des données à l'administration fiscale</li>
                <li>L'annuaire des entreprises et de leurs modes de réception</li>
              </ul>

              <h3>Les Plateformes de Dématérialisation Partenaires (PDP)</h3>
              <p>
                Les <strong>PDP</strong> sont des plateformes privées agréées par l'État qui offrent des services supplémentaires :
              </p>
              <ul>
                <li>Intégration avec votre ERP/logiciel de gestion</li>
                <li>Conversion automatique de formats</li>
                <li>Archivage légal à valeur probante</li>
                <li>Support client dédié</li>
                <li>Fonctionnalités avancées (workflow, relances, etc.)</li>
              </ul>

              <div className="blog-table-wrapper">
                <table className="blog-table">
                  <thead>
                    <tr>
                      <th>Critère</th>
                      <th>PPF</th>
                      <th>PDP</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr>
                      <td>Coût</td>
                      <td>Gratuit</td>
                      <td>Payant (abonnement)</td>
                    </tr>
                    <tr>
                      <td>Intégration ERP</td>
                      <td>Limitée</td>
                      <td>Avancée</td>
                    </tr>
                    <tr>
                      <td>Support</td>
                      <td>Standard</td>
                      <td>Premium</td>
                    </tr>
                    <tr>
                      <td>Fonctionnalités</td>
                      <td>Basiques</td>
                      <td>Étendues</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </section>

            {/* Préparation */}
            <section id="preparation">
              <h2>Comment se préparer à la facturation électronique</h2>

              <h3>Étape 1 : Audit de vos processus actuels</h3>
              <p>
                Commencez par analyser votre processus de facturation actuel :
              </p>
              <ul>
                <li>Combien de factures émettez-vous par mois ?</li>
                <li>Quels logiciels utilisez-vous actuellement ?</li>
                <li>Comment archivez-vous vos factures ?</li>
                <li>Vos données clients sont-elles à jour (SIRET, adresse) ?</li>
              </ul>

              <h3>Étape 2 : Mise à jour de vos données</h3>
              <p>
                Assurez-vous que toutes vos fiches clients contiennent :
              </p>
              <ul>
                <li>Le numéro SIRET valide</li>
                <li>L'adresse complète</li>
                <li>Le numéro de TVA intracommunautaire (si applicable)</li>
                <li>Les coordonnées de contact</li>
              </ul>

              <h3>Étape 3 : Choix de votre solution</h3>
              <p>
                Optez pour un ERP ou un logiciel de facturation compatible avec la réforme 2026. Vérifiez :
              </p>
              <ul>
                <li>La génération de factures Factur-X</li>
                <li>L'intégration avec PPF ou une PDP agréée</li>
                <li>L'archivage légal à valeur probante</li>
                <li>La possibilité d'export FEC pour la comptabilité</li>
              </ul>

              <h3>Étape 4 : Formation de vos équipes</h3>
              <p>
                Formez vos collaborateurs aux nouveaux processus :
              </p>
              <ul>
                <li>Création de factures conformes</li>
                <li>Gestion des statuts de factures (envoyée, reçue, rejetée)</li>
                <li>Traitement des anomalies</li>
              </ul>
            </section>

            {/* Solution Azalscore */}
            <section id="azalscore">
              <h2>Azalscore : Votre solution pour la facturation électronique 2026</h2>
              <p>
                <strong>Azalscore ERP</strong> est nativement conçu pour la facturation électronique. Notre module de facturation inclut :
              </p>

              <div className="blog-features-grid">
                <div className="blog-feature">
                  <CheckCircle size={24} className="blog-feature-icon" />
                  <h4>Factur-X natif</h4>
                  <p>Génération automatique de factures au format Factur-X EN16931, conformes aux exigences 2026.</p>
                </div>
                <div className="blog-feature">
                  <CheckCircle size={24} className="blog-feature-icon" />
                  <h4>Intégration PDP</h4>
                  <p>Connexion avec les principales plateformes de dématérialisation partenaires agréées.</p>
                </div>
                <div className="blog-feature">
                  <CheckCircle size={24} className="blog-feature-icon" />
                  <h4>Archivage légal</h4>
                  <p>Conservation à valeur probante pendant 10 ans, conforme aux exigences fiscales.</p>
                </div>
                <div className="blog-feature">
                  <CheckCircle size={24} className="blog-feature-icon" />
                  <h4>Export FEC</h4>
                  <p>Génération automatique du Fichier des Écritures Comptables pour l'administration fiscale.</p>
                </div>
              </div>

              <div className="blog-cta-box">
                <h3>Prêt pour 2026 ?</h3>
                <p>Testez Azalscore gratuitement pendant 30 jours et découvrez notre module de facturation électronique.</p>
                <Link to="/essai-gratuit" className="blog-btn blog-btn-primary blog-btn-lg">
                  Essai gratuit 30 jours
                  <ArrowRight size={20} />
                </Link>
              </div>
            </section>

            {/* FAQ */}
            <section id="faq">
              <h2>Questions fréquentes</h2>

              <div className="blog-faq">
                <details className="blog-faq-item">
                  <summary>La facturation électronique est-elle obligatoire pour toutes les entreprises ?</summary>
                  <p>
                    Oui, toutes les entreprises assujetties à la TVA en France sont concernées. Cela inclut les micro-entreprises, PME, ETI et grandes entreprises. Seules les entreprises non assujetties (associations, certaines professions libérales) sont exemptées.
                  </p>
                </details>

                <details className="blog-faq-item">
                  <summary>Que se passe-t-il si je ne suis pas conforme ?</summary>
                  <p>
                    Le non-respect des obligations de facturation électronique expose à des amendes pouvant atteindre 15 € par facture (plafonné à 45 000 € par an pour les personnes physiques). De plus, vos clients risquent de rejeter vos factures non conformes.
                  </p>
                </details>

                <details className="blog-faq-item">
                  <summary>Puis-je continuer à envoyer des factures PDF ?</summary>
                  <p>
                    Les factures PDF simples ne seront plus acceptées pour les transactions B2B après 2026. Vous devez utiliser un format structuré (Factur-X, UBL, CII). Le format Factur-X permet toutefois de conserver un visuel PDF en plus des données structurées.
                  </p>
                </details>

                <details className="blog-faq-item">
                  <summary>Comment mes clients vont-ils recevoir mes factures ?</summary>
                  <p>
                    Vos factures seront transmises via le PPF ou une PDP. Vos clients les recevront sur la plateforme de leur choix (PPF ou leur PDP). L'annuaire centralisé permettra de connaître le mode de réception de chaque entreprise.
                  </p>
                </details>

                <details className="blog-faq-item">
                  <summary>Azalscore est-il compatible avec la facturation électronique 2026 ?</summary>
                  <p>
                    Oui, Azalscore est entièrement compatible avec les exigences de la réforme. Notre module de facturation génère des factures Factur-X, s'intègre avec les PDP agréées, et permet l'export FEC pour la comptabilité. Nous accompagnons nos clients dans leur mise en conformité.
                  </p>
                </details>
              </div>
            </section>

            {/* Conclusion */}
            <section className="blog-conclusion">
              <h2>Conclusion</h2>
              <p>
                La facturation électronique 2026 représente un changement majeur pour les entreprises françaises. En vous préparant dès maintenant avec une solution adaptée comme Azalscore, vous transformez cette obligation en opportunité : gain de temps, réduction des erreurs, et amélioration de votre trésorerie grâce à des paiements plus rapides.
              </p>
              <p>
                N'attendez pas le dernier moment. Commencez votre transition dès aujourd'hui avec un essai gratuit de 30 jours.
              </p>
            </section>

          </div>
        </div>

        {/* Navigation articles */}
        <nav className="blog-article-nav">
          <div className="blog-container">
            <Link to="/blog" className="blog-nav-link blog-nav-link--prev">
              <ArrowLeft size={20} />
              Retour au blog
            </Link>
            <Link to="/blog/erp-pme-guide-complet" className="blog-nav-link blog-nav-link--next">
              Article suivant : ERP pour PME
              <ArrowRight size={20} />
            </Link>
          </div>
        </nav>
      </article>
    </>
  );
};

export default FacturationElectronique2026;
