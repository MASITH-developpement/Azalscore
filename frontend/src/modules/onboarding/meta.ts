/**
 * AZALSCORE - Onboarding Module Meta
 * ====================================
 * Metadonnees du module Onboarding / Formation.
 */

import { GraduationCap } from 'lucide-react';

export const moduleMeta = {
  id: 'onboarding',
  name: 'Formation & Aide',
  description: 'Systeme de formation integre avec tours guides, aide contextuelle et gamification',
  icon: GraduationCap,
  category: 'support',
  path: '/formation',
  permissions: ['user.onboarding.view'],
  tags: ['formation', 'aide', 'onboarding', 'tutoriel', 'gamification'],
  version: '1.0.0',
  status: 'active',
  features: [
    'Tours guides interactifs',
    'Centre de formation',
    'Videos tutorielles',
    'Documentation integree',
    'Aide contextuelle',
    'Systeme de gamification',
    'Progression et badges',
    'Examens de niveau',
    'Quiz d\'entrainement',
    'Micro-learning',
    'Base de connaissances',
    'Support multilingue',
  ],
  dependencies: [],
  tier: 'core',
} as const;

export type ModuleMeta = typeof moduleMeta;
export const onboardingMeta = moduleMeta;
export default moduleMeta;
