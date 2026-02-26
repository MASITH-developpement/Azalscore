/**
 * AZALSCORE - Comparatif Azalscore vs Sage
 * Page SEO pour le positionnement sur les recherches comparatives
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Check, X, Minus, ArrowRight, Cloud, Euro, Zap, HeadphonesIcon } from 'lucide-react';

interface ComparisonRow {
  feature: string;
  azalscore: 'yes' | 'no' | 'partial' | string;
  sage: 'yes' | 'no' | 'partial' | string;
  note?: string;
}

const comparisonData: ComparisonRow[] = [
  { feature: 'Solution 100% Cloud', azalscore: 'yes', sage: 'partial', note: 'Sage propose cloud et on-premise' },
  { feature: 'Hébergement France', azalscore: 'yes', sage: 'partial', note: 'Variable selon la solution Sage' },
  { feature: 'Facturation électronique 2026', azalscore: 'yes', sage: 'yes' },
  { feature: 'Format Factur-X natif', azalscore: 'yes', sage: 'yes' },
  { feature: 'Export FEC automatique', azalscore: 'yes', sage: 'yes' },
  { feature: 'CRM intégré', azalscore: 'yes', sage: 'partial', note: 'Selon la gamme Sage choisie' },
  { feature: 'Gestion de stock', azalscore: 'yes', sage: 'yes' },
  { feature: 'Ressources Humaines', azalscore: 'yes', sage: 'yes', note: 'Sage HR séparé' },
  { feature: 'Point de Vente (POS)', azalscore: 'yes', sage: 'partial', note: 'Via partenaires' },
  { feature: 'Gestion des interventions', azalscore: 'yes', sage: 'no' },
  { feature: 'Interface moderne', azalscore: 'yes', sage: 'partial', note: 'Nouvelles versions uniquement' },
  { feature: 'Tarif transparent', azalscore: 'yes', sage: 'no', note: 'Devis personnalisé Sage' },
  { feature: 'API REST complète', azalscore: 'yes', sage: 'yes' },
  { feature: 'Multi-sociétés', azalscore: 'yes', sage: 'yes' },
  { feature: 'Historique 40+ ans', azalscore: 'no', sage: 'yes', note: 'Sage fondé en 1981' },
  { feature: 'Réseau partenaires', azalscore: 'no', sage: 'yes', note: '2000+ partenaires Sage France' },
  { feature: 'Essai gratuit', azalscore: '30 jours', sage: 'no', note: 'Démo sur demande' },
  { feature: 'Conformité RGPD', azalscore: 'yes', sage: 'yes' },
];

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  if (status === 'yes') return <Check className="w-5 h-5 text-green-600" />;
  if (status === 'no') return <X className="w-5 h-5 text-red-500" />;
  if (status === 'partial') return <Minus className="w-5 h-5 text-yellow-500" />;
  return <span className="text-sm text-gray-700">{status}</span>;
};

const VsSage: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Azalscore vs Sage : Comparatif ERP 2026 | Alternative moderne à Sage</title>
        <meta name="description" content="Comparaison entre Azalscore et Sage. ERP cloud moderne vs solution historique. Découvrez les différences et choisissez la meilleure solution pour votre PME." />
        <meta name="keywords" content="azalscore vs sage, comparatif erp, alternative sage, erp français, sage 100, sage x3" />
        <link rel="canonical" href="https://azalscore.com/comparatif/sage" />
        <meta property="og:title" content="Azalscore vs Sage : Comparatif ERP 2026" />
        <meta property="og:description" content="Alternative moderne à Sage pour les PME françaises." />
        <meta property="og:url" content="https://azalscore.com/comparatif/sage" />
        <meta property="og:image" content="https://azalscore.com/screenshots/comparatif-sage.png" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://azalscore.com" },
              { "@type": "ListItem", "position": 2, "name": "Comparatifs", "item": "https://azalscore.com/comparatif" },
              { "@type": "ListItem", "position": 3, "name": "Azalscore vs Sage", "item": "https://azalscore.com/comparatif/sage" }
            ]
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
        <section className="bg-gradient-to-b from-blue-50 to-white py-16">
          <div className="max-w-4xl mx-auto px-4 text-center">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
              Azalscore vs Sage : Comparatif ERP
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Solution cloud moderne contre éditeur historique : quelle solution correspond le mieux à votre PME française ?
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-blue-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-700">
                Essayer Azalscore gratuitement <ArrowRight className="ml-2 w-5 h-5" />
              </Link>
            </div>
          </div>
        </section>

        {/* Key Differences */}
        <section className="py-16 bg-white">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Différences Clés</h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
              <div className="text-center p-6 bg-blue-50 rounded-xl">
                <Cloud className="w-12 h-12 text-blue-600 mx-auto mb-4" />
                <h3 className="font-semibold text-lg mb-2">Architecture</h3>
                <p className="text-sm text-gray-600">
                  <strong>Azalscore</strong> : 100% Cloud<br />
                  <strong>Sage</strong> : Cloud ou On-premise
                </p>
              </div>
              <div className="text-center p-6 bg-green-50 rounded-xl">
                <Euro className="w-12 h-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-semibold text-lg mb-2">Tarification</h3>
                <p className="text-sm text-gray-600">
                  <strong>Azalscore</strong> : Dès 29€/mois<br />
                  <strong>Sage</strong> : Sur devis
                </p>
              </div>
              <div className="text-center p-6 bg-purple-50 rounded-xl">
                <Zap className="w-12 h-12 text-purple-600 mx-auto mb-4" />
                <h3 className="font-semibold text-lg mb-2">Démarrage</h3>
                <p className="text-sm text-gray-600">
                  <strong>Azalscore</strong> : Immédiat<br />
                  <strong>Sage</strong> : Projet d'intégration
                </p>
              </div>
              <div className="text-center p-6 bg-orange-50 rounded-xl">
                <HeadphonesIcon className="w-12 h-12 text-orange-600 mx-auto mb-4" />
                <h3 className="font-semibold text-lg mb-2">Support</h3>
                <p className="text-sm text-gray-600">
                  <strong>Azalscore</strong> : Direct inclus<br />
                  <strong>Sage</strong> : Via partenaires
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Comparison Table */}
        <section className="py-16 bg-gray-50">
          <div className="max-w-5xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Tableau Comparatif Détaillé</h2>
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-6 py-4 text-left font-semibold">Fonctionnalité</th>
                      <th className="px-6 py-4 text-center font-semibold text-blue-600">Azalscore</th>
                      <th className="px-6 py-4 text-center font-semibold text-green-600">Sage</th>
                      <th className="px-6 py-4 text-left font-semibold">Note</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {comparisonData.map((row, index) => (
                      <tr key={index} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="px-6 py-4 font-medium">{row.feature}</td>
                        <td className="px-6 py-4 text-center">
                          <div className="flex justify-center">
                            <StatusIcon status={row.azalscore} />
                          </div>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <div className="flex justify-center">
                            <StatusIcon status={row.sage} />
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">{row.note || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        {/* When to Choose */}
        <section className="py-16 bg-white">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Quelle solution choisir ?</h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="p-8 border-2 border-blue-200 rounded-xl bg-blue-50">
                <h3 className="text-2xl font-bold text-blue-700 mb-4">Choisir Azalscore si...</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous cherchez une solution moderne et simple</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous préférez un tarif clair sans surprise</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous voulez démarrer rapidement sans projet</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous gérez des interventions terrain</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous êtes une PME (5-100 employés)</span>
                  </li>
                </ul>
              </div>
              <div className="p-8 border-2 border-green-200 rounded-xl bg-green-50">
                <h3 className="text-2xl font-bold text-green-700 mb-4">Choisir Sage si...</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                    <span>Vous avez besoin d'un acteur historique reconnu</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                    <span>Vous préférez une installation on-premise</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                    <span>Vous avez des besoins métier très spécifiques</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                    <span>Vous êtes déjà équipé Sage et satisfait</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-green-600 mt-1 flex-shrink-0" />
                    <span>Vous êtes une grande entreprise (ETI/GE)</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="py-16 bg-blue-600">
          <div className="max-w-4xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Essayez Azalscore gratuitement pendant 30 jours
            </h2>
            <p className="text-blue-100 text-lg mb-8">
              Sans engagement, sans carte bancaire. Migration depuis Sage possible.
            </p>
            <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50">
              Démarrer l'essai gratuit <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-12">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <h4 className="font-bold mb-4">Azalscore</h4>
                <p className="text-gray-400 text-sm">ERP SaaS français pour PME</p>
              </div>
              <div>
                <h4 className="font-bold mb-4">Produit</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><Link to="/features" className="hover:text-white">Fonctionnalités</Link></li>
                  <li><Link to="/pricing" className="hover:text-white">Tarifs</Link></li>
                  <li><Link to="/demo" className="hover:text-white">Démo</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold mb-4">Comparatifs</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><Link to="/comparatif/azalscore-vs-odoo" className="hover:text-white">vs Odoo</Link></li>
                  <li><Link to="/comparatif/azalscore-vs-sage" className="hover:text-white">vs Sage</Link></li>
                  <li><Link to="/comparatif/azalscore-vs-ebp" className="hover:text-white">vs EBP</Link></li>
                </ul>
              </div>
              <div>
                <h4 className="font-bold mb-4">Légal</h4>
                <ul className="space-y-2 text-sm text-gray-400">
                  <li><Link to="/mentions-legales" className="hover:text-white">Mentions légales</Link></li>
                  <li><Link to="/confidentialite" className="hover:text-white">Confidentialité</Link></li>
                  <li><Link to="/cgv" className="hover:text-white">CGV</Link></li>
                </ul>
              </div>
            </div>
            <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400 text-sm">
              © 2026 AZALSCORE - MASITH Développement. Tous droits réservés.
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default VsSage;
