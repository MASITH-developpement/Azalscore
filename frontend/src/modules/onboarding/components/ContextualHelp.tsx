/**
 * AZALSCORE Module - Onboarding - Aide Contextuelle
 * Tooltips d'aide integres aux formulaires
 */

import React, { useState } from 'react';
import { HelpCircle, Lightbulb, Sparkles, X } from 'lucide-react';

// ============================================================================
// TYPES
// ============================================================================

interface ContextualHelpProps {
  context: string;
  children: React.ReactNode;
}

// ============================================================================
// HELP CONTENT
// ============================================================================

const helpContent: Record<string, { title: string; tips: string[] }> = {
  'client-form': {
    title: 'Creer un client',
    tips: [
      'Les champs marques * sont obligatoires',
      'Le SIRET doit contenir 14 chiffres',
      'Vous pouvez ajouter plusieurs contacts',
    ],
  },
  'quote-form': {
    title: 'Creer un devis',
    tips: [
      'Selectionnez d\'abord le client',
      'Les prix se calculent automatiquement',
      'La validite par defaut est de 30 jours',
    ],
  },
  'invoice-form': {
    title: 'Creer une facture',
    tips: [
      'Les factures validees ne peuvent plus etre modifiees',
      'Utilisez les avoirs pour les corrections',
      'Le numero est attribue automatiquement',
    ],
  },
  'product-form': {
    title: 'Creer un produit',
    tips: [
      'La reference doit etre unique',
      'Definissez les unites de vente et d\'achat',
      'Les prix peuvent etre mis a jour par import',
    ],
  },
  'intervention-form': {
    title: 'Planifier une intervention',
    tips: [
      'Verifiez la disponibilite du technicien',
      'Ajoutez le materiel necessaire',
      'Le client sera notifie par email',
    ],
  },
};

// ============================================================================
// COMPONENT
// ============================================================================

export function ContextualHelp({ context, children }: ContextualHelpProps) {
  const [isOpen, setIsOpen] = useState(false);

  const help = helpContent[context];
  if (!help) return <>{children}</>;

  return (
    <div className="relative">
      {children}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="absolute -top-2 -right-2 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center hover:bg-blue-200 transition-colors"
      >
        <HelpCircle className="w-4 h-4" />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-8 w-72 bg-white rounded-xl shadow-xl border border-gray-200 p-4 z-50">
          <div className="flex items-center gap-2 mb-3">
            <Lightbulb className="w-5 h-5 text-amber-500" />
            <h4 className="font-semibold text-gray-900">{help.title}</h4>
          </div>
          <ul className="space-y-2">
            {help.tips.map((tip, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-gray-600">
                <Sparkles className="w-4 h-4 text-blue-500 flex-shrink-0 mt-0.5" />
                {tip}
              </li>
            ))}
          </ul>
          <button
            onClick={() => setIsOpen(false)}
            className="absolute top-2 right-2 text-gray-400 hover:text-gray-600"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
}

export default ContextualHelp;
