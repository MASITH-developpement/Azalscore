/**
 * AZALSCORE - Article Blog : Conformité RGPD et ERP
 * Article SEO sur la protection des données dans un ERP
 */

import React from 'react';
import { Calendar, Clock, ArrowLeft, ArrowRight, Share2, Bookmark, CheckCircle, Shield, Lock, Eye, Trash2, Download } from 'lucide-react';
import { Helmet } from 'react-helmet-async';
import { Link } from 'react-router-dom';

export const ConformiteRgpdErp: React.FC = () => {
  const articleData = {
    title: 'RGPD et ERP : Comment Assurer la Conformité de Vos Données',
    description: 'Les obligations RGPD pour les entreprises utilisant un ERP. Bonnes pratiques, checklist de conformité, et comment Azalscore protège vos données.',
    date: '2026-02-05',
    readTime: '10 min',
    author: 'Équipe Azalscore',
    category: 'Sécurité',
  };

  const articleSchema = {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: articleData.title,
    description: articleData.description,
    datePublished: articleData.date,
    author: { '@type': 'Organization', name: 'Azalscore', url: 'https://azalscore.com' },
    publisher: {
      '@type': 'Organization',
      name: 'Azalscore',
      logo: { '@type': 'ImageObject', url: 'https://azalscore.com/pwa-512x512.png' },
    },
  };

  return (
    <>
      <Helmet>
        <title>{articleData.title} | Blog Azalscore</title>
        <meta name="description" content={articleData.description} />
        <meta name="keywords" content="RGPD, ERP, protection données, conformité, données personnelles, CNIL, DPO, sécurité données" />
        <link rel="canonical" href="https://azalscore.com/blog/conformite-rgpd-erp" />
        <meta property="og:title" content={articleData.title} />
        <meta property="og:description" content={articleData.description} />
        <meta property="og:url" content="https://azalscore.com/blog/conformite-rgpd-erp" />
        <meta property="og:type" content="article" />
        <script type="application/ld+json">{JSON.stringify(articleSchema)}</script>
      </Helmet>

      <article className="blog-article">
        <header className="blog-article-header">
          <div className="blog-container">
            <nav className="blog-breadcrumb" aria-label="Fil d'Ariane">
              <Link to="/">Accueil</Link>
              <span>/</span>
              <Link to="/blog">Blog</Link>
              <span>/</span>
              <span>RGPD et ERP</span>
            </nav>

            <div className="blog-article-meta">
              <span className="blog-article-category">{articleData.category}</span>
              <span className="blog-article-date">
                <Calendar size={14} />
                <time dateTime={articleData.date}>
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

            <h1 className="blog-article-title">{articleData.title}</h1>
            <p className="blog-article-excerpt">{articleData.description}</p>

            <div className="blog-article-actions">
              <button className="blog-action-btn"><Share2 size={18} /> Partager</button>
              <button className="blog-action-btn"><Bookmark size={18} /> Sauvegarder</button>
            </div>
          </div>
        </header>

        <figure className="blog-article-hero">
          <img src="/screenshots/real-security.png" alt="Sécurité des données dans Azalscore" width={1200} height={600} />
          <figcaption>Protection des données et conformité RGPD dans Azalscore ERP</figcaption>
        </figure>

        <div className="blog-article-content">
          <div className="blog-container blog-container--narrow">

            <nav className="blog-toc" aria-label="Sommaire">
              <h2>Sommaire</h2>
              <ol>
                <li><a href="#introduction">Qu'est-ce que le RGPD ?</a></li>
                <li><a href="#obligations">Obligations des entreprises</a></li>
                <li><a href="#erp-rgpd">ERP et données personnelles</a></li>
                <li><a href="#checklist">Checklist de conformité</a></li>
                <li><a href="#azalscore-rgpd">Azalscore et le RGPD</a></li>
                <li><a href="#bonnes-pratiques">Bonnes pratiques</a></li>
              </ol>
            </nav>

            <section id="introduction">
              <h2>Qu'est-ce que le RGPD ?</h2>
              <p>
                Le <strong>RGPD</strong> (Règlement Général sur la Protection des Données) est la réglementation européenne entrée en vigueur le 25 mai 2018. Il encadre le traitement des données personnelles des citoyens européens.
              </p>
              <p>
                <strong>Une donnée personnelle</strong> est toute information se rapportant à une personne physique identifiée ou identifiable : nom, email, téléphone, adresse IP, mais aussi des données plus indirectes comme un numéro client ou un historique d'achats.
              </p>

              <div className="blog-callout blog-callout--warning">
                <Shield size={20} />
                <div>
                  <strong>Le RGPD concerne toutes les entreprises</strong>
                  <p>Que vous soyez une TPE ou une grande entreprise, dès que vous traitez des données personnelles de citoyens européens, vous êtes soumis au RGPD.</p>
                </div>
              </div>
            </section>

            <section id="obligations">
              <h2>Les 6 obligations principales du RGPD</h2>

              <div className="blog-rgpd-principles">
                <div className="blog-rgpd-principle">
                  <div className="blog-rgpd-icon">
                    <CheckCircle size={24} />
                  </div>
                  <h3>1. Licéité et transparence</h3>
                  <p>
                    Vous devez avoir une base légale pour traiter les données (consentement, contrat, obligation légale, intérêt légitime) et informer clairement les personnes concernées.
                  </p>
                </div>

                <div className="blog-rgpd-principle">
                  <div className="blog-rgpd-icon">
                    <Lock size={24} />
                  </div>
                  <h3>2. Limitation des finalités</h3>
                  <p>
                    Les données collectées doivent servir uniquement aux finalités déclarées. Vous ne pouvez pas les réutiliser pour d'autres objectifs sans consentement.
                  </p>
                </div>

                <div className="blog-rgpd-principle">
                  <div className="blog-rgpd-icon">
                    <Eye size={24} />
                  </div>
                  <h3>3. Minimisation</h3>
                  <p>
                    Ne collectez que les données strictement nécessaires. Demander une date de naissance pour une newsletter n'est pas justifié.
                  </p>
                </div>

                <div className="blog-rgpd-principle">
                  <div className="blog-rgpd-icon">
                    <CheckCircle size={24} />
                  </div>
                  <h3>4. Exactitude</h3>
                  <p>
                    Les données doivent être exactes et mises à jour. Vous devez permettre leur rectification.
                  </p>
                </div>

                <div className="blog-rgpd-principle">
                  <div className="blog-rgpd-icon">
                    <Trash2 size={24} />
                  </div>
                  <h3>5. Limitation de conservation</h3>
                  <p>
                    Les données ne doivent pas être conservées indéfiniment. Définissez des durées de rétention adaptées.
                  </p>
                </div>

                <div className="blog-rgpd-principle">
                  <div className="blog-rgpd-icon">
                    <Shield size={24} />
                  </div>
                  <h3>6. Sécurité</h3>
                  <p>
                    Vous devez protéger les données contre les accès non autorisés, les pertes ou les fuites.
                  </p>
                </div>
              </div>
            </section>

            <section id="erp-rgpd">
              <h2>ERP et données personnelles : quels enjeux ?</h2>
              <p>
                Un ERP centralise énormément de données personnelles :
              </p>

              <h3>Données clients (CRM)</h3>
              <ul>
                <li>Noms, prénoms, civilité</li>
                <li>Adresses email et postales</li>
                <li>Numéros de téléphone</li>
                <li>Historique des achats et interactions</li>
                <li>Coordonnées bancaires (IBAN, CB)</li>
              </ul>

              <h3>Données employés (RH)</h3>
              <ul>
                <li>Identité complète</li>
                <li>Numéro de sécurité sociale</li>
                <li>Coordonnées bancaires</li>
                <li>Historique des absences et maladies</li>
                <li>Évaluations professionnelles</li>
              </ul>

              <h3>Données fournisseurs</h3>
              <ul>
                <li>Contacts commerciaux</li>
                <li>Coordonnées bancaires</li>
                <li>Historique des transactions</li>
              </ul>

              <div className="blog-callout blog-callout--info">
                <Eye size={20} />
                <div>
                  <strong>Responsabilité partagée</strong>
                  <p>En tant que responsable de traitement, vous restez responsable de la conformité même si vous utilisez un ERP SaaS. L'éditeur est sous-traitant au sens du RGPD.</p>
                </div>
              </div>
            </section>

            <section id="checklist">
              <h2>Checklist de conformité RGPD pour votre ERP</h2>

              <div className="blog-checklist">
                <h3>📋 Registre des traitements</h3>
                <ul className="blog-check-list">
                  <li><CheckCircle size={16} /> Listez tous les traitements de données personnelles</li>
                  <li><CheckCircle size={16} /> Documentez les finalités de chaque traitement</li>
                  <li><CheckCircle size={16} /> Identifiez les bases légales</li>
                  <li><CheckCircle size={16} /> Définissez les durées de conservation</li>
                </ul>

                <h3>🔐 Sécurité technique</h3>
                <ul className="blog-check-list">
                  <li><CheckCircle size={16} /> Chiffrement des données (AES-256 minimum)</li>
                  <li><CheckCircle size={16} /> Authentification forte (2FA)</li>
                  <li><CheckCircle size={16} /> Gestion des droits d'accès (RBAC)</li>
                  <li><CheckCircle size={16} /> Journalisation des accès (audit trail)</li>
                  <li><CheckCircle size={16} /> Sauvegardes régulières et testées</li>
                </ul>

                <h3>👤 Droits des personnes</h3>
                <ul className="blog-check-list">
                  <li><CheckCircle size={16} /> Procédure de droit d'accès</li>
                  <li><CheckCircle size={16} /> Procédure de rectification</li>
                  <li><CheckCircle size={16} /> Procédure de suppression (droit à l'oubli)</li>
                  <li><CheckCircle size={16} /> Procédure de portabilité</li>
                  <li><CheckCircle size={16} /> Procédure d'opposition</li>
                </ul>

                <h3>📝 Documentation</h3>
                <ul className="blog-check-list">
                  <li><CheckCircle size={16} /> Politique de confidentialité à jour</li>
                  <li><CheckCircle size={16} /> Mentions d'information sur les formulaires</li>
                  <li><CheckCircle size={16} /> Contrat de sous-traitance avec l'éditeur ERP</li>
                  <li><CheckCircle size={16} /> PIA (analyse d'impact) si nécessaire</li>
                </ul>
              </div>
            </section>

            <section id="azalscore-rgpd">
              <h2>Comment Azalscore assure votre conformité RGPD</h2>

              <div className="blog-features-grid">
                <div className="blog-feature">
                  <Shield size={32} className="blog-feature-icon" />
                  <h4>Hébergement en France</h4>
                  <p>Toutes vos données sont hébergées exclusivement en France, sur des serveurs certifiés.</p>
                </div>

                <div className="blog-feature">
                  <Lock size={32} className="blog-feature-icon" />
                  <h4>Chiffrement AES-256</h4>
                  <p>Données chiffrées au repos et en transit avec les standards les plus élevés.</p>
                </div>

                <div className="blog-feature">
                  <Eye size={32} className="blog-feature-icon" />
                  <h4>Audit trail complet</h4>
                  <p>Traçabilité de toutes les actions sur les données personnelles.</p>
                </div>

                <div className="blog-feature">
                  <Download size={32} className="blog-feature-icon" />
                  <h4>Export des données</h4>
                  <p>Export facilité pour répondre aux demandes de portabilité.</p>
                </div>

                <div className="blog-feature">
                  <Trash2 size={32} className="blog-feature-icon" />
                  <h4>Suppression sécurisée</h4>
                  <p>Procédures de suppression et d'anonymisation des données.</p>
                </div>

                <div className="blog-feature">
                  <CheckCircle size={32} className="blog-feature-icon" />
                  <h4>DPA inclus</h4>
                  <p>Contrat de sous-traitance RGPD (DPA) fourni à tous nos clients.</p>
                </div>
              </div>

              <div className="blog-cta-box">
                <h3>Besoin d'un ERP conforme RGPD ?</h3>
                <p>Azalscore a été conçu avec la conformité RGPD en son cœur. Testez-le gratuitement.</p>
                <Link to="/essai-gratuit" className="blog-btn blog-btn-primary blog-btn-lg">
                  Essai gratuit 30 jours
                  <ArrowRight size={20} />
                </Link>
              </div>
            </section>

            <section id="bonnes-pratiques">
              <h2>Bonnes pratiques RGPD au quotidien</h2>

              <h3>Pour vos équipes</h3>
              <ul>
                <li><strong>Formez vos collaborateurs</strong> aux enjeux de la protection des données</li>
                <li><strong>Limitez les accès</strong> au strict nécessaire (principe du moindre privilège)</li>
                <li><strong>Ne partagez jamais</strong> les identifiants et mots de passe</li>
                <li><strong>Signalez immédiatement</strong> toute anomalie ou incident</li>
              </ul>

              <h3>Pour vos processus</h3>
              <ul>
                <li><strong>Purgez régulièrement</strong> les données obsolètes</li>
                <li><strong>Documentez</strong> vos traitements et leurs évolutions</li>
                <li><strong>Testez</strong> vos procédures de réponse aux demandes</li>
                <li><strong>Auditez</strong> périodiquement votre conformité</li>
              </ul>

              <h3>En cas de violation de données</h3>
              <ol>
                <li>Identifiez et contenez l'incident</li>
                <li>Évaluez la gravité et les risques</li>
                <li>Notifiez la CNIL sous 72h si nécessaire</li>
                <li>Informez les personnes concernées si risque élevé</li>
                <li>Documentez l'incident et les mesures prises</li>
              </ol>
            </section>

            <section className="blog-conclusion">
              <h2>Conclusion</h2>
              <p>
                La conformité RGPD n'est pas une option mais une obligation légale avec des sanctions pouvant atteindre 4% du chiffre d'affaires mondial. Avec un ERP comme Azalscore, conçu pour la conformité, vous disposez des outils nécessaires pour protéger les données de vos clients et employés.
              </p>
              <p>
                N'attendez pas un contrôle de la CNIL pour vous mettre en conformité. Commencez dès aujourd'hui avec une solution qui intègre la protection des données par conception.
              </p>
            </section>

          </div>
        </div>

        <nav className="blog-article-nav">
          <div className="blog-container">
            <Link to="/blog/erp-pme-guide-complet" className="blog-nav-link blog-nav-link--prev">
              <ArrowLeft size={20} />
              ERP pour PME : Guide complet
            </Link>
            <Link to="/blog" className="blog-nav-link blog-nav-link--next">
              Retour au blog
              <ArrowRight size={20} />
            </Link>
          </div>
        </nav>
      </article>
    </>
  );
};

export default ConformiteRgpdErp;
