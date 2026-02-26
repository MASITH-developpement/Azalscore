/**
 * AZALSCORE Module - HR - EmployeeDetailView
 * Vue de detail d'un employe avec BaseViewStandard
 */

import React from 'react';
import {
  User, FileText, Calendar, History, Sparkles, ArrowLeft, Edit,
  Building, Briefcase, Clock
} from 'lucide-react';
import { Button } from '@ui/actions';
import { BaseViewStandard } from '@ui/standards';
import { formatDate, formatCurrency } from '@/utils/formatters';
import type { TabDefinition, InfoBarItem, SidebarSection, ActionDefinition, SemanticColor } from '@ui/standards';
import type { Employee } from '../types';
import {
  getFullName, getSeniorityFormatted,
  CONTRACT_TYPE_CONFIG, EMPLOYEE_STATUS_CONFIG,
  getRemainingLeave, getTotalRemainingLeave
} from '../types';
import { useEmployee } from '../hooks';
import {
  EmployeeInfoTab, EmployeeContractTab, EmployeeLeavesTab,
  EmployeeDocsTab, EmployeeHistoryTab, EmployeeIATab
} from './index';

interface EmployeeDetailViewProps {
  employeeId: string;
  onBack: () => void;
  onEdit?: () => void;
}

const EmployeeDetailView: React.FC<EmployeeDetailViewProps> = ({ employeeId, onBack, onEdit }) => {
  const { data: employee, isLoading, error, refetch } = useEmployee(employeeId);

  if (isLoading) {
    return (
      <div className="azals-loading">
        <div className="azals-loading__spinner" />
        <p>Chargement du dossier employe...</p>
      </div>
    );
  }

  if (error || !employee) {
    return (
      <div className="azals-error">
        <p>Erreur lors du chargement du dossier.</p>
        <Button onClick={onBack} leftIcon={<ArrowLeft size={16} />}>Retour</Button>
      </div>
    );
  }

  // Configuration des onglets
  const tabs: TabDefinition<Employee>[] = [
    { id: 'info', label: 'Informations', icon: <User size={16} />, component: EmployeeInfoTab },
    { id: 'contract', label: 'Contrat', icon: <FileText size={16} />, component: EmployeeContractTab },
    { id: 'leaves', label: 'Conges', icon: <Calendar size={16} />, badge: employee.leave_requests?.filter(r => r.status === 'PENDING').length, component: EmployeeLeavesTab },
    { id: 'docs', label: 'Documents', icon: <FileText size={16} />, badge: employee.documents?.length, component: EmployeeDocsTab },
    { id: 'history', label: 'Historique', icon: <History size={16} />, component: EmployeeHistoryTab },
    { id: 'ia', label: 'Assistant IA', icon: <Sparkles size={16} />, component: EmployeeIATab }
  ];

  // Configuration InfoBar
  const statusConfig = EMPLOYEE_STATUS_CONFIG[employee.status];
  const contractConfig = CONTRACT_TYPE_CONFIG[employee.contract_type];

  const infoBarItems: InfoBarItem[] = [
    {
      id: 'department',
      label: 'Departement',
      value: employee.department_name || '-',
      icon: <Building size={16} />
    },
    {
      id: 'position',
      label: 'Poste',
      value: employee.position_title || '-',
      icon: <Briefcase size={16} />
    },
    {
      id: 'seniority',
      label: 'Anciennete',
      value: getSeniorityFormatted(employee),
      icon: <Clock size={16} />
    },
    {
      id: 'leave-balance',
      label: 'Conges restants',
      value: `${getTotalRemainingLeave(employee)}j`,
      valueColor: getTotalRemainingLeave(employee) > 20 ? 'orange' : 'green'
    }
  ];

  // Configuration Sidebar
  const sidebarSections: SidebarSection[] = [
    {
      id: 'status',
      title: 'Statut',
      items: [
        { id: 'status', label: 'Statut', value: statusConfig.label },
        { id: 'contract', label: 'Contrat', value: contractConfig.label },
        { id: 'hire-date', label: 'Embauche', value: formatDate(employee.hire_date) }
      ]
    },
    {
      id: 'leaves',
      title: 'Conges',
      items: [
        { id: 'cp', label: 'CP restants', value: `${getRemainingLeave(employee, 'PAID')}j`, highlight: getRemainingLeave(employee, 'PAID') > 20 },
        { id: 'total', label: 'Total restant', value: `${getTotalRemainingLeave(employee)}j` }
      ]
    },
    {
      id: 'salary',
      title: 'Remuneration',
      items: [
        { id: 'salary', label: 'Salaire mensuel', value: employee.salary ? formatCurrency(employee.salary) : '-', format: 'currency' }
      ]
    }
  ];

  // Actions header
  const headerActions: ActionDefinition[] = [
    { id: 'back', label: 'Retour', icon: <ArrowLeft size={16} />, variant: 'ghost', onClick: onBack },
    ...(onEdit ? [{ id: 'edit', label: 'Modifier', icon: <Edit size={16} />, variant: 'secondary' as const, onClick: onEdit }] : [])
  ];

  // Actions primaires
  const primaryActions: ActionDefinition[] = [
    {
      id: 'new-leave',
      label: 'Demande de conge',
      icon: <Calendar size={16} />,
      variant: 'secondary'
    }
  ];

  // Mapping couleurs
  const statusColorMap: Record<string, SemanticColor> = {
    gray: 'gray',
    blue: 'blue',
    orange: 'orange',
    green: 'green',
    red: 'red'
  };

  return (
    <BaseViewStandard<Employee>
      title={getFullName(employee)}
      subtitle={`${employee.employee_number} - ${employee.position_title || 'N/A'}`}
      status={{
        label: statusConfig.label,
        color: statusColorMap[statusConfig.color] || 'gray'
      }}
      data={employee}
      view="detail"
      tabs={tabs}
      infoBarItems={infoBarItems}
      sidebarSections={sidebarSections}
      headerActions={headerActions}
      primaryActions={primaryActions}
      error={error ? (error as Error) : null}
      onRetry={() => refetch()}
    />
  );
};

export default EmployeeDetailView;
