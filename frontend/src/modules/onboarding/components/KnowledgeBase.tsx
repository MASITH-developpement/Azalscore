/**
 * AZALSCORE - Base de Connaissances In-App
 * =========================================
 * Articles d'aide contextuels integres dans l'application.
 */

import React, { useState, useMemo } from 'react';
import {
  Search,
  BookOpen,
  ChevronRight,
  ExternalLink,
  ThumbsUp,
  ThumbsDown,
  MessageCircle,
  FileText,
  Video,
  Lightbulb,
  AlertCircle,
  CheckCircle,
  ArrowLeft,
  Star,
} from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

export interface Article {
  id: string;
  title: string;
  summary: string;
  content: string;
  category: string;
  tags: string[];
  module?: string;
  difficulty: 'facile' | 'moyen' | 'avance';
  readTime: string;
  helpful?: number;
  notHelpful?: number;
  relatedArticles?: string[];
  video?: string;
  lastUpdated: string;
}

export interface Category {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  articleCount: number;
}

// ============================================================================
// DONNEES D'ARTICLES
// ============================================================================

export const HELP_ARTICLES: Article[] = [
  // Premiers pas
  {
    id: 'getting-started',
    title: 'Premiers pas avec AZALSCORE',
    summary: 'Apprenez les bases pour bien demarrer',
    category: 'premiers-pas',
    tags: ['debutant', 'connexion', 'interface'],
    difficulty: 'facile',
    readTime: '5 min',
    helpful: 156,
    notHelpful: 3,
    lastUpdated: '2026-02-01',
    content: `
# Premiers pas avec AZALSCORE

Bienvenue sur AZALSCORE ! Ce guide vous aidera a faire vos premiers pas.

## Connexion

1. Ouvrez votre navigateur et allez sur **azalscore.com**
2. Cliquez sur **"Se connecter"**
3. Entrez votre email et mot de passe
4. Si 2FA est active, entrez le code recu

## L'interface

AZALSCORE propose deux modes d'affichage :

- **Mode AZALSCORE** : Interface simplifiee avec menu horizontal
- **Mode ERP** : Interface complete avec menu lateral

Pour changer de mode, cliquez sur votre avatar puis "Basculer en mode..."

## La recherche

Appuyez sur **/** pour ouvrir la recherche globale. Prefixes utiles :
- **@** : Rechercher un client
- **#** : Rechercher un document
- **$** : Rechercher un produit

## Besoin d'aide ?

Cliquez sur l'icone **?** en bas a droite pour acceder a l'assistant Theo.
    `,
  },
  {
    id: 'search-tips',
    title: 'Astuces de recherche',
    summary: 'Trouvez rapidement ce que vous cherchez',
    category: 'premiers-pas',
    tags: ['recherche', 'raccourcis', 'productivite'],
    difficulty: 'facile',
    readTime: '3 min',
    helpful: 89,
    notHelpful: 2,
    lastUpdated: '2026-01-15',
    content: `
# Astuces de recherche

La recherche globale est votre meilleur ami dans AZALSCORE.

## Raccourcis

- Appuyez sur **/** ou **Cmd+K** pour ouvrir la recherche
- Tapez directement ce que vous cherchez
- Utilisez les fleches pour naviguer dans les resultats
- Appuyez sur **Entree** pour ouvrir le resultat

## Prefixes

| Prefixe | Recherche |
|---------|-----------|
| @ | Clients |
| # | Documents |
| $ | Produits |

## Exemples

- \`@Dupont\` → Trouve tous les clients Dupont
- \`#FAC-2026\` → Trouve les factures 2026
- \`$Climatiseur\` → Trouve les produits climatiseur

## Filtres avances

Dans les listes, combinez plusieurs filtres pour affiner vos resultats.
    `,
  },
  // CRM
  {
    id: 'create-customer',
    title: 'Creer un nouveau client',
    summary: 'Guide etape par etape pour ajouter un client',
    category: 'crm',
    tags: ['client', 'creation', 'crm'],
    module: 'crm',
    difficulty: 'facile',
    readTime: '4 min',
    helpful: 234,
    notHelpful: 5,
    lastUpdated: '2026-02-10',
    content: `
# Creer un nouveau client

## Acces

1. Allez dans **CRM** > **Clients**
2. Cliquez sur **"+ Nouveau client"**

## Informations obligatoires

Les champs marques d'un asterisque (*) sont obligatoires :

- **Type** : Entreprise ou Particulier
- **Raison sociale** (entreprise) ou **Nom** (particulier)
- **Email** : Adresse email principale

## Informations recommandees

- **SIRET** : 14 chiffres pour les entreprises francaises
- **Adresse** : Adresse complete avec code postal et ville
- **Telephone** : Numero de contact principal

## Contact principal

Ajoutez au moins un contact avec :
- Nom et prenom
- Fonction
- Email direct
- Telephone

## Informations commerciales

- Commercial assigne
- Conditions de paiement
- Remise par defaut

## Enregistrement

Cliquez sur **"Enregistrer"** pour creer le client.

> **Astuce** : Vous pouvez aussi creer un client depuis un devis ou une commande.
    `,
  },
  // Facturation
  {
    id: 'create-quote',
    title: 'Creer un devis',
    summary: 'Apprenez a creer et envoyer un devis',
    category: 'facturation',
    tags: ['devis', 'facturation', 'vente'],
    module: 'invoicing',
    difficulty: 'facile',
    readTime: '6 min',
    helpful: 312,
    notHelpful: 8,
    lastUpdated: '2026-02-15',
    content: `
# Creer un devis

## Acces

1. Allez dans **Devis**
2. Cliquez sur **"+ Nouveau devis"**

## Selection du client

Commencez par selectionner le client. Tapez son nom pour le rechercher.

Si le client n'existe pas, cliquez sur **"+ Creer"** pour l'ajouter rapidement.

## Ajout des lignes

Pour chaque produit ou service :

1. Cliquez sur **"+ Ajouter une ligne"**
2. Recherchez le produit
3. Ajustez la quantite
4. Le prix se remplit automatiquement

### Modifier un prix

Vous pouvez modifier le prix unitaire directement dans la ligne.

### Appliquer une remise

- **Par ligne** : Cliquez sur la ligne et ajoutez une remise
- **Globale** : Utilisez le champ "Remise" en bas du devis

## Verification

Verifiez les totaux :
- Sous-total HT
- Remises
- Total HT
- TVA
- **Total TTC**

## Validite

Par defaut, le devis est valide 30 jours. Modifiez si necessaire.

## Enregistrement

- **Enregistrer** : Sauvegarde en brouillon
- **Envoyer** : Enregistre et envoie par email
    `,
  },
  // Comptabilite
  {
    id: 'bank-reconciliation',
    title: 'Rapprochement bancaire',
    summary: 'Pointer les operations avec votre releve',
    category: 'comptabilite',
    tags: ['banque', 'rapprochement', 'comptabilite'],
    module: 'treasury',
    difficulty: 'moyen',
    readTime: '8 min',
    helpful: 145,
    notHelpful: 12,
    lastUpdated: '2026-02-05',
    content: `
# Rapprochement bancaire

Le rapprochement bancaire permet de verifier que vos ecritures correspondent au releve de banque.

## Acces

1. Allez dans **Tresorerie** > **Comptes bancaires**
2. Selectionnez le compte
3. Cliquez sur **"Rapprochement"**

## Import du releve

1. Cliquez sur **"Importer releve"**
2. Formats acceptes : CSV, OFX, QIF
3. Selectionnez votre fichier
4. Verifiez le mapping des colonnes

## Pointage

Pour chaque operation du releve :

### Correspondance trouvee
Si AZALSCORE trouve une correspondance, elle est proposee automatiquement.
- Verifiez le montant et la date
- Cliquez sur **✓** pour valider

### Pas de correspondance
Si aucune correspondance n'est trouvee :
- Recherchez manuellement l'ecriture
- Ou creez une nouvelle ecriture

## Verification

L'ecart de rapprochement doit etre **0**.

Si un ecart persiste :
- Verifiez les operations non pointees
- Recherchez les erreurs de saisie
- Verifiez les operations en double

## Validation

Une fois l'ecart a zero, cliquez sur **"Valider le rapprochement"**.
    `,
  },
  // Administration
  {
    id: 'user-management',
    title: 'Gerer les utilisateurs',
    summary: 'Creer et configurer les comptes utilisateurs',
    category: 'administration',
    tags: ['utilisateurs', 'roles', 'administration'],
    module: 'admin',
    difficulty: 'avance',
    readTime: '10 min',
    helpful: 98,
    notHelpful: 4,
    lastUpdated: '2026-02-20',
    content: `
# Gerer les utilisateurs

## Acces

Menu > **Administration** > **Utilisateurs**

## Creer un utilisateur

1. Cliquez sur **"+ Nouvel utilisateur"**
2. Remplissez les informations :
   - Nom et prenom
   - Email (sera l'identifiant)
   - Role(s) a attribuer
3. Options de securite :
   - Forcer changement mot de passe
   - Activer 2FA obligatoire
4. Cliquez sur **"Creer"**

L'utilisateur recoit un email avec ses identifiants.

## Roles disponibles

| Role | Description |
|------|-------------|
| Dirigeant | Acces complet, tableaux de bord |
| Commercial | CRM, devis, commandes |
| Comptable | Comptabilite, tresorerie |
| RH | Ressources humaines |
| Technicien | Interventions |

## Modifier les droits

1. Ouvrez la fiche utilisateur
2. Onglet **Roles**
3. Ajoutez ou retirez des roles

## Desactiver un compte

1. Ouvrez la fiche utilisateur
2. Cliquez sur **"Desactiver"**
3. L'utilisateur ne peut plus se connecter
4. Ses donnees sont conservees
    `,
  },
];

export const HELP_CATEGORIES: Category[] = [
  {
    id: 'premiers-pas',
    name: 'Premiers pas',
    icon: <Star className="w-5 h-5" />,
    description: 'Demarrez avec AZALSCORE',
    articleCount: 5,
  },
  {
    id: 'crm',
    name: 'CRM',
    icon: <FileText className="w-5 h-5" />,
    description: 'Gestion des clients',
    articleCount: 8,
  },
  {
    id: 'facturation',
    name: 'Facturation',
    icon: <FileText className="w-5 h-5" />,
    description: 'Devis et factures',
    articleCount: 12,
  },
  {
    id: 'comptabilite',
    name: 'Comptabilite',
    icon: <FileText className="w-5 h-5" />,
    description: 'Ecritures et etats',
    articleCount: 10,
  },
  {
    id: 'administration',
    name: 'Administration',
    icon: <FileText className="w-5 h-5" />,
    description: 'Configuration systeme',
    articleCount: 6,
  },
];

// ============================================================================
// COMPOSANTS
// ============================================================================

interface KnowledgeBaseProps {
  initialCategory?: string;
  initialArticle?: string;
  contextModule?: string;
}

export function KnowledgeBase({ initialCategory, initialArticle, contextModule }: KnowledgeBaseProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string | null>(initialCategory || null);
  const [selectedArticle, setSelectedArticle] = useState<Article | null>(
    initialArticle ? HELP_ARTICLES.find(a => a.id === initialArticle) || null : null
  );
  const [feedback, setFeedback] = useState<Record<string, 'helpful' | 'not-helpful'>>({});

  // Filtrer les articles
  const filteredArticles = useMemo(() => {
    let articles = HELP_ARTICLES;

    // Filtre par module contextuel
    if (contextModule) {
      articles = articles.filter(a => !a.module || a.module === contextModule);
    }

    // Filtre par categorie
    if (selectedCategory) {
      articles = articles.filter(a => a.category === selectedCategory);
    }

    // Filtre par recherche
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      articles = articles.filter(
        a =>
          a.title.toLowerCase().includes(query) ||
          a.summary.toLowerCase().includes(query) ||
          a.tags.some(t => t.toLowerCase().includes(query))
      );
    }

    return articles;
  }, [searchQuery, selectedCategory, contextModule]);

  const handleFeedback = (articleId: string, type: 'helpful' | 'not-helpful') => {
    setFeedback(prev => ({ ...prev, [articleId]: type }));
    // Envoyer le feedback au serveur
  };

  // Vue article
  if (selectedArticle) {
    return (
      <div className="max-w-3xl mx-auto">
        {/* Back button */}
        <button
          onClick={() => setSelectedArticle(null)}
          className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Retour aux articles
        </button>

        {/* Article header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <span className={`text-xs px-2 py-0.5 rounded-full ${
              selectedArticle.difficulty === 'facile' ? 'bg-green-100 text-green-700' :
              selectedArticle.difficulty === 'moyen' ? 'bg-amber-100 text-amber-700' :
              'bg-purple-100 text-purple-700'
            }`}>
              {selectedArticle.difficulty}
            </span>
            <span className="text-xs text-gray-500">{selectedArticle.readTime} de lecture</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">{selectedArticle.title}</h1>
          <p className="text-gray-600">{selectedArticle.summary}</p>
        </div>

        {/* Article content */}
        <div className="prose prose-blue max-w-none">
          {/* Render markdown content - simplified for example */}
          <div className="whitespace-pre-wrap text-gray-700">
            {selectedArticle.content}
          </div>
        </div>

        {/* Feedback */}
        <div className="mt-8 p-4 bg-gray-50 rounded-xl">
          <p className="text-sm text-gray-600 mb-3">Cet article vous a-t-il ete utile ?</p>
          <div className="flex gap-3">
            <button
              onClick={() => handleFeedback(selectedArticle.id, 'helpful')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm ${
                feedback[selectedArticle.id] === 'helpful'
                  ? 'bg-green-100 text-green-700'
                  : 'bg-white border border-gray-200 text-gray-600 hover:border-green-300'
              }`}
            >
              <ThumbsUp className="w-4 h-4" />
              Oui ({selectedArticle.helpful})
            </button>
            <button
              onClick={() => handleFeedback(selectedArticle.id, 'not-helpful')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm ${
                feedback[selectedArticle.id] === 'not-helpful'
                  ? 'bg-red-100 text-red-700'
                  : 'bg-white border border-gray-200 text-gray-600 hover:border-red-300'
              }`}
            >
              <ThumbsDown className="w-4 h-4" />
              Non ({selectedArticle.notHelpful})
            </button>
          </div>
        </div>

        {/* Related articles */}
        {selectedArticle.relatedArticles && selectedArticle.relatedArticles.length > 0 && (
          <div className="mt-8">
            <h3 className="font-semibold text-gray-900 mb-3">Articles connexes</h3>
            <div className="space-y-2">
              {selectedArticle.relatedArticles.map(id => {
                const related = HELP_ARTICLES.find(a => a.id === id);
                if (!related) return null;
                return (
                  <button
                    key={id}
                    onClick={() => setSelectedArticle(related)}
                    className="w-full flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:border-blue-300 text-left"
                  >
                    <span className="text-gray-700">{related.title}</span>
                    <ChevronRight className="w-4 h-4 text-gray-400" />
                  </button>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }

  // Vue liste
  return (
    <div>
      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Rechercher dans l'aide..."
          className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>

      {/* Categories */}
      {!searchQuery && !selectedCategory && (
        <div className="grid md:grid-cols-2 gap-4 mb-8">
          {HELP_CATEGORIES.map(cat => (
            <button
              key={cat.id}
              onClick={() => setSelectedCategory(cat.id)}
              className="flex items-start gap-4 p-4 bg-white border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-md transition-all text-left"
            >
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600">
                {cat.icon}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{cat.name}</h3>
                <p className="text-sm text-gray-500">{cat.description}</p>
                <p className="text-xs text-gray-400 mt-1">{cat.articleCount} articles</p>
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Category header */}
      {selectedCategory && (
        <div className="flex items-center gap-2 mb-4">
          <button
            onClick={() => setSelectedCategory(null)}
            className="text-blue-600 hover:text-blue-800"
          >
            Toutes les categories
          </button>
          <ChevronRight className="w-4 h-4 text-gray-400" />
          <span className="font-medium text-gray-900">
            {HELP_CATEGORIES.find(c => c.id === selectedCategory)?.name}
          </span>
        </div>
      )}

      {/* Articles list */}
      <div className="space-y-3">
        {filteredArticles.map(article => (
          <button
            key={article.id}
            onClick={() => setSelectedArticle(article)}
            className="w-full flex items-start gap-4 p-4 bg-white border border-gray-200 rounded-xl hover:border-blue-300 hover:shadow-md transition-all text-left"
          >
            <BookOpen className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-medium text-gray-900 mb-1">{article.title}</h3>
              <p className="text-sm text-gray-500 line-clamp-2">{article.summary}</p>
              <div className="flex items-center gap-3 mt-2">
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  article.difficulty === 'facile' ? 'bg-green-100 text-green-700' :
                  article.difficulty === 'moyen' ? 'bg-amber-100 text-amber-700' :
                  'bg-purple-100 text-purple-700'
                }`}>
                  {article.difficulty}
                </span>
                <span className="text-xs text-gray-400">{article.readTime}</span>
                {article.video && (
                  <span className="flex items-center gap-1 text-xs text-blue-600">
                    <Video className="w-3 h-3" />
                    Video
                  </span>
                )}
              </div>
            </div>
            <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
          </button>
        ))}

        {filteredArticles.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            <BookOpen className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>Aucun article trouve</p>
            <p className="text-sm">Essayez avec d'autres mots-cles</p>
          </div>
        )}
      </div>

      {/* Contact support */}
      <div className="mt-8 p-4 bg-blue-50 rounded-xl flex items-start gap-4">
        <MessageCircle className="w-6 h-6 text-blue-600 flex-shrink-0" />
        <div>
          <h4 className="font-medium text-gray-900">Vous ne trouvez pas de reponse ?</h4>
          <p className="text-sm text-gray-600 mb-2">
            Contactez notre equipe support ou demandez a Theo.
          </p>
          <div className="flex gap-2">
            <button className="px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
              Contacter le support
            </button>
            <button className="px-3 py-1.5 bg-white border border-gray-200 text-gray-700 rounded-lg text-sm hover:bg-gray-50">
              Demander a Theo
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default KnowledgeBase;
