/**
 * AZALSCORE - Blog Index Page
 * Liste des articles du blog pour le SEO et le content marketing
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { Calendar, Clock, ArrowRight, Tag, User } from 'lucide-react';
import { Helmet } from 'react-helmet-async';

// Types
interface BlogArticle {
  slug: string;
  title: string;
  excerpt: string;
  date: string;
  readTime: string;
  category: string;
  author: string;
  image: string;
  featured?: boolean;
}

// Articles du blog
const articles: BlogArticle[] = [
  {
    slug: 'facturation-electronique-2026',
    title: 'Facturation Électronique 2026 : Guide Complet pour les PME',
    excerpt: 'Tout ce que vous devez savoir sur les obligations de facturation électronique en France. Calendrier, formats Factur-X, PPF/PDP, et comment vous préparer.',
    date: '2026-02-15',
    readTime: '12 min',
    category: 'Conformité',
    author: 'Équipe Azalscore',
    image: '/screenshots/real-facturation.png',
    featured: true,
  },
  {
    slug: 'erp-pme-guide-complet',
    title: 'ERP pour PME : Le Guide Complet 2026',
    excerpt: 'Comment choisir le bon ERP pour votre PME ? Critères de sélection, fonctionnalités essentielles, et comparatif des solutions du marché français.',
    date: '2026-02-10',
    readTime: '15 min',
    category: 'Guide',
    author: 'Équipe Azalscore',
    image: '/screenshots/mockup-dashboard.png',
    featured: true,
  },
  {
    slug: 'conformite-rgpd-erp',
    title: 'RGPD et ERP : Comment Assurer la Conformité de Vos Données',
    excerpt: 'Les obligations RGPD pour les entreprises utilisant un ERP. Bonnes pratiques, checklist de conformité, et comment Azalscore protège vos données.',
    date: '2026-02-05',
    readTime: '10 min',
    category: 'Sécurité',
    author: 'Équipe Azalscore',
    image: '/screenshots/real-security.png',
  },
  {
    slug: 'gestion-tresorerie-pme',
    title: 'Gestion de Trésorerie : 7 Bonnes Pratiques pour les PME',
    excerpt: 'Optimisez votre trésorerie avec ces conseils pratiques. Prévisions, rapprochement bancaire, et outils pour une gestion financière efficace.',
    date: '2026-01-28',
    readTime: '8 min',
    category: 'Finance',
    author: 'Équipe Azalscore',
    image: '/screenshots/real-treasury.png',
  },
  {
    slug: 'crm-relation-client',
    title: 'CRM : Comment Améliorer Votre Relation Client en 2026',
    excerpt: 'Les meilleures pratiques CRM pour fidéliser vos clients. Pipeline de ventes, segmentation, et automatisation de la relation client.',
    date: '2026-01-20',
    readTime: '9 min',
    category: 'CRM',
    author: 'Équipe Azalscore',
    image: '/screenshots/real-crm.png',
  },
  {
    slug: 'gestion-stock-optimisation',
    title: 'Gestion de Stock : Optimisez Votre Inventaire',
    excerpt: 'Réduisez les ruptures et les surstocks avec une gestion d\'inventaire efficace. Méthodes, KPIs, et outils pour une supply chain optimisée.',
    date: '2026-01-15',
    readTime: '11 min',
    category: 'Logistique',
    author: 'Équipe Azalscore',
    image: '/screenshots/real-inventory.png',
  },
];

// Composant Article Card
const ArticleCard: React.FC<{ article: BlogArticle; featured?: boolean }> = ({ article, featured }) => (
  <article className={`blog-card ${featured ? 'blog-card--featured' : ''}`}>
    <Link to={`/blog/${article.slug}`} className="blog-card-image">
      <img
        src={article.image}
        alt={article.title}
        loading="lazy"
        width={featured ? 800 : 400}
        height={featured ? 400 : 200}
      />
    </Link>
    <div className="blog-card-content">
      <div className="blog-card-meta">
        <span className="blog-card-category">
          <Tag size={14} />
          {article.category}
        </span>
        <span className="blog-card-date">
          <Calendar size={14} />
          {new Date(article.date).toLocaleDateString('fr-FR', {
            day: 'numeric',
            month: 'long',
            year: 'numeric',
          })}
        </span>
        <span className="blog-card-read-time">
          <Clock size={14} />
          {article.readTime}
        </span>
      </div>
      <h2 className="blog-card-title">
        <Link to={`/blog/${article.slug}`}>{article.title}</Link>
      </h2>
      <p className="blog-card-excerpt">{article.excerpt}</p>
      <div className="blog-card-footer">
        <span className="blog-card-author">
          <User size={14} />
          {article.author}
        </span>
        <Link to={`/blog/${article.slug}`} className="blog-card-link">
          Lire l'article
          <ArrowRight size={16} />
        </Link>
      </div>
    </div>
  </article>
);

// Page Blog Index
export const BlogIndex: React.FC = () => {
  const featuredArticles = articles.filter((a) => a.featured);
  const regularArticles = articles.filter((a) => !a.featured);

  return (
    <>
      <Helmet>
        <title>Blog Azalscore - Actualités ERP, Gestion d'Entreprise et Conformité</title>
        <meta
          name="description"
          content="Découvrez nos articles sur la gestion d'entreprise, la facturation électronique 2026, le RGPD, et les meilleures pratiques ERP pour les PME françaises."
        />
        <meta name="keywords" content="blog ERP, facturation électronique 2026, RGPD, gestion PME, CRM, comptabilité, trésorerie" />
        <link rel="canonical" href="https://azalscore.com/blog" />
        <meta property="og:title" content="Blog Azalscore - Actualités ERP et Gestion d'Entreprise" />
        <meta property="og:description" content="Articles et guides sur la gestion d'entreprise, la conformité et les meilleures pratiques ERP." />
        <meta property="og:url" content="https://azalscore.com/blog" />
        <meta property="og:type" content="website" />
      </Helmet>

      <div className="blog-page">
        {/* Header */}
        <header className="blog-header">
          <div className="blog-container">
            <nav className="blog-nav" aria-label="Fil d'Ariane">
              <Link to="/">Accueil</Link>
              <span>/</span>
              <span>Blog</span>
            </nav>
            <h1 className="blog-title">Blog Azalscore</h1>
            <p className="blog-subtitle">
              Actualités, guides et bonnes pratiques pour la gestion de votre entreprise
            </p>
          </div>
        </header>

        {/* Featured Articles */}
        {featuredArticles.length > 0 && (
          <section className="blog-section blog-featured" aria-labelledby="featured-title">
            <div className="blog-container">
              <h2 id="featured-title" className="blog-section-title">Articles à la une</h2>
              <div className="blog-featured-grid">
                {featuredArticles.map((article) => (
                  <ArticleCard key={article.slug} article={article} featured />
                ))}
              </div>
            </div>
          </section>
        )}

        {/* All Articles */}
        <section className="blog-section blog-articles" aria-labelledby="articles-title">
          <div className="blog-container">
            <h2 id="articles-title" className="blog-section-title">Tous les articles</h2>
            <div className="blog-grid">
              {regularArticles.map((article) => (
                <ArticleCard key={article.slug} article={article} />
              ))}
            </div>
          </div>
        </section>

        {/* Newsletter CTA */}
        <section className="blog-section blog-newsletter">
          <div className="blog-container">
            <div className="blog-newsletter-card">
              <h2>Restez informé</h2>
              <p>
                Recevez nos derniers articles et guides directement dans votre boîte mail.
              </p>
              <form className="blog-newsletter-form" onSubmit={(e) => e.preventDefault()}>
                <input
                  type="email"
                  placeholder="Votre email professionnel"
                  required
                  aria-label="Email pour la newsletter"
                />
                <button type="submit" className="blog-btn blog-btn-primary">
                  S'abonner
                </button>
              </form>
            </div>
          </div>
        </section>

        {/* Footer CTA */}
        <section className="blog-section blog-cta">
          <div className="blog-container">
            <h2>Prêt à simplifier votre gestion ?</h2>
            <p>Découvrez Azalscore ERP avec un essai gratuit de 30 jours.</p>
            <Link to="/essai-gratuit" className="blog-btn blog-btn-primary blog-btn-lg">
              Essayer gratuitement
              <ArrowRight size={20} />
            </Link>
          </div>
        </section>
      </div>
    </>
  );
};

export default BlogIndex;
