/**
 * AZALSCORE Module - HR - Employee History Tab
 * Onglet historique de l'employe
 */

import React from 'react';
import {
  Clock, User, Edit, FileText, ArrowRight,
  Briefcase, Calendar, Euro, CheckCircle, XCircle
} from 'lucide-react';
import { Card } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Employee, EmployeeHistoryEntry } from '../types';
import {
  formatDateTime, formatDate, getFullName,
  CONTRACT_TYPE_CONFIG, EMPLOYEE_STATUS_CONFIG
} from '../types';

/**
 * EmployeeHistoryTab - Historique de l'employe
 */
export const EmployeeHistoryTab: React.FC<TabContentProps<Employee>> = ({ data: employee }) => {
  // Generer l'historique combine
  const history = generateHistoryFromEmployee(employee);

  return (
    <div className="azals-std-tab-content">
      {/* Timeline des evenements */}
      <Card title="Historique des evenements" icon={<Clock size={18} />}>
        {history.length > 0 ? (
          <div className="azals-timeline">
            {history.map((entry, index) => (
              <HistoryEntry
                key={entry.id}
                entry={entry}
                isFirst={index === 0}
                isLast={index === history.length - 1}
              />
            ))}
          </div>
        ) : (
          <div className="azals-empty azals-empty--sm">
            <Clock size={32} className="text-muted" />
            <p className="text-muted">Aucun historique disponible</p>
          </div>
        )}
      </Card>

      {/* Journal d'audit detaille (ERP only) */}
      <Card
        title="Journal d'audit detaille"
        icon={<FileText size={18} />}
        className="mt-4 azals-std-field--secondary"
      >
        <table className="azals-table azals-table--simple azals-table--compact">
          <thead>
            <tr>
              <th>Date/Heure</th>
              <th>Action</th>
              <th>Utilisateur</th>
              <th>Details</th>
            </tr>
          </thead>
          <tbody>
            {history.map((entry) => (
              <tr key={entry.id}>
                <td className="text-muted text-sm">{formatDateTime(entry.timestamp)}</td>
                <td>{entry.action}</td>
                <td>{entry.user_name || 'Systeme'}</td>
                <td className="text-muted text-sm">
                  {entry.details || '-'}
                  {entry.old_value && entry.new_value && (
                    <span className="ml-2">
                      <span className="text-danger">{entry.old_value}</span>
                      <ArrowRight size={12} className="mx-1 inline" />
                      <span className="text-success">{entry.new_value}</span>
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
};

/**
 * Composant entree de timeline
 */
interface HistoryEntryProps {
  entry: EmployeeHistoryEntry;
  isFirst: boolean;
  isLast: boolean;
}

const HistoryEntry: React.FC<HistoryEntryProps> = ({ entry, isFirst, isLast }) => {
  const getIcon = () => {
    const action = entry.action.toLowerCase();
    if (action.includes('cree') || action.includes('creation') || action.includes('embauche')) {
      return <CheckCircle size={16} className="text-success" />;
    }
    if (action.includes('contrat')) {
      return <FileText size={16} className="text-blue" />;
    }
    if (action.includes('poste') || action.includes('departement') || action.includes('mutation')) {
      return <Briefcase size={16} className="text-purple" />;
    }
    if (action.includes('salaire') || action.includes('remuneration')) {
      return <Euro size={16} className="text-green" />;
    }
    if (action.includes('conge') || action.includes('absence')) {
      return <Calendar size={16} className="text-orange" />;
    }
    if (action.includes('termine') || action.includes('depart') || action.includes('fin')) {
      return <XCircle size={16} className="text-danger" />;
    }
    if (action.includes('modifie') || action.includes('modification')) {
      return <Edit size={16} className="text-warning" />;
    }
    return <Clock size={16} className="text-muted" />;
  };

  return (
    <div className={`azals-timeline__entry ${isFirst ? 'azals-timeline__entry--first' : ''} ${isLast ? 'azals-timeline__entry--last' : ''}`}>
      <div className="azals-timeline__icon">{getIcon()}</div>
      <div className="azals-timeline__content">
        <div className="azals-timeline__header">
          <span className="azals-timeline__action">{entry.action}</span>
          <span className="azals-timeline__time text-muted">
            {formatDateTime(entry.timestamp)}
          </span>
        </div>
        {entry.user_name && (
          <div className="azals-timeline__user text-sm">
            <User size={12} className="mr-1" />
            {entry.user_name}
          </div>
        )}
        {entry.details && (
          <p className="azals-timeline__details text-muted text-sm mt-1">
            {entry.details}
          </p>
        )}
        {entry.old_value && entry.new_value && (
          <div className="azals-timeline__change text-sm mt-1">
            <span className="text-danger line-through">{entry.old_value}</span>
            <ArrowRight size={12} className="mx-2" />
            <span className="text-success">{entry.new_value}</span>
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Generer l'historique a partir des donnees de l'employe
 */
function generateHistoryFromEmployee(employee: Employee): EmployeeHistoryEntry[] {
  const history: EmployeeHistoryEntry[] = [];

  // Embauche
  history.push({
    id: 'hired',
    timestamp: employee.hire_date,
    action: 'Embauche',
    user_name: employee.created_by,
    details: `Matricule: ${employee.employee_number}, Contrat: ${CONTRACT_TYPE_CONFIG[employee.contract_type].label}`,
  });

  // Debut contrat (si different de l'embauche)
  if (employee.contract_start_date && employee.contract_start_date !== employee.hire_date) {
    history.push({
      id: 'contract-start',
      timestamp: employee.contract_start_date,
      action: 'Debut de contrat',
      details: `Type: ${CONTRACT_TYPE_CONFIG[employee.contract_type].label}`,
    });
  }

  // Fin de periode d'essai
  if (employee.probation_end_date) {
    const probationPassed = new Date(employee.probation_end_date) < new Date();
    if (probationPassed) {
      history.push({
        id: 'probation-end',
        timestamp: employee.probation_end_date,
        action: 'Fin de periode d\'essai',
        details: 'Periode d\'essai validee',
      });
    }
  }

  // Demandes de conges approuvees
  const approvedLeaves = employee.leave_requests?.filter(r => r.status === 'APPROVED') || [];
  approvedLeaves.forEach((leave, index) => {
    if (leave.approved_at) {
      history.push({
        id: `leave-approved-${index}`,
        timestamp: leave.approved_at,
        action: 'Conge approuve',
        user_name: leave.approved_by_name,
        details: `${formatDate(leave.start_date)} - ${formatDate(leave.end_date)} (${leave.days} jours)`,
      });
    }
  });

  // Derniere modification
  if (employee.updated_at && employee.updated_at !== employee.created_at) {
    history.push({
      id: 'updated',
      timestamp: employee.updated_at,
      action: 'Fiche modifiee',
      details: 'Mise a jour des informations',
    });
  }

  // Historique fourni par l'API
  if (employee.history && employee.history.length > 0) {
    history.push(...employee.history);
  }

  // Trier par date decroissante
  return history.sort((a, b) =>
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );
}

export default EmployeeHistoryTab;
