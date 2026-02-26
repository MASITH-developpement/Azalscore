/**
 * AZALSCORE - Page Secteur Commerce
 * Landing page optimisée SEO pour le secteur du commerce et retail
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { ShoppingBag, BarChart3, Package, CreditCard, Users, TrendingUp, ArrowRight, Check } from 'lucide-react';
import { Footer } from '../../components/Footer';
import { AzalscoreLogo } from '../../components/Logo';

const features = [
  {
    icon: ShoppingBag,
    title: 'Point de Vente (POS)',
    description: 'Caisse enregistreuse tactile, gestion multi-caisses, tickets de caisse conformes NF525.'
  },
  {
    icon: Package,
    title: 'Gestion des stocks',
    description: 'Stock temps réel, alertes réapprovisionnement, gestion multi-entrepôts et multi-dépôts.'
  },
  {
    icon: CreditCard,
    title: 'Paiements intégrés',
    description: 'Terminal CB, espèces, chèques, tickets restaurant. Clôture de caisse automatisée.'
  },
  {
    icon: Users,
    title: 'Fidélité client',
    description: 'Programme de fidélité, cartes client, historique des achats, statistiques par client.'
  },
  {
    icon: BarChart3,
    title: 'Analyses commerciales',
    description: 'Meilleures ventes, marges par produit, performance par vendeur, tableaux de bord.'
  },
  {
    icon: TrendingUp,
    title: 'E-commerce intégré',
    description: 'Synchronisation boutique en ligne, stock unifié, commandes centralisées.'
  }
];

const testimonials = [
  {
    quote: "Azalscore a simplifié notre gestion quotidienne. La synchronisation entre notre boutique physique et notre site e-commerce est parfaite.",
    author: "Marie L.",
    company: "Boutique de prêt-à-porter, Lyon",
    rating: 5
  }
];

const Commerce: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>ERP Commerce et Retail | Azalscore - Logiciel de gestion boutique</title>
        <meta name="description" content="Solution ERP pour commerces et boutiques : caisse enregistreuse, gestion de stock, fidélité client, e-commerce. Logiciel de gestion adapté au retail français." />
        <meta name="keywords" content="erp commerce, logiciel caisse, gestion boutique, pos retail, erp retail, logiciel magasin" />
        <link rel="canonical" href="https://azalscore.com/secteurs/commerce" />
        <meta property="og:title" content="ERP Commerce et Retail | Azalscore" />
        <meta property="og:description" content="Solution complète pour gérer votre commerce : caisse, stock, fidélité, e-commerce." />
        <meta property="og:url" content="https://azalscore.com/secteurs/commerce" />
        <meta property="og:type" content="website" />
        <meta property="og:image" content="https://azalscore.com/screenshots/real-pos.png" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://azalscore.com" },
              { "@type": "ListItem", "position": 2, "name": "Secteurs", "item": "https://azalscore.com/secteurs" },
              { "@type": "ListItem", "position": 3, "name": "Commerce", "item": "https://azalscore.com/secteurs/commerce" }
            ]
          })}
        </script>
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Azalscore ERP Commerce",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web",
            "description": "Solution ERP pour commerces et boutiques : caisse enregistreuse, gestion de stock, fidélité client, e-commerce.",
            "offers": {
              "@type": "Offer",
              "price": "29",
              "priceCurrency": "EUR",
              "priceSpecification": {
                "@type": "UnitPriceSpecification",
                "price": "29",
                "priceCurrency": "EUR",
                "billingDuration": "P1M"
              }
            },
            "aggregateRating": {
              "@type": "AggregateRating",
              "ratingValue": "4.8",
              "ratingCount": "127",
              "bestRating": "5"
            }
          })}
        </script>
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <div className="flex items-center gap-6">
              <Link to="/" className="text-gray-500 hover:text-blue-600 text-sm flex items-center gap-1">
                ← Accueil
              </Link>
              <Link to="/" className="flex items-center gap-2">
                <AzalscoreLogo size={40} />
              </Link>
            </div>
            <nav className="hidden md:flex gap-6">
              <Link to="/features" className="text-gray-600 hover:text-gray-900">Fonctionnalités</Link>
              <Link to="/pricing" className="text-gray-600 hover:text-gray-900">Tarifs</Link>
              <Link to="/comparatif" className="text-gray-600 hover:text-gray-900">Comparatifs</Link>
              <Link to="/blog" className="text-gray-600 hover:text-gray-900">Blog</Link>
            </nav>
            <Link to="/essai-gratuit" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              Essai gratuit
            </Link>
          </div>
        </header>

        {/* Hero */}
        <section className="bg-gradient-to-b from-orange-50 to-white py-20">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <span className="inline-block bg-orange-100 text-orange-700 px-3 py-1 rounded-full text-sm font-medium mb-4">
                  Secteur Commerce
                </span>
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                  L'ERP conçu pour le commerce et le retail
                </h1>
                <p className="text-xl text-gray-600 mb-8">
                  Gérez votre boutique, votre stock et votre caisse depuis une seule plateforme. Solution complète pour commerces de détail, prêt-à-porter, alimentation, décoration...
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-orange-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-orange-700">
                    Essai gratuit 30 jours <ArrowRight className="ml-2 w-5 h-5" />
                  </Link>
                  <Link to="/demo" className="inline-flex items-center justify-center border border-gray-300 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50">
                    Voir une démo
                  </Link>
                </div>
              </div>
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <picture>
                  <source srcSet="/screenshots/real-pos.webp" type="image/webp" />
                  <img
                    src="/screenshots/real-pos.png"
                    alt="Interface point de vente Azalscore"
                    className="rounded-lg"
                    loading="lazy"
                  />
                </picture>
              </div>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="py-20 bg-white">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-4">Fonctionnalités pour le commerce</h2>
            <p className="text-gray-600 text-center mb-12 max-w-2xl mx-auto">
              Tout ce dont vous avez besoin pour gérer votre activité commerciale au quotidien
            </p>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div key={index} className="p-6 bg-gray-50 rounded-xl hover:shadow-md transition-shadow">
                  <feature.icon className="w-10 h-10 text-orange-600 mb-4" />
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Benefits */}
        <section className="py-20 bg-orange-50">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Pourquoi choisir Azalscore pour votre commerce ?</h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4">
                {[
                  'Caisse conforme NF525 et facturation 2026',
                  'Stock synchronisé boutique + e-commerce',
                  'Gestion multi-magasins centralisée',
                  'Rapports de ventes en temps réel',
                  'Programme de fidélité intégré',
                  'Formation et support inclus'
                ].map((item, index) => (
                  <div key={index} className="flex items-start gap-3">
                    <Check className="w-6 h-6 text-orange-600 flex-shrink-0" />
                    <span className="text-gray-700">{item}</span>
                  </div>
                ))}
              </div>
              <div className="bg-white rounded-xl p-8 shadow-lg">
                {testimonials.map((t, index) => (
                  <div key={index}>
                    <div className="flex gap-1 mb-4">
                      {[...Array(t.rating)].map((_, i) => (
                        <span key={i} className="text-yellow-400">★</span>
                      ))}
                    </div>
                    <blockquote className="text-lg text-gray-700 mb-4">"{t.quote}"</blockquote>
                    <p className="font-semibold">{t.author}</p>
                    <p className="text-sm text-gray-500">{t.company}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-orange-600">
          <div className="max-w-4xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Démarrez votre essai gratuit aujourd'hui
            </h2>
            <p className="text-orange-100 text-lg mb-8">
              30 jours pour tester toutes les fonctionnalités. Sans engagement.
            </p>
            <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-white text-orange-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-orange-50">
              Essayer gratuitement <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        </section>

        {/* Footer */}
        <Footer />
      </div>
    </>
  );
};

export default Commerce;
