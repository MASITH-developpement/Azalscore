/**
 * AZALSCORE - Page de détail fonctionnalité
 * Pages SEO individuelles pour chaque module
 */
import React from 'react';
import { useParams, Link, Navigate } from 'react-router-dom';
import { Helmet } from 'react-helmet-async';
import { ArrowRight, Check } from 'lucide-react';

interface FeatureData {
  title: string;
  metaTitle: string;
  metaDescription: string;
  keywords: string;
  headline: string;
  description: string;
  benefits: string[];
  screenshot: string;
  color: string;
}

const featuresData: Record<string, FeatureData> = {
  crm: {
    title: 'CRM',
    metaTitle: 'Module CRM Azalscore | Gestion Relation Client PME',
    metaDescription: 'CRM français intégré à votre ERP : gestion contacts, pipeline ventes, historique client, rappels automatiques. Solution complète pour PME.',
    keywords: 'crm français, gestion relation client, pipeline ventes, erp crm',
    headline: 'CRM intégré pour gérer votre relation client',
    description: 'Centralisez toutes vos interactions clients dans une seule solution. Suivez vos prospects, gérez votre pipeline de ventes et fidélisez vos clients.',
    benefits: [
      'Fiche client 360° avec historique complet',
      'Pipeline de ventes visuel par étapes',
      'Rappels et tâches automatiques',
      'Segmentation et tags clients',
      'Import/export contacts facilité',
      'Synchronisation email intégrée'
    ],
    screenshot: '/screenshots/real-crm.png',
    color: 'blue'
  },
  facturation: {
    title: 'Facturation',
    metaTitle: 'Facturation Électronique 2026 | Azalscore - Factur-X conforme',
    metaDescription: 'Logiciel de facturation électronique conforme 2026 : devis, factures Factur-X, relances automatiques. Solution française pour PME.',
    keywords: 'facturation electronique 2026, factur-x, devis facture, logiciel facturation',
    headline: 'Facturation électronique conforme 2026',
    description: 'Créez vos devis et factures en quelques clics. Conformité totale avec les obligations de facturation électronique 2026 (Factur-X).',
    benefits: [
      'Devis en 2 clics, transformation en facture',
      'Format Factur-X (PDF + XML)',
      'Envoi automatique par email',
      'Relances clients automatiques',
      'Paiement en ligne intégré',
      'Export comptable automatique'
    ],
    screenshot: '/screenshots/real-facturation.png',
    color: 'green'
  },
  comptabilite: {
    title: 'Comptabilité',
    metaTitle: 'Comptabilité PME | Azalscore - Export FEC & Plan Comptable',
    metaDescription: 'Module comptabilité française : plan comptable, export FEC, rapprochement bancaire, TVA. Conforme aux normes fiscales françaises.',
    keywords: 'comptabilite pme, export fec, plan comptable, logiciel comptable',
    headline: 'Comptabilité française simplifiée',
    description: 'Gérez votre comptabilité au quotidien avec un outil pensé pour les PME françaises. Export FEC automatique et conformité fiscale garantie.',
    benefits: [
      'Plan comptable français intégré',
      'Export FEC en un clic',
      'Rapprochement bancaire automatique',
      'Déclarations TVA préparées',
      'Multi-devises supporté',
      'Collaboration avec votre expert-comptable'
    ],
    screenshot: '/screenshots/real-accounting.png',
    color: 'purple'
  },
  inventaire: {
    title: 'Inventaire',
    metaTitle: 'Gestion de Stock | Azalscore - Inventaire Multi-entrepôts',
    metaDescription: 'Gestion de stock temps réel : multi-entrepôts, alertes réapprovisionnement, lots et séries. Solution inventaire pour PME.',
    keywords: 'gestion stock, inventaire, multi entrepots, logiciel stock',
    headline: 'Gestion de stock en temps réel',
    description: 'Suivez vos stocks en temps réel, gérez plusieurs entrepôts et optimisez votre réapprovisionnement automatiquement.',
    benefits: [
      'Stock temps réel multi-dépôts',
      'Alertes réapprovisionnement',
      'Gestion lots et numéros de série',
      'Inventaire partiel ou complet',
      'Valorisation FIFO/LIFO/CMP',
      'Codes-barres intégrés'
    ],
    screenshot: '/screenshots/real-inventory.png',
    color: 'orange'
  },
  rh: {
    title: 'Ressources Humaines',
    metaTitle: 'Gestion RH PME | Azalscore - Employés, Congés, Contrats',
    metaDescription: 'Module RH complet : gestion employés, congés et absences, contrats de travail, évaluations. Solution RH française pour PME.',
    keywords: 'gestion rh, conges absences, ressources humaines pme, logiciel rh',
    headline: 'Ressources humaines simplifiées',
    description: 'Gérez vos employés, leurs congés, absences et contrats depuis une seule interface. Parfait pour les PME de 5 à 250 salariés.',
    benefits: [
      'Fiches employés complètes',
      'Gestion congés et absences',
      'Contrats de travail digitalisés',
      'Évaluations et objectifs',
      'Export DSN préparé',
      'Portail employé self-service'
    ],
    screenshot: '/screenshots/real-hr.png',
    color: 'pink'
  },
  tresorerie: {
    title: 'Trésorerie',
    metaTitle: 'Gestion Trésorerie | Azalscore - Flux, Prévisions, Banque',
    metaDescription: 'Module trésorerie : suivi encaissements, prévisions de trésorerie, rapprochement bancaire automatique. Pilotez votre cash flow.',
    keywords: 'gestion tresorerie, cash flow, previsions tresorerie, rapprochement bancaire',
    headline: 'Pilotez votre trésorerie',
    description: 'Visualisez vos flux de trésorerie, anticipez vos besoins et optimisez votre cash flow avec des prévisions automatiques.',
    benefits: [
      'Vue temps réel des comptes',
      'Prévisions automatiques',
      'Rapprochement bancaire auto',
      'Alertes seuils bas',
      'Multi-banques centralisé',
      'Export vers comptabilité'
    ],
    screenshot: '/screenshots/real-treasury.png',
    color: 'cyan'
  },
  pos: {
    title: 'Point de Vente',
    metaTitle: 'Caisse Enregistreuse | Azalscore - POS Tactile NF525',
    metaDescription: 'Point de vente tactile conforme NF525 : caisse enregistreuse, gestion multi-caisses, tickets conformes. Solution POS française.',
    keywords: 'caisse enregistreuse, pos, point de vente, nf525',
    headline: 'Caisse enregistreuse moderne',
    description: 'Point de vente tactile conforme NF525. Idéal pour boutiques, restaurants et commerces de proximité.',
    benefits: [
      'Interface tactile intuitive',
      'Conformité NF525 garantie',
      'Multi-caisses synchronisées',
      'Paiements CB, espèces, TR',
      'Clôture de caisse automatique',
      'Statistiques ventes temps réel'
    ],
    screenshot: '/screenshots/real-pos.png',
    color: 'amber'
  },
  interventions: {
    title: 'Interventions',
    metaTitle: 'Gestion Interventions Terrain | Azalscore - Planning Techniciens',
    metaDescription: 'Module interventions : planning techniciens, suivi GPS, rapports terrain, devis sur site. Solution pour entreprises de services.',
    keywords: 'gestion interventions, planning techniciens, application terrain, erp services',
    headline: 'Gérez vos interventions terrain',
    description: 'Planifiez vos interventions, suivez vos techniciens en temps réel et digitalisez vos rapports terrain.',
    benefits: [
      'Planning visuel drag & drop',
      'Application mobile technicien',
      'Géolocalisation temps réel',
      'Rapports d\'intervention digitaux',
      'Signature client sur tablette',
      'Facturation immédiate'
    ],
    screenshot: '/screenshots/real-interventions.png',
    color: 'teal'
  }
};

const colorClasses: Record<string, { bg: string; text: string; button: string }> = {
  blue: { bg: 'bg-blue-50', text: 'text-blue-600', button: 'bg-blue-600 hover:bg-blue-700' },
  green: { bg: 'bg-green-50', text: 'text-green-600', button: 'bg-green-600 hover:bg-green-700' },
  purple: { bg: 'bg-purple-50', text: 'text-purple-600', button: 'bg-purple-600 hover:bg-purple-700' },
  orange: { bg: 'bg-orange-50', text: 'text-orange-600', button: 'bg-orange-600 hover:bg-orange-700' },
  pink: { bg: 'bg-pink-50', text: 'text-pink-600', button: 'bg-pink-600 hover:bg-pink-700' },
  cyan: { bg: 'bg-cyan-50', text: 'text-cyan-600', button: 'bg-cyan-600 hover:bg-cyan-700' },
  amber: { bg: 'bg-amber-50', text: 'text-amber-600', button: 'bg-amber-600 hover:bg-amber-700' },
  teal: { bg: 'bg-teal-50', text: 'text-teal-600', button: 'bg-teal-600 hover:bg-teal-700' }
};

const FeatureDetail: React.FC = () => {
  const { feature } = useParams<{ feature: string }>();

  if (!feature || !featuresData[feature]) {
    return <Navigate to="/features" replace />;
  }

  const data = featuresData[feature];
  const colors = colorClasses[data.color] || colorClasses.blue;

  return (
    <>
      <Helmet>
        <title>{data.metaTitle}</title>
        <meta name="description" content={data.metaDescription} />
        <meta name="keywords" content={data.keywords} />
        <link rel="canonical" href={`https://azalscore.com/features/${feature}`} />
        <meta property="og:title" content={data.metaTitle} />
        <meta property="og:description" content={data.metaDescription} />
        <meta property="og:url" content={`https://azalscore.com/features/${feature}`} />
        <meta property="og:image" content={`https://azalscore.com${data.screenshot}`} />
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
              { "@type": "ListItem", "position": 1, "name": "Accueil", "item": "https://azalscore.com" },
              { "@type": "ListItem", "position": 2, "name": "Fonctionnalités", "item": "https://azalscore.com/features" },
              { "@type": "ListItem", "position": 3, "name": data.title, "item": `https://azalscore.com/features/${feature}` }
            ]
          })}
        </script>
        <script type="application/ld+json">
          {JSON.stringify({
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": `Azalscore - Module ${data.title}`,
            "applicationCategory": "BusinessApplication",
            "description": data.metaDescription,
            "url": `https://azalscore.com/features/${feature}`,
            "screenshot": `https://azalscore.com${data.screenshot}`,
            "offers": {
              "@type": "Offer",
              "price": "0",
              "priceCurrency": "EUR",
              "description": "Essai gratuit 30 jours"
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
        <section className={`${colors.bg} py-20`}>
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-12 items-center">
              <div>
                <Link to="/features" className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-4">
                  ← Toutes les fonctionnalités
                </Link>
                <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-6">
                  {data.headline}
                </h1>
                <p className="text-xl text-gray-600 mb-8">
                  {data.description}
                </p>
                <div className="flex flex-col sm:flex-row gap-4">
                  <Link to="/essai-gratuit" className={`inline-flex items-center justify-center ${colors.button} text-white px-6 py-3 rounded-lg font-semibold`}>
                    Essayer gratuitement <ArrowRight className="ml-2 w-5 h-5" />
                  </Link>
                  <Link to="/demo" className="inline-flex items-center justify-center border border-gray-300 bg-white px-6 py-3 rounded-lg font-semibold hover:bg-gray-50">
                    Voir une démo
                  </Link>
                </div>
              </div>
              <div className="bg-white rounded-2xl shadow-xl p-4">
                <img
                  src={data.screenshot}
                  alt={`Interface ${data.title} Azalscore`}
                  className="rounded-lg"
                  loading="lazy"
                />
              </div>
            </div>
          </div>
        </section>

        {/* Benefits */}
        <section className="py-20 bg-white">
          <div className="max-w-4xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Ce que vous pouvez faire</h2>
            <div className="grid md:grid-cols-2 gap-6">
              {data.benefits.map((benefit, index) => (
                <div key={index} className="flex items-start gap-3 p-4 bg-gray-50 rounded-lg">
                  <Check className={`w-6 h-6 ${colors.text} flex-shrink-0 mt-0.5`} />
                  <span className="text-gray-700">{benefit}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Other Features */}
        <section className="py-20 bg-gray-50">
          <div className="max-w-6xl mx-auto px-4">
            <h2 className="text-3xl font-bold text-center mb-12">Autres modules inclus</h2>
            <div className="grid md:grid-cols-4 gap-4">
              {Object.entries(featuresData)
                .filter(([key]) => key !== feature)
                .slice(0, 4)
                .map(([key, f]) => (
                  <Link
                    key={key}
                    to={`/features/${key}`}
                    className="p-4 bg-white rounded-lg shadow-sm hover:shadow-md transition-shadow text-center"
                  >
                    <h3 className="font-semibold">{f.title}</h3>
                  </Link>
                ))}
            </div>
          </div>
        </section>

        {/* CTA */}
        <section className={`py-16 ${colors.button.split(' ')[0]}`}>
          <div className="max-w-4xl mx-auto px-4 text-center">
            <h2 className="text-3xl font-bold text-white mb-4">
              Essayez {data.title} gratuitement
            </h2>
            <p className="text-white/80 text-lg mb-8">
              30 jours d'essai. Toutes les fonctionnalités incluses.
            </p>
            <Link to="/essai-gratuit" className="inline-flex items-center justify-center bg-white text-gray-900 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-gray-100">
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

export default FeatureDetail;
