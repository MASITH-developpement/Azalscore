/**
 * AZALSCORE - Page Secteur Industrie
 * Landing page optimisée SEO pour le secteur industriel
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Factory, Package, Truck, ClipboardCheck, Settings, BarChart3, ArrowRight, Check } from 'lucide-react';

const features = [
  {
    icon: Factory,
    title: 'Gestion de production',
    description: 'Ordres de fabrication, nomenclatures, suivi des opérations, planification capacité.'
  },
  {
    icon: Package,
    title: 'Stock multi-dépôts',
    description: 'Gestion des matières premières, produits finis, emplacements, lots et séries.'
  },
  {
    icon: ClipboardCheck,
    title: 'Contrôle qualité',
    description: 'Points de contrôle, non-conformités, traçabilité complète, certifications.'
  },
  {
    icon: Truck,
    title: 'Approvisionnement',
    description: 'Gestion fournisseurs, commandes automatiques, réceptions, calcul des besoins.'
  },
  {
    icon: Settings,
    title: 'Maintenance GMAO',
    description: 'Maintenance préventive, gestion du parc machines, historique interventions.'
  },
  {
    icon: BarChart3,
    title: 'Tableaux de bord',
    description: 'KPIs production, taux de rendement, coûts de revient, analyses temps réel.'
  }
];

const industries = [
  'Métallurgie et mécanique',
  'Agroalimentaire',
  'Plasturgie',
  'Électronique',
  'Textile et confection',
  'Menuiserie et ameublement'
];

const Industrie: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>ERP Industrie et Production | Azalscore - Gestion industrielle PME</title>
        <meta name="description" content="Solution ERP pour PME industrielles : gestion de production, stocks, qualité, maintenance GMAO. Logiciel adapté à l'industrie française." />
        <meta name="keywords" content="erp industrie, logiciel production, gpao pme, gestion industrielle, erp fabrication, gmao" />
        <link rel="canonical" href="https://azalscore.com/secteurs/industrie" />
        <meta property="og:title" content="ERP Industrie et Production | Azalscore" />
        <meta property="og:description" content="Solution complète pour gérer votre production industrielle." />
        <meta property="og:url" content="https://azalscore.com/secteurs/industrie" />
        <meta property="og:type" content="website" />
        <meta property="og:image" content="https://azalscore.com/screenshots/real-production.png" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://azalscore.com" },
              { "@type": "ListItem", "position": 2, "name": "Secteurs", "item": "https://azalscore.com/secteurs" },
              { "@type": "ListItem", "position": 3, "name": "Industrie", "item": "https://azalscore.com/secteurs/industrie" }
            ]
          })}
        </script>
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Azalscore ERP Industrie",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web",
            "description": "Solution ERP pour PME industrielles : gestion de production, stocks, qualité, maintenance GMAO.",
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
              "ratingValue": "4.7",
              "ratingCount": "64",
              "bestRating": "5"
            }
          })}
        </script>
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <Link to="/" className="text-2xl font-bold text-blue-600">AZALSCORE</Link>
            <nav className="hidden md:flex gap-6">
              <Link to="/features" className="text-gray-600 hover:text-gray-900">Fonctionnalités</Link>
              <Link to="/pricing" className="text-gray-600 hover:text-gray-900">Tarifs</Link>
              <Link to="/blog" className="text-gray-600 hover:text-gray-900">Blog</Link>
            </nav>
            <Link to="/essai-gratuit" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              Essai gratuit
            </Link>
          </div>
        </header>

        {/* Hero */}
        <section className="bg-gradient-to-b from-slate-100 to-white py-20">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <span className="inline-block bg-slate-200 text-slate-700 px-3 py-1 rounded-full text-sm font-medium mb-4">
                  Secteur Industrie
                </span>
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                  L'ERP adapté à l'industrie française
                </h1>
                <p className="text-xl text-gray-600 mb-8">
                  Pilotez votre production, gérez vos stocks et optimisez votre supply chain. Solution complète pour PME industrielles.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-slate-800 text-white px-6 py-3 rounded-lg font-semibold hover:bg-slate-900">
                    Essai gratuit 30 jours <ArrowRight className="ml-2 w-5 h-5" />
                  </Link>
                  <Link to="/demo" className="inline-flex items-center justify-center border border-gray-300 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50">
                    Demander une démo
                  </Link>
                </div>
              </div>
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <picture>
                  <source srcSet="/screenshots/real-production.webp" type="image/webp" />
                  <img
                    src="/screenshots/real-production.png"
                    alt="Interface gestion de production Azalscore"
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
            <h2 className="text-3xl font-bold text-center mb-4">Fonctionnalités pour l'industrie</h2>
            <p className="text-gray-600 text-center mb-12 max-w-2xl mx-auto">
              Outils spécialisés pour piloter votre activité industrielle
            </p>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div key={index} className="p-6 bg-gray-50 rounded-xl hover:shadow-md transition-shadow">
                  <feature.icon className="w-10 h-10 text-slate-700 mb-4" />
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Industries */}
        <section className="py-20 bg-slate-100">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Secteurs industriels couverts</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {industries.map((industry, index) => (
                <div key={index} className="flex items-center gap-3 bg-white p-4 rounded-lg shadow-sm">
                  <Check className="w-6 h-6 text-slate-700 flex-shrink-0" />
                  <span className="text-gray-700">{industry}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Compliance */}
        <section className="py-20 bg-white">
          <div className="max-w-4xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold mb-8">Conformité et traçabilité</h2>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="p-6 bg-blue-50 rounded-xl">
                <h3 className="font-semibold text-lg mb-2">Traçabilité lots</h3>
                <p className="text-gray-600 text-sm">Suivi complet des lots et numéros de série</p>
              </div>
              <div className="p-6 bg-green-50 rounded-xl">
                <h3 className="font-semibold text-lg mb-2">Export FEC</h3>
                <p className="text-gray-600 text-sm">Comptabilité conforme aux exigences fiscales</p>
              </div>
              <div className="p-6 bg-purple-50 rounded-xl">
                <h3 className="font-semibold text-lg mb-2">Factur-X 2026</h3>
                <p className="text-gray-600 text-sm">Facturation électronique obligatoire</p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-slate-800">
          <div className="max-w-4xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Modernisez votre gestion industrielle
            </h2>
            <p className="text-slate-300 text-lg mb-8">
              Essai gratuit 30 jours. Formation et accompagnement inclus.
            </p>
            <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-white text-slate-800 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-slate-100">
              Démarrer l'essai gratuit <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-12">
          <div className="max-w-6xl mx-auto px-4 text-center">
            <p className="text-gray-400 text-sm">
              © 2026 AZALSCORE - MASITH Développement. Tous droits réservés.
            </p>
          </div>
        </footer>
      </div>
    </>
  );
};

export default Industrie;
