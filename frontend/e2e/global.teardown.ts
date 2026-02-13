/**
 * AZALSCORE - Global Teardown
 *
 * Execute une seule fois APRES tous les tests.
 * Nettoie les fichiers temporaires.
 */

import { test as teardown } from '@playwright/test';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// ES Module compatibility
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const AUTH_FILE = path.join(__dirname, '.auth/user.json');

teardown('Nettoyage global', async () => {
  // Optionnel: supprimer le fichier d'auth
  // Decommenter si on veut un login frais a chaque run
  //
  // if (fs.existsSync(AUTH_FILE)) {
  //   fs.unlinkSync(AUTH_FILE);
  //   console.log('[TEARDOWN] Fichier auth supprime');
  // }

  console.log('[TEARDOWN] Nettoyage termine');
});
