/**
 * AZALSCORE Module - Training Meta
 * Metadonnees du module de formation
 */



export const trainingMeta = {
  id: 'training',
  name: 'Formation',
  description: 'Gestion des formations, sessions, inscriptions et certifications',
  icon: 'GraduationCap',
  route: '/training',
  category: 'hr',
  permissions: ['training:read', 'training:write', 'training:admin'],
  features: [
    'courses',       // Catalogue de formations
    'sessions',      // Sessions de formation
    'enrollments',   // Inscriptions
    'trainers',      // Formateurs
    'certificates',  // Certifications
    'elearning',     // E-learning
  ],
  navigation: [
    {
      label: 'Tableau de bord',
      path: '/training',
      icon: 'LayoutDashboard',
    },
    {
      label: 'Catalogue',
      path: '/training/courses',
      icon: 'BookOpen',
    },
    {
      label: 'Sessions',
      path: '/training/sessions',
      icon: 'Calendar',
    },
    {
      label: 'Formateurs',
      path: '/training/trainers',
      icon: 'UserCheck',
    },
    {
      label: 'Mes formations',
      path: '/training/my',
      icon: 'User',
    },
    {
      label: 'Certificats',
      path: '/training/certificates',
      icon: 'Award',
    },
  ],
  stats: [
    { key: 'total_courses', label: 'Formations', icon: 'BookOpen' },
    { key: 'upcoming_sessions', label: 'Sessions a venir', icon: 'Calendar' },
    { key: 'total_participants', label: 'Participants', icon: 'Users' },
    { key: 'certificates_issued', label: 'Certificats', icon: 'Award' },
  ],
};

export default trainingMeta;
