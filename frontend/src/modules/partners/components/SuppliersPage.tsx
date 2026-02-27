/**
 * AZALSCORE Module - Partners - SuppliersPage
 * Page liste des fournisseurs (wrapper PartnerList)
 */

import React from 'react';
import { PartnerList } from './PartnerList';

export const SuppliersPage: React.FC = () => (
  <PartnerList type="supplier" title="Fournisseurs" />
);

export default SuppliersPage;
