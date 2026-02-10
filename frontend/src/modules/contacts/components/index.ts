/**
 * AZALS MODULE - Contacts Unifiés - Exports Composants
 * =====================================================
 *
 * Sous-programmes réutilisables pour la gestion des contacts.
 */

// Sélecteur de contact (pour tous les modules)
export { ContactSelector } from './ContactSelector';
export { default as ContactSelectorDefault } from './ContactSelector';

// Gestionnaire des personnes de contact
export { ContactPersonsManager } from './ContactPersonsManager';
export { default as ContactPersonsManagerDefault } from './ContactPersonsManager';

// Gestionnaire des adresses
export { AddressManager } from './AddressManager';
export { default as AddressManagerDefault } from './AddressManager';

// Upload de logo/photo
export { LogoUploader } from './LogoUploader';
export { default as LogoUploaderDefault } from './LogoUploader';
