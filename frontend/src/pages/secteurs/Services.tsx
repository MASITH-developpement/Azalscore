/**
 * AZALSCORE - Page Secteur Services
 * Landing page optimisée SEO pour le secteur des services
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Wrench, Calendar, Clock, FileText, MapPin, Users, ArrowRight, Check } from 'lucide-react';

const features = [
  {
    icon: Calendar,
    title: 'Planification interventions',
    description: 'Planning techniciens, affectation automatique, vue calendrier multi-ressources.'
  },
  {
    icon: MapPin,
    title: 'Suivi terrain GPS',
    description: 'Géolocalisation des équipes, optimisation des tournées, pointage sur site.'
  },
  {
    icon: FileText,
    title: 'Devis et factures',
    description: 'Création rapide de devis, transformation en facture, signature électronique.'
  },
  {
    icon: Clock,
    title: 'Feuilles de temps',
    description: 'Saisie des heures par projet, validation manager, export paie automatique.'
  },
  {
    icon: Users,
    title: 'Gestion clients',
    description: 'CRM intégré, historique interventions, contrats de maintenance, rappels.'
  },
  {
    icon: Wrench,
    title: 'Gestion du matériel',
    description: 'Suivi parc équipements, maintenance préventive, inventaire outillage.'
  }
];

const useCases = [
  'Entreprises de maintenance (CVC, plomberie, électricité)',
  'Services informatiques et réseaux',
  'Sociétés de nettoyage',
  'Agences de communication',
  'Bureaux d\'études et cabinets conseil',
  'Artisans et TPE du bâtiment'
];

const Services: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>ERP Services et Interventions | Azalscore - Gestion des prestataires</title>
        <meta name="description" content="Solution ERP pour entreprises de services : planification, interventions terrain, devis, facturation. Idéal pour maintenance, informatique, conseil." />
        <meta name="keywords" content="erp services, logiciel interventions, gestion prestataires, planning techniciens, erp maintenance" />
        <link rel="canonical" href="https://azalscore.com/secteurs/services" />
        <meta property="og:title" content="ERP Services et Interventions | Azalscore" />
        <meta property="og:description" content="Solution complète pour gérer vos interventions terrain et vos équipes." />
        <meta property="og:url" content="https://azalscore.com/secteurs/services" />
        <meta property="og:type" content="website" />
        <meta property="og:image" content="https://azalscore.com/screenshots/real-interventions.png" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://azalscore.com" },
              { "@type": "ListItem", "position": 2, "name": "Secteurs", "item": "https://azalscore.com/secteurs" },
              { "@type": "ListItem", "position": 3, "name": "Services", "item": "https://azalscore.com/secteurs/services" }
            ]
          })}
        </script>
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": "Azalscore ERP Services",
            "applicationCategory": "BusinessApplication",
            "operatingSystem": "Web",
            "description": "Solution ERP pour entreprises de services : planification, interventions terrain, devis, facturation.",
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
              "ratingValue": "4.9",
              "ratingCount": "89",
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
        <section className="bg-gradient-to-b from-green-50 to-white py-20">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <span className="inline-block bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-medium mb-4">
                  Secteur Services
                </span>
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                  L'ERP pensé pour les entreprises de services
                </h1>
                <p className="text-xl text-gray-600 mb-8">
                  Planifiez vos interventions, suivez vos équipes terrain et facturez vos clients en temps réel. Solution complète pour prestataires de services.
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700">
                    Essai gratuit 30 jours <ArrowRight className="ml-2 w-5 h-5" />
                  </Link>
                  <Link to="/demo" className="inline-flex items-center justify-center border border-gray-300 px-6 py-3 rounded-lg font-semibold hover:bg-gray-50">
                    Voir une démo
                  </Link>
                </div>
              </div>
              <div className="bg-white rounded-2xl shadow-xl p-8">
                <picture>
                  <source srcSet="/screenshots/real-interventions.webp" type="image/webp" />
                  <img
                    src="/screenshots/real-interventions.png"
                    alt="Interface gestion des interventions Azalscore"
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
            <h2 className="text-3xl font-bold text-center mb-4">Fonctionnalités pour les services</h2>
            <p className="text-gray-600 text-center mb-12 max-w-2xl mx-auto">
              Outils spécialisés pour gérer vos interventions et vos équipes terrain
            </p>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div key={index} className="p-6 bg-gray-50 rounded-xl hover:shadow-md transition-shadow">
                  <feature.icon className="w-10 h-10 text-green-600 mb-4" />
                  <h3 className="text-xl font-semibold mb-2">{feature.title}</h3>
                  <p className="text-gray-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Use Cases */}
        <section className="py-20 bg-green-50">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Idéal pour</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {useCases.map((useCase, index) => (
                <div key={index} className="flex items-center gap-3 bg-white p-4 rounded-lg shadow-sm">
                  <Check className="w-6 h-6 text-green-600 flex-shrink-0" />
                  <span className="text-gray-700">{useCase}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-green-600">
          <div className="max-w-4xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Optimisez la gestion de vos interventions
            </h2>
            <p className="text-green-100 text-lg mb-8">
              Essai gratuit 30 jours. Sans engagement, sans carte bancaire.
            </p>
            <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-white text-green-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-green-50">
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

export default Services;
