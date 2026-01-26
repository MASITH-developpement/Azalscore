/**
 * AZALSCORE - Module Template
 * ============================
 * Template pour créer un nouveau module conforme AZA-FE
 */

import React from 'react';
import { BaseViewStandard } from '@/ui-engine/standards/BaseViewStandard';

// Import des composants locaux
import { Tab1View } from './components/Tab1View';
import { Tab2View } from './components/Tab2View';

/**
 * Module Principal
 * Utilise BaseViewStandard pour garantir conformité AZA-FE-ENF
 */
export default function TemplateModule() {
  return (
    <BaseViewStandard
      title="Nom du Module"
      icon="🔧"
      tabs={[
        {
          id: 'tab1',
          label: 'Vue 1',
          content: <Tab1View />,
        },
        {
          id: 'tab2',
          label: 'Vue 2',
          content: <Tab2View />,
        },
      ]}
    />
  );
}
