/**
 * AZALSCORE Module - HR - Employee Info Tab
 * Onglet informations generales de l'employe
 */

import React from 'react';
import {
  User, Mail, Phone, MapPin, Calendar, Building,
  Briefcase, UserCheck, AlertTriangle, Globe
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Employee } from '../types';
import {
  formatDate, getFullName, getSeniorityFormatted, getAge,
  CONTRACT_TYPE_CONFIG, EMPLOYEE_STATUS_CONFIG,
  isContractExpiringSoon, isOnProbation, isActive
} from '../types';

/**
 * EmployeeInfoTab - Informations generales de l'employe
 */
export const EmployeeInfoTab: React.FC<TabContentProps<Employee>> = ({ data: employee }) => {
  const statusConfig = EMPLOYEE_STATUS_CONFIG[employee.status];
  const contractConfig = CONTRACT_TYPE_CONFIG[employee.contract_type];

  return (
    <div className="azals-std-tab-content">
      {/* Alertes */}
      {(isContractExpiringSoon(employee) || isOnProbation(employee)) && (
        <div className={`azals-alert azals-alert--${isContractExpiringSoon(employee) ? 'warning' : 'info'} mb-4`}>
          <AlertTriangle size={18} />
          <span>
            {isContractExpiringSoon(employee) && `Contrat arrivant a echeance le ${formatDate(employee.contract_end_date!)}. `}
            {isOnProbation(employee) && `Periode d'essai jusqu'au ${formatDate(employee.probation_end_date!)}.`}
          </span>
        </div>
      )}

      <Grid cols={2} gap="lg">
        {/* Informations personnelles */}
        <Card title="Informations personnelles" icon={<User size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Nom complet</label>
              <div className="azals-field__value text-lg font-semibold">{getFullName(employee)}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Matricule</label>
              <div className="azals-field__value font-mono">{employee.employee_number}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Statut</label>
              <div className="azals-field__value">
                <span className={`azals-badge azals-badge--${statusConfig.color}`}>
                  {statusConfig.label}
                </span>
              </div>
            </div>
            {employee.birth_date && (
              <div className="azals-field azals-std-field--secondary">
                <label className="azals-field__label">Date de naissance</label>
                <div className="azals-field__value">
                  {formatDate(employee.birth_date)}
                  {getAge(employee) && <span className="text-muted ml-2">({getAge(employee)} ans)</span>}
                </div>
              </div>
            )}
            {employee.nationality && (
              <div className="azals-field azals-std-field--secondary">
                <label className="azals-field__label">Nationalite</label>
                <div className="azals-field__value">
                  <Globe size={14} className="inline mr-1" />
                  {employee.nationality}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Coordonnees */}
        <Card title="Coordonnees" icon={<Mail size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Email</label>
              <div className="azals-field__value">
                <a href={`mailto:${employee.email}`} className="text-primary hover:underline">
                  <Mail size={14} className="inline mr-1" />
                  {employee.email}
                </a>
              </div>
            </div>
            {employee.phone && (
              <div className="azals-field">
                <label className="azals-field__label">Telephone</label>
                <div className="azals-field__value">
                  <Phone size={14} className="inline mr-1" />
                  {employee.phone}
                </div>
              </div>
            )}
            {employee.mobile && (
              <div className="azals-field">
                <label className="azals-field__label">Mobile</label>
                <div className="azals-field__value">
                  <Phone size={14} className="inline mr-1" />
                  {employee.mobile}
                </div>
              </div>
            )}
            {employee.address && (
              <div className="azals-field azals-std-field--secondary">
                <label className="azals-field__label">Adresse</label>
                <div className="azals-field__value">
                  <MapPin size={14} className="inline mr-1" />
                  {employee.address}
                  {employee.postal_code && employee.city && (
                    <span>, {employee.postal_code} {employee.city}</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Poste et departement */}
        <Card title="Poste et departement" icon={<Briefcase size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Departement</label>
              <div className="azals-field__value">
                <Building size={14} className="inline mr-1" />
                {employee.department_name || '-'}
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Poste</label>
              <div className="azals-field__value font-medium">
                {employee.position_title || '-'}
              </div>
            </div>
            {employee.manager_name && (
              <div className="azals-field">
                <label className="azals-field__label">Responsable</label>
                <div className="azals-field__value">
                  <UserCheck size={14} className="inline mr-1" />
                  {employee.manager_name}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Anciennete */}
        <Card title="Anciennete" icon={<Calendar size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Date d'embauche</label>
              <div className="azals-field__value">{formatDate(employee.hire_date)}</div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Anciennete</label>
              <div className="azals-field__value text-lg font-semibold text-primary">
                {getSeniorityFormatted(employee)}
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Type de contrat</label>
              <div className="azals-field__value">
                <span className={`azals-badge azals-badge--${contractConfig.color}`}>
                  {contractConfig.label}
                </span>
              </div>
            </div>
            {employee.contract_end_date && (
              <div className="azals-field">
                <label className="azals-field__label">Fin de contrat</label>
                <div className={`azals-field__value ${isContractExpiringSoon(employee) ? 'text-warning font-semibold' : ''}`}>
                  {formatDate(employee.contract_end_date)}
                </div>
              </div>
            )}
          </div>
        </Card>
      </Grid>

      {/* Contacts d'urgence (ERP only) */}
      {employee.emergency_contacts && employee.emergency_contacts.length > 0 && (
        <Card title="Contacts d'urgence" icon={<Phone size={18} />} className="mt-4 azals-std-field--secondary">
          <div className="azals-contacts-list">
            {employee.emergency_contacts.map((contact, index) => (
              <div key={contact.id || index} className="azals-contact-item">
                <div className="azals-contact-item__info">
                  <span className="font-medium">{contact.name}</span>
                  <span className="text-muted ml-2">({contact.relationship})</span>
                </div>
                <div className="azals-contact-item__phone">
                  <Phone size={14} className="mr-1" />
                  {contact.phone}
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Notes */}
      {employee.notes && (
        <Card title="Notes" className="mt-4 azals-std-field--secondary">
          <div className="azals-field__value azals-field__value--multiline">
            {employee.notes}
          </div>
        </Card>
      )}
    </div>
  );
};

export default EmployeeInfoTab;
