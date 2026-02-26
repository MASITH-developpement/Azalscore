/**
 * AZALSCORE - Comparatif Azalscore vs EBP
 * Page SEO pour le positionnement sur les recherches comparatives
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Check, X, Minus, ArrowRight, Cloud, Smartphone, Layers, RefreshCw } from 'lucide-react';
import { Footer } from '../../components/Footer';
import { AzalscoreLogo } from '../../components/Logo';

interface ComparisonRow {
  feature: string;
  azalscore: 'yes' | 'no' | 'partial' | string;
  ebp: 'yes' | 'no' | 'partial' | string;
  note?: string;
}

const comparisonData: ComparisonRow[] = [
  { feature: 'Solution 100% Cloud', azalscore: 'yes', ebp: 'partial', note: 'EBP propose aussi versions locales' },
  { feature: 'Hébergement France', azalscore: 'yes', ebp: 'yes' },
  { feature: 'Facturation électronique 2026', azalscore: 'yes', ebp: 'yes' },
  { feature: 'Format Factur-X natif', azalscore: 'yes', ebp: 'yes' },
  { feature: 'Export FEC automatique', azalscore: 'yes', ebp: 'yes' },
  { feature: 'CRM intégré', azalscore: 'yes', ebp: 'partial', note: 'Module CRM séparé' },
  { feature: 'Gestion de stock', azalscore: 'yes', ebp: 'yes' },
  { feature: 'Ressources Humaines', azalscore: 'yes', ebp: 'yes', note: 'EBP Paie séparé' },
  { feature: 'Point de Vente (POS)', azalscore: 'yes', ebp: 'yes', note: 'EBP Point de Vente' },
  { feature: 'Gestion des interventions', azalscore: 'yes', ebp: 'no' },
  { feature: 'Interface web moderne', azalscore: 'yes', ebp: 'partial', note: 'Interface Windows native' },
  { feature: 'Application mobile native', azalscore: 'yes', ebp: 'partial' },
  { feature: 'Tous modules inclus', azalscore: 'yes', ebp: 'no', note: 'Modules vendus séparément' },
  { feature: 'API REST complète', azalscore: 'yes', ebp: 'partial' },
  { feature: 'Multi-sociétés', azalscore: 'yes', ebp: 'yes' },
  { feature: 'Comptabilité certifiée', azalscore: 'yes', ebp: 'yes', note: 'NF Logiciel comptable' },
  { feature: 'Essai gratuit', azalscore: '30 jours', ebp: '30 jours' },
  { feature: 'Conformité RGPD', azalscore: 'yes', ebp: 'yes' },
];

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  if (status === 'yes') return <Check className="w-5 h-5 text-green-600" />;
  if (status === 'no') return <X className="w-5 h-5 text-red-500" />;
  if (status === 'partial') return <Minus className="w-5 h-5 text-yellow-500" />;
  return <span className="text-sm text-gray-700">{status}</span>;
};

const VsEbp: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Azalscore vs EBP : Comparatif ERP 2026 | Alternative cloud à EBP</title>
        <meta name="description" content="Comparaison entre Azalscore et EBP. Solution cloud tout-en-un vs logiciels modulaires. Guide pour choisir votre ERP de gestion française." />
        <meta name="keywords" content="azalscore vs ebp, comparatif erp, alternative ebp, erp français, ebp gestion commerciale" />
        <link rel="canonical" href="https://azalscore.com/comparatif/ebp" />
        <meta property="og:title" content="Azalscore vs EBP : Comparatif ERP 2026" />
        <meta property="og:description" content="Alternative cloud moderne à EBP pour les TPE/PME françaises." />
        <meta property="og:url" content="https://azalscore.com/comparatif/ebp" />
        <meta property="og:image" content="https://azalscore.com/screenshots/comparatif-ebp.png" />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://azalscore.com" },
              { "@type": "ListItem", "position": 2, "name": "Comparatifs", "item": "https://azalscore.com/comparatif" },
              { "@type": "ListItem", "position": 3, "name": "Azalscore vs EBP", "item": "https://azalscore.com/comparatif/ebp" }
            ]
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
              <Link to="/" className="flex items-center">
                <AzalscoreLogo size={40} />
              </Link>
            </div>
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
              Azalscore vs EBP : Comparatif ERP
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Solution cloud tout-en-un contre logiciels modulaires : quel choix pour votre gestion d'entreprise ?
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
                  <strong>EBP</strong> : Local + Cloud
                </p>
              </div>
              <div className="text-center p-6 bg-green-50 rounded-xl">
                <Layers className="w-12 h-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-semibold text-lg mb-2">Modules</h3>
                <p className="text-sm text-gray-600">
                  <strong>Azalscore</strong> : Tout inclus<br />
                  <strong>EBP</strong> : À la carte
                </p>
              </div>
              <div className="text-center p-6 bg-purple-50 rounded-xl">
                <Smartphone className="w-12 h-12 text-purple-600 mx-auto mb-4" />
                <h3 className="font-semibold text-lg mb-2">Interface</h3>
                <p className="text-sm text-gray-600">
                  <strong>Azalscore</strong> : Web/Mobile<br />
                  <strong>EBP</strong> : Windows natif
                </p>
              </div>
              <div className="text-center p-6 bg-orange-50 rounded-xl">
                <RefreshCw className="w-12 h-12 text-orange-600 mx-auto mb-4" />
                <h3 className="font-semibold text-lg mb-2">Mises à jour</h3>
                <p className="text-sm text-gray-600">
                  <strong>Azalscore</strong> : Auto cloud<br />
                  <strong>EBP</strong> : Manuelles
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
                      <th className="px-6 py-4 text-center font-semibold text-orange-600">EBP</th>
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
                            <StatusIcon status={row.ebp} />
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
                    <span>Vous voulez tout dans une seule solution</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous travaillez souvent en mobilité</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous ne voulez pas gérer les mises à jour</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous gérez des interventions terrain</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-blue-600 mt-1 flex-shrink-0" />
                    <span>Vous préférez les interfaces web modernes</span>
                  </li>
                </ul>
              </div>
              <div className="p-8 border-2 border-orange-200 rounded-xl bg-orange-50">
                <h3 className="text-2xl font-bold text-orange-700 mb-4">Choisir EBP si...</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-orange-600 mt-1 flex-shrink-0" />
                    <span>Vous préférez une installation locale</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-orange-600 mt-1 flex-shrink-0" />
                    <span>Vous n'avez besoin que d'un module spécifique</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-orange-600 mt-1 flex-shrink-0" />
                    <span>Vous êtes habitué aux interfaces Windows</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-orange-600 mt-1 flex-shrink-0" />
                    <span>Vous êtes déjà équipé EBP et satisfait</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <Check className="w-5 h-5 text-orange-600 mt-1 flex-shrink-0" />
                    <span>Vous avez une connexion internet instable</span>
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
              Sans engagement, sans carte bancaire. Import depuis EBP disponible.
            </p>
            <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-white text-blue-600 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-blue-50">
              Démarrer l'essai gratuit <ArrowRight className="ml-2 w-5 h-5" />
            </Link>
          </div>
        </section>

        {/* Footer */}
        <Footer />
      </div>
    </>
  );
};

export default VsEbp;
