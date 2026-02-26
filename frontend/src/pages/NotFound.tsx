/**
 * AZALSCORE - Page 404 Optimisée SEO
 * Récupération de trafic et amélioration UX
 */

import React from 'react';
import { Home, ArrowLeft, Search, FileText, Users, Calculator, Package, HelpCircle } from 'lucide-react';
import { useNavigate, Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  const popularPages = [
    { title: 'Fonctionnalités', href: '/features', icon: FileText, description: 'Découvrez tous nos modules' },
    { title: 'Tarifs', href: '/pricing', icon: Calculator, description: 'Plans et prix transparents' },
    { title: 'CRM', href: '/features/crm', icon: Users, description: 'Gestion relation client' },
    { title: 'Inventaire', href: '/features/inventaire', icon: Package, description: 'Gestion de stock' },
    { title: 'Aide', href: '/docs', icon: HelpCircle, description: 'Documentation et guides' },
  ];

  return (
    <>
      <Helmet>
        <title>Page non trouvée - Azalscore ERP</title>
        <meta name="robots" content="noindex, follow" />
        <meta name="description" content="Cette page n'existe pas. Découvrez Azalscore ERP, le logiciel de gestion français pour PME." />
      </Helmet>

      <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white flex flex-col">
        {/* Header simple */}
        <header className="bg-white border-b border-gray-200 py-4">
          <div className="max-w-7xl mx-auto px-4">
            <Link to="/" className="text-2xl font-bold text-blue-600">AZALSCORE</Link>
          </div>
        </header>

        {/* Contenu principal */}
        <main className="flex-1 flex items-center justify-center px-4 py-16">
          <div className="max-w-2xl w-full text-center">
            {/* Code 404 */}
            <div className="mb-8">
              <span className="text-9xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                404
              </span>
            </div>

            {/* Message */}
            <h1 className="text-3xl font-bold text-gray-900 mb-4">
              Page non trouvée
            </h1>
            <p className="text-lg text-gray-600 mb-8">
              La page que vous recherchez n'existe pas ou a été déplacée.
              Pas de panique, voici quelques suggestions pour vous aider.
            </p>

            {/* Actions principales */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <button
                onClick={() => navigate(-1)}
                className="inline-flex items-center justify-center gap-2 px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <ArrowLeft className="w-5 h-5" />
                Retour
              </button>
              <Link
                to="/"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <Home className="w-5 h-5" />
                Accueil
              </Link>
              <Link
                to="/essai-gratuit"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
              >
                Essai gratuit
              </Link>
            </div>

            {/* Pages populaires */}
            <div className="bg-white rounded-2xl border border-gray-200 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center justify-center gap-2">
                <Search className="w-5 h-5 text-blue-600" />
                Pages populaires
              </h2>
              <div className="grid sm:grid-cols-2 md:grid-cols-3 gap-4">
                {popularPages.map((page) => (
                  <Link
                    key={page.href}
                    to={page.href}
                    className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left group"
                  >
                    <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center flex-shrink-0 group-hover:bg-blue-200 transition-colors">
                      <page.icon className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                        {page.title}
                      </h3>
                      <p className="text-sm text-gray-500">{page.description}</p>
                    </div>
                  </Link>
                ))}
              </div>
            </div>

            {/* Contact support */}
            <p className="mt-8 text-gray-500">
              Besoin d'aide ?{' '}
              <Link to="/contact" className="text-blue-600 hover:underline">
                Contactez notre support
              </Link>
            </p>
          </div>
        </main>

        {/* Footer simple */}
        <footer className="bg-gray-900 text-white py-6">
          <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-400">
            © 2026 AZALSCORE - MASITH Développement. Tous droits réservés.
          </div>
        </footer>
      </div>
    </>
  );
};

export default NotFoundPage;
