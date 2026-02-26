/**
 * AZALSCORE - Page Index des Comparatifs
 * Liste tous les comparatifs disponibles
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { ArrowRight, BarChart3 } from 'lucide-react';
import { Footer } from '../../components/Footer';
import { AzalscoreLogo } from '../../components/Logo';

interface Comparatif {
  slug: string;
  name: string;
  description: string;
  color: string;
}

const comparatifs: Comparatif[] = [
  {
    slug: 'pennylane',
    name: 'Azalscore vs Pennylane',
    description: 'ERP complet vs logiciel comptable. Quel outil choisir pour votre PME ?',
    color: 'bg-purple-600',
  },
  {
    slug: 'odoo',
    name: 'Azalscore vs Odoo',
    description: 'Comparaison avec l\'ERP open source belge. Hébergement, modules, tarifs.',
    color: 'bg-orange-600',
  },
  {
    slug: 'sage',
    name: 'Azalscore vs Sage',
    description: 'Alternative moderne au leader historique. Cloud vs On-Premise.',
    color: 'bg-green-600',
  },
  {
    slug: 'ebp',
    name: 'Azalscore vs EBP',
    description: 'Deux solutions françaises face à face. Laquelle pour votre activité ?',
    color: 'bg-blue-600',
  },
];

const ComparatifIndex: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Comparatifs ERP - Azalscore vs Odoo, Sage, EBP, Pennylane | 2026</title>
        <meta name="description" content="Comparez Azalscore avec les principaux ERP du marché : Odoo, Sage, EBP, Pennylane. Tableaux comparatifs, fonctionnalités, tarifs. Guide de choix ERP pour PME." />
        <meta name="keywords" content="comparatif erp, azalscore vs odoo, azalscore vs sage, azalscore vs pennylane, alternative erp" />
        <link rel="canonical" href="https://azalscore.com/comparatif" />
        <meta property="og:title" content="Comparatifs ERP - Azalscore vs Concurrents" />
        <meta property="og:description" content="Comparez Azalscore avec Odoo, Sage, EBP, Pennylane. Guide de choix ERP." />
        <meta property="og:url" content="https://azalscore.com/comparatif" />
        <meta property="og:type" content="website" />
      </Helmet>

      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <div className="flex items-center gap-6">
              <Link to="/" className="text-gray-500 hover:text-blue-600 text-sm flex items-center gap-1">
                ← Accueil
              </Link>
              <Link to="/" className="flex items-center">
                <AzalscoreLogo size={40} />
              </Link>
            </div>
            <nav className="hidden md:flex gap-6">
              <Link to="/features" className="text-gray-600 hover:text-blue-600">Fonctionnalités</Link>
              <Link to="/pricing" className="text-gray-600 hover:text-blue-600">Tarifs</Link>
              <Link to="/comparatif" className="text-blue-600 font-medium">Comparatifs</Link>
              <Link to="/blog" className="text-gray-600 hover:text-blue-600">Blog</Link>
            </nav>
            <Link to="/essai-gratuit" className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700">
              Essai gratuit
            </Link>
          </div>
        </header>

        {/* Breadcrumb */}
        <nav className="max-w-7xl mx-auto px-4 py-3" aria-label="Breadcrumb">
          <ol className="flex text-sm text-gray-500">
            <li><Link to="/" className="hover:text-blue-600">Accueil</Link></li>
            <li className="mx-2">/</li>
            <li className="text-gray-900">Comparatifs ERP</li>
          </ol>
        </nav>

        {/* Hero */}
        <section className="max-w-7xl mx-auto px-4 py-12">
          <div className="text-center mb-12">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-6">
              <BarChart3 className="w-8 h-8 text-blue-600" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Comparatifs ERP
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Comparez Azalscore avec les principales solutions du marché.
              Tableaux détaillés, fonctionnalités, tarifs et recommandations.
            </p>
          </div>

          {/* Grid of comparisons */}
          <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            {comparatifs.map((comp) => (
              <Link
                key={comp.slug}
                to={`/comparatif/${comp.slug}`}
                className="bg-white rounded-xl shadow-lg p-8 hover:shadow-xl transition group"
              >
                <div className="flex items-center gap-4 mb-4">
                  <div className={`w-12 h-12 ${comp.color} rounded-lg flex items-center justify-center`}>
                    <span className="text-white font-bold text-xl">vs</span>
                  </div>
                  <h2 className="text-xl font-bold text-gray-900 group-hover:text-blue-600 transition">
                    {comp.name}
                  </h2>
                </div>
                <p className="text-gray-600 mb-4">{comp.description}</p>
                <span className="inline-flex items-center text-blue-600 font-medium">
                  Voir le comparatif
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition" />
                </span>
              </Link>
            ))}
          </div>
        </section>

        {/* Why compare */}
        <section className="bg-white py-16">
          <div className="max-w-7xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Pourquoi comparer avant de choisir ?</h2>
            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              <div className="text-center">
                <div className="text-4xl mb-4">1</div>
                <h3 className="font-bold mb-2">Évitez les erreurs coûteuses</h3>
                <p className="text-gray-600">
                  Un mauvais choix d'ERP peut coûter des mois de migration et des milliers d'euros.
                </p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-4">2</div>
                <h3 className="font-bold mb-2">Comprenez vos besoins</h3>
                <p className="text-gray-600">
                  Chaque solution a ses forces. Identifiez celle qui correspond à votre activité.
                </p>
              </div>
              <div className="text-center">
                <div className="text-4xl mb-4">3</div>
                <h3 className="font-bold mb-2">Gagnez du temps</h3>
                <p className="text-gray-600">
                  Nos comparatifs résument des heures de recherche en tableaux clairs.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="max-w-7xl mx-auto px-4 py-16 text-center">
          <h2 className="text-3xl font-bold mb-4">Prêt à tester Azalscore ?</h2>
          <p className="text-xl text-gray-600 mb-8">
            30 jours d'essai gratuit, sans engagement.
          </p>
          <Link
            to="/essai-gratuit"
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition"
          >
            Démarrer l'essai gratuit
            <ArrowRight className="w-5 h-5" />
          </Link>
        </section>

        {/* Footer */}
        <Footer />
      </div>
    </>
  );
};

export default ComparatifIndex;
