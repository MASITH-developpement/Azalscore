/**
 * AZALSCORE Module - Shipping Meta
 * Metadonnees du module d'expedition
 */



export const shippingMeta = {
  id: 'shipping',
  name: 'Expeditions',
  description: 'Gestion des expeditions, transporteurs, suivi et retours',
  icon: 'Truck',
  route: '/shipping',
  category: 'logistics',
  permissions: ['shipping:read', 'shipping:write', 'shipping:admin'],
  features: [
    'shipments',      // Expeditions
    'carriers',       // Transporteurs
    'rates',          // Tarifs
    'tracking',       // Suivi
    'returns',        // Retours
    'pickup-points',  // Points relais
  ],
  navigation: [
    {
      label: 'Tableau de bord',
      path: '/shipping',
      icon: 'LayoutDashboard',
    },
    {
      label: 'Expeditions',
      path: '/shipping/shipments',
      icon: 'Package',
    },
    {
      label: 'Transporteurs',
      path: '/shipping/carriers',
      icon: 'Truck',
    },
    {
      label: 'Tarifs',
      path: '/shipping/rates',
      icon: 'DollarSign',
    },
    {
      label: 'Retours',
      path: '/shipping/returns',
      icon: 'RotateCcw',
    },
    {
      label: 'Points relais',
      path: '/shipping/pickup-points',
      icon: 'MapPin',
    },
  ],
  stats: [
    { key: 'total_shipments', label: 'Expeditions', icon: 'Package' },
    { key: 'in_transit', label: 'En transit', icon: 'Truck' },
    { key: 'delivered_today', label: 'Livrees', icon: 'CheckCircle' },
    { key: 'pending_returns', label: 'Retours', icon: 'RotateCcw' },
  ],
};

export default shippingMeta;
