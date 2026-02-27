/**
 * AZALSCORE Module - DOCUMENTS (GED) - Metadata
 * ==============================================
 */

export const meta = {
  id: 'documents',
  name: 'Documents',
  description: 'Gestion Electronique de Documents (GED)',
  version: '1.0.0',
  category: 'productivity',
  icon: 'FileText',
  color: '#3B82F6',

  routes: [
    { path: '/documents', label: 'Documents', icon: 'FileText' },
    { path: '/documents/folders', label: 'Dossiers', icon: 'Folder' },
    { path: '/documents/shared', label: 'Partages', icon: 'Share2' },
    { path: '/documents/recent', label: 'Recents', icon: 'Clock' },
  ],

  capabilities: [
    'documents:read',
    'documents:write',
    'documents:delete',
    'documents:share',
    'documents:manage',
    'folders:read',
    'folders:write',
    'folders:delete',
  ],

  dependencies: [],
  status: 'active',
  certification: 'B',
};

export default meta;
