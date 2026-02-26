/**
 * AZALSCORE - Comparatif Azalscore vs Pennylane
 * Page SEO pour le positionnement sur les recherches comparatives
 *
 * PRINCIPES :
 * - Comparaison factuelle et honnête
 * - Pas de dénigrement du concurrent
 * - Mise en avant des différences objectives
 */
import React from 'react';
import { Link } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { Check, X, Minus, ArrowRight, Shield, Server, Euro, Users, BarChart3, Package, FileText, CreditCard } from 'lucide-react';
import { Footer } from '../../components/Footer';
import { AzalscoreLogo } from '../../components/Logo';

interface ComparisonRow {
  feature: string;
  azalscore: 'yes' | 'no' | 'partial' | string;
  pennylane: 'yes' | 'no' | 'partial' | string;
  note?: string;
}

const comparisonData: ComparisonRow[] = [
  { feature: 'Hébergement France', azalscore: 'yes', pennylane: 'yes' },
  { feature: 'Comptabilité complète', azalscore: 'yes', pennylane: 'yes', note: 'Pennylane est spécialisé comptabilité' },
  { feature: 'Facturation électronique 2026', azalscore: 'yes', pennylane: 'yes' },
  { feature: 'Format Factur-X natif', azalscore: 'yes', pennylane: 'yes' },
  { feature: 'Export FEC automatique', azalscore: 'yes', pennylane: 'yes' },
  { feature: 'CRM intégré', azalscore: 'yes', pennylane: 'no', note: 'Pennylane nécessite intégration tierce' },
  { feature: 'Gestion de stock', azalscore: 'yes', pennylane: 'no', note: 'Non disponible sur Pennylane' },
  { feature: 'Ressources Humaines', azalscore: 'yes', pennylane: 'partial', note: 'Notes de frais uniquement' },
  { feature: 'Point de Vente (POS)', azalscore: 'yes', pennylane: 'no' },
  { feature: 'Gestion des interventions', azalscore: 'yes', pennylane: 'no' },
  { feature: 'Rapprochement bancaire auto', azalscore: 'yes', pennylane: 'yes', note: 'Point fort de Pennylane' },
  { feature: 'OCR factures fournisseurs', azalscore: 'yes', pennylane: 'yes', note: 'Très performant sur Pennylane' },
  { feature: 'Collaboration expert-comptable', azalscore: 'yes', pennylane: 'yes', note: 'Cœur de métier Pennylane' },
  { feature: 'API REST complète', azalscore: 'yes', pennylane: 'yes' },
  { feature: 'Multi-sociétés', azalscore: 'yes', pennylane: 'yes' },
  { feature: 'Trésorerie et prévisions', azalscore: 'yes', pennylane: 'partial' },
  { feature: 'Gestion de projets', azalscore: 'yes', pennylane: 'no' },
  { feature: 'Essai gratuit', azalscore: '30 jours', pennylane: 'Démo' },
  { feature: 'Conformité RGPD', azalscore: 'yes', pennylane: 'yes' },
];

const StatusIcon: React.FC<{ status: string }> = ({ status }) => {
  if (status === 'yes') return <Check className="w-5 h-5 text-green-600" />;
  if (status === 'no') return <X className="w-5 h-5 text-red-500" />;
  if (status === 'partial') return <Minus className="w-5 h-5 text-yellow-500" />;
  return <span className="text-sm text-gray-700">{status}</span>;
};

const VsPennylane: React.FC = () => {
  return (
    <>
      <Helmet>
        <title>Azalscore vs Pennylane : Comparatif 2026 | ERP vs Comptabilité</title>
        <meta name="description" content="Comparaison Azalscore vs Pennylane. ERP complet ou logiciel comptable ? Fonctionnalités, tarifs, différences. Guide pour choisir la meilleure solution pour votre PME." />
        <meta name="keywords" content="azalscore vs pennylane, comparatif erp comptabilité, alternative pennylane, logiciel comptabilité pme, erp français" />
        <link rel="canonical" href="https://azalscore.com/comparatif/pennylane" />
        <meta property="og:title" content="Azalscore vs Pennylane : Comparatif 2026" />
        <meta property="og:description" content="ERP complet ou logiciel comptable ? Comparaison pour choisir la meilleure solution." />
        <meta property="og:url" content="https://azalscore.com/comparatif/pennylane" />
        <meta property="og:type" content="article" />
        <meta property="og:image" content="https://azalscore.com/og-image.png" />
        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:title" content="Azalscore vs Pennylane : Comparatif 2026" />
        <meta name="twitter:description" content="ERP complet ou logiciel comptable ? Comparaison pour PME." />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://azalscore.com" },
              { "@type": "ListItem", "position": 2, "name": "Comparatifs", "item": "https://azalscore.com/comparatif" },
              { "@type": "ListItem", "position": 3, "name": "Azalscore vs Pennylane", "item": "https://azalscore.com/comparatif/pennylane" }
            ]
          })}
        </script>
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "Azalscore vs Pennylane : Comparatif Complet 2026",
            "description": "Comparaison objective entre Azalscore (ERP complet) et Pennylane (logiciel comptable). Guide de choix pour PME françaises.",
            "author": { "@type": "Organization", "name": "Azalscore" },
            "publisher": { "@type": "Organization", "name": "Azalscore", "logo": { "@type": "ImageObject", "url": "https://azalscore.com/pwa-512x512.png" } },
            "datePublished": "2026-02-26",
            "dateModified": "2026-02-26"
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
              <Link to="/features" className="text-gray-600 hover:text-blue-600">Fonctionnalités</Link>
              <Link to="/pricing" className="text-gray-600 hover:text-blue-600">Tarifs</Link>
              <Link to="/comparatif" className="text-gray-600 hover:text-blue-600">Comparatifs</Link>
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
            <li><Link to="/comparatif" className="hover:text-blue-600">Comparatifs</Link></li>
            <li className="mx-2">/</li>
            <li className="text-gray-900">Azalscore vs Pennylane</li>
          </ol>
        </nav>

        {/* Hero */}
        <section className="max-w-7xl mx-auto px-4 py-12">
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Azalscore vs Pennylane
            </h1>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              ERP complet ou logiciel comptable spécialisé ? Découvrez les différences
              pour choisir la solution adaptée à votre PME.
            </p>
          </div>

          {/* Quick Summary */}
          <div className="grid md:grid-cols-2 gap-8 mb-16">
            <div className="bg-white rounded-xl shadow-lg p-8 border-2 border-blue-600">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xl">A</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Azalscore</h2>
                  <p className="text-gray-500">ERP complet tout-en-un</p>
                </div>
              </div>
              <ul className="space-y-3">
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>8 modules intégrés (CRM, Compta, Stock, RH...)</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>Gestion commerciale complète</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>Point de vente intégré</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>Gestion des interventions terrain</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>Tarif unique tout inclus</span>
                </li>
              </ul>
              <p className="mt-6 text-sm text-gray-500">
                <strong>Idéal pour :</strong> PME cherchant une solution tout-en-un pour gérer
                l'ensemble de leur activité (commercial, stock, comptabilité, RH).
              </p>
            </div>

            <div className="bg-white rounded-xl shadow-lg p-8">
              <div className="flex items-center gap-4 mb-6">
                <div className="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xl">P</span>
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">Pennylane</h2>
                  <p className="text-gray-500">Comptabilité collaborative</p>
                </div>
              </div>
              <ul className="space-y-3">
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>Comptabilité automatisée</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>OCR factures performant</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>Collaboration expert-comptable native</span>
                </li>
                <li className="flex items-center gap-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <span>Rapprochement bancaire automatique</span>
                </li>
                <li className="flex items-center gap-2">
                  <X className="w-5 h-5 text-red-500" />
                  <span className="text-gray-500">Pas de CRM, stock, RH intégrés</span>
                </li>
              </ul>
              <p className="mt-6 text-sm text-gray-500">
                <strong>Idéal pour :</strong> Entreprises focalisées sur la comptabilité
                avec un expert-comptable, sans besoins de gestion commerciale ou stock.
              </p>
            </div>
          </div>
        </section>

        {/* Comparison Table */}
        <section className="bg-white py-16">
          <div className="max-w-7xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Comparatif détaillé des fonctionnalités</h2>

            <div className="overflow-x-auto">
              <table className="w-full border-collapse">
                <thead>
                  <tr className="border-b-2">
                    <th className="text-left py-4 px-4 font-semibold">Fonctionnalité</th>
                    <th className="text-center py-4 px-4 font-semibold text-blue-600">Azalscore</th>
                    <th className="text-center py-4 px-4 font-semibold text-purple-600">Pennylane</th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-500">Note</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisonData.map((row, idx) => (
                    <tr key={idx} className={idx % 2 === 0 ? 'bg-gray-50' : ''}>
                      <td className="py-3 px-4 font-medium">{row.feature}</td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex justify-center">
                          <StatusIcon status={row.azalscore} />
                        </div>
                      </td>
                      <td className="py-3 px-4 text-center">
                        <div className="flex justify-center">
                          <StatusIcon status={row.pennylane} />
                        </div>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500">{row.note || '-'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </section>

        {/* Key Differences */}
        <section className="max-w-7xl mx-auto px-4 py-16">
          <h2 className="text-3xl font-bold text-center mb-12">Les différences clés</h2>

          <div className="grid md:grid-cols-2 gap-8">
            <div className="bg-white rounded-xl p-8 shadow-lg">
              <div className="flex items-center gap-3 mb-4">
                <Package className="w-8 h-8 text-blue-600" />
                <h3 className="text-xl font-bold">Périmètre fonctionnel</h3>
              </div>
              <p className="text-gray-600 mb-4">
                <strong>Azalscore</strong> est un ERP complet qui couvre l'ensemble des besoins
                d'une PME : CRM, devis/factures, comptabilité, stock, RH, point de vente,
                interventions et trésorerie.
              </p>
              <p className="text-gray-600">
                <strong>Pennylane</strong> se concentre sur la comptabilité et la facturation,
                avec une excellente intégration expert-comptable. Pour le CRM ou le stock,
                il faut ajouter des outils tiers.
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-lg">
              <div className="flex items-center gap-3 mb-4">
                <Users className="w-8 h-8 text-blue-600" />
                <h3 className="text-xl font-bold">Profil utilisateur</h3>
              </div>
              <p className="text-gray-600 mb-4">
                <strong>Azalscore</strong> s'adresse aux PME qui veulent centraliser toute leur
                gestion dans un seul outil, sans multiplier les abonnements et intégrations.
              </p>
              <p className="text-gray-600">
                <strong>Pennylane</strong> convient aux entreprises dont le besoin principal est
                la comptabilité automatisée et la collaboration avec leur expert-comptable.
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-lg">
              <div className="flex items-center gap-3 mb-4">
                <Euro className="w-8 h-8 text-blue-600" />
                <h3 className="text-xl font-bold">Modèle tarifaire</h3>
              </div>
              <p className="text-gray-600 mb-4">
                <strong>Azalscore</strong> propose un tarif unique tout inclus : tous les modules
                sont accessibles sans supplément (à partir de 29 EUR/mois).
              </p>
              <p className="text-gray-600">
                <strong>Pennylane</strong> propose des formules selon le volume de transactions,
                avec des options payantes pour certaines fonctionnalités avancées.
              </p>
            </div>

            <div className="bg-white rounded-xl p-8 shadow-lg">
              <div className="flex items-center gap-3 mb-4">
                <BarChart3 className="w-8 h-8 text-blue-600" />
                <h3 className="text-xl font-bold">Points forts respectifs</h3>
              </div>
              <p className="text-gray-600 mb-4">
                <strong>Azalscore</strong> excelle dans la gestion commerciale complète :
                pipeline CRM, devis, commandes, stock, livraisons, interventions terrain.
              </p>
              <p className="text-gray-600">
                <strong>Pennylane</strong> excelle dans l'automatisation comptable :
                OCR factures, rapprochement bancaire, collaboration temps réel avec le cabinet.
              </p>
            </div>
          </div>
        </section>

        {/* When to choose */}
        <section className="bg-blue-50 py-16">
          <div className="max-w-7xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Quelle solution choisir ?</h2>

            <div className="grid md:grid-cols-2 gap-8">
              <div className="bg-white rounded-xl p-8">
                <h3 className="text-xl font-bold text-blue-600 mb-4">Choisissez Azalscore si vous :</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Avez besoin d'un CRM pour gérer vos prospects et clients</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Gérez un stock de produits ou matières premières</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Faites de la vente au comptoir (commerce, restaurant)</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Envoyez des techniciens en intervention</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Voulez un seul outil pour tout gérer</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Préférez un tarif fixe prévisible</span>
                  </li>
                </ul>
              </div>

              <div className="bg-white rounded-xl p-8">
                <h3 className="text-xl font-bold text-purple-600 mb-4">Choisissez Pennylane si vous :</h3>
                <ul className="space-y-3">
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>N'avez besoin que de comptabilité et facturation</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Travaillez étroitement avec un expert-comptable</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Recevez beaucoup de factures fournisseurs à scanner</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Avez déjà un CRM et un outil de gestion de stock</span>
                  </li>
                  <li className="flex items-start gap-2">
                    <Check className="w-5 h-5 text-green-600 mt-0.5" />
                    <span>Êtes une société de services sans stock physique</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className="max-w-7xl mx-auto px-4 py-16 text-center">
          <h2 className="text-3xl font-bold mb-4">Testez Azalscore gratuitement</h2>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            30 jours d'essai gratuit, sans engagement, sans carte bancaire.
            Découvrez tous les modules et fonctionnalités.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/essai-gratuit"
              className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition"
            >
              Démarrer l'essai gratuit
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/demo"
              className="inline-flex items-center gap-2 border-2 border-blue-600 text-blue-600 px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-50 transition"
            >
              Demander une démo
            </Link>
          </div>
        </section>

        {/* Related */}
        <section className="bg-gray-100 py-16">
          <div className="max-w-7xl mx-auto px-4">
            <h2 className="text-2xl font-bold mb-8">Autres comparatifs</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <Link to="/comparatif/odoo" className="bg-white rounded-lg p-6 hover:shadow-lg transition">
                <h3 className="font-bold mb-2">Azalscore vs Odoo</h3>
                <p className="text-gray-600 text-sm">Comparaison avec l'ERP open source belge</p>
              </Link>
              <Link to="/comparatif/sage" className="bg-white rounded-lg p-6 hover:shadow-lg transition">
                <h3 className="font-bold mb-2">Azalscore vs Sage</h3>
                <p className="text-gray-600 text-sm">Comparaison avec le leader historique</p>
              </Link>
              <Link to="/comparatif/ebp" className="bg-white rounded-lg p-6 hover:shadow-lg transition">
                <h3 className="font-bold mb-2">Azalscore vs EBP</h3>
                <p className="text-gray-600 text-sm">Comparaison avec la solution française</p>
              </Link>
            </div>
          </div>
        </section>

        {/* Footer */}
        <Footer />
      </div>
    </>
  );
};

export default VsPennylane;
