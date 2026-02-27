/**
 * AZALSCORE Module - Workflows Meta
 * Metadonnees du module BPM/Workflows
 */



export const workflowsMeta = {
  id: 'workflows',
  name: 'Workflows (BPM)',
  description: 'Gestion des processus metier - Workflows, approbations, automatisation',
  icon: 'Workflow',
  route: '/workflows',
  category: 'automation',
  permissions: ['workflows:read', 'workflows:write', 'workflows:admin'],
  features: [
    'definitions',  // Definition de workflows
    'instances',    // Instances en cours
    'tasks',        // Taches a traiter
    'designer',     // Editeur visuel
    'monitoring',   // Supervision
  ],
  navigation: [
    {
      label: 'Tableau de bord',
      path: '/workflows',
      icon: 'LayoutDashboard',
    },
    {
      label: 'Mes taches',
      path: '/workflows/tasks',
      icon: 'CheckSquare',
    },
    {
      label: 'Definitions',
      path: '/workflows/definitions',
      icon: 'GitBranch',
    },
    {
      label: 'Instances',
      path: '/workflows/instances',
      icon: 'Play',
    },
  ],
  stats: [
    { key: 'pending_tasks', label: 'Taches en attente', icon: 'Clock' },
    { key: 'running_instances', label: 'En cours', icon: 'Play' },
    { key: 'completed_today', label: 'Termines', icon: 'CheckCircle' },
    { key: 'sla_breach_rate', label: 'Depassement SLA', icon: 'AlertTriangle', format: 'percent' },
  ],
};

export default workflowsMeta;
