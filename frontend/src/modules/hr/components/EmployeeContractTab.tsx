/**
 * AZALSCORE Module - HR - Employee Contract Tab
 * Onglet contrat et remuneration de l'employe
 */

import React from 'react';
import {
  FileText, Euro, Calendar, CreditCard, Building,
  AlertTriangle, CheckCircle, Clock
} from 'lucide-react';
import { Card, Grid } from '@ui/layout';
import type { TabContentProps } from '@ui/standards';
import type { Employee } from '../types';
import {
  CONTRACT_TYPE_CONFIG,
  isFixedTerm, isContractExpiringSoon, isOnProbation
} from '../types';
import { formatDate, formatCurrency } from '@/utils/formatters';

/**
 * EmployeeContractTab - Contrat et remuneration
 */
export const EmployeeContractTab: React.FC<TabContentProps<Employee>> = ({ data: employee }) => {
  const contractConfig = CONTRACT_TYPE_CONFIG[employee.contract_type];

  return (
    <div className="azals-std-tab-content">
      <Grid cols={2} gap="lg">
        {/* Informations contrat */}
        <Card title="Contrat de travail" icon={<FileText size={18} />}>
          <div className="azals-field-group">
            <div className="azals-field">
              <label className="azals-field__label">Type de contrat</label>
              <div className="azals-field__value">
                <span className={`azals-badge azals-badge--${contractConfig.color}`}>
                  {contractConfig.label}
                </span>
                <span className="text-muted text-sm ml-2">{contractConfig.description}</span>
              </div>
            </div>
            <div className="azals-field">
              <label className="azals-field__label">Date de debut</label>
              <div className="azals-field__value">
                {formatDate(employee.contract_start_date || employee.hire_date)}
              </div>
            </div>
            {isFixedTerm(employee) && employee.contract_end_date && (
              <div className="azals-field">
                <label className="azals-field__label">Date de fin</label>
                <div className={`azals-field__value ${isContractExpiringSoon(employee) ? 'text-warning font-semibold' : ''}`}>
                  {formatDate(employee.contract_end_date)}
                  {isContractExpiringSoon(employee) && (
                    <AlertTriangle size={14} className="ml-1 inline text-warning" />
                  )}
                </div>
              </div>
            )}
            {employee.probation_end_date && (
              <div className="azals-field">
                <label className="azals-field__label">Fin de periode d'essai</label>
                <div className="azals-field__value">
                  {formatDate(employee.probation_end_date)}
                  {isOnProbation(employee) ? (
                    <span className="azals-badge azals-badge--orange azals-badge--sm ml-2">En cours</span>
                  ) : (
                    <span className="azals-badge azals-badge--green azals-badge--sm ml-2">Validee</span>
                  )}
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Remuneration */}
        <Card title="Remuneration" icon={<Euro size={18} />}>
          <div className="azals-field-group">
            {employee.salary !== undefined && (
              <div className="azals-field">
                <label className="azals-field__label">Salaire mensuel brut</label>
                <div className="azals-field__value text-xl font-semibold text-primary">
                  {formatCurrency(employee.salary)}
                </div>
              </div>
            )}
            {employee.salary !== undefined && (
              <div className="azals-field azals-std-field--secondary">
                <label className="azals-field__label">Salaire annuel brut</label>
                <div className="azals-field__value">
                  {formatCurrency(employee.salary * 12)}
                </div>
              </div>
            )}
            {!employee.salary && (
              <div className="azals-empty azals-empty--sm">
                <Euro size={32} className="text-muted" />
                <p className="text-muted">Salaire non renseigne</p>
              </div>
            )}
          </div>
        </Card>

        {/* Dates cles */}
        <Card title="Dates cles" icon={<Calendar size={18} />}>
          <div className="azals-timeline azals-timeline--compact">
            <div className="azals-timeline__entry">
              <div className="azals-timeline__icon">
                <CheckCircle size={16} className="text-success" />
              </div>
              <div className="azals-timeline__content">
                <span className="font-medium">Embauche</span>
                <span className="text-muted ml-2">{formatDate(employee.hire_date)}</span>
              </div>
            </div>
            {employee.contract_start_date && employee.contract_start_date !== employee.hire_date && (
              <div className="azals-timeline__entry">
                <div className="azals-timeline__icon">
                  <FileText size={16} className="text-blue" />
                </div>
                <div className="azals-timeline__content">
                  <span className="font-medium">Debut contrat actuel</span>
                  <span className="text-muted ml-2">{formatDate(employee.contract_start_date)}</span>
                </div>
              </div>
            )}
            {employee.probation_end_date && (
              <div className="azals-timeline__entry">
                <div className="azals-timeline__icon">
                  <Clock size={16} className={isOnProbation(employee) ? 'text-orange' : 'text-success'} />
                </div>
                <div className="azals-timeline__content">
                  <span className="font-medium">Fin periode d'essai</span>
                  <span className="text-muted ml-2">{formatDate(employee.probation_end_date)}</span>
                </div>
              </div>
            )}
            {employee.seniority_date && employee.seniority_date !== employee.hire_date && (
              <div className="azals-timeline__entry azals-std-field--secondary">
                <div className="azals-timeline__icon">
                  <Calendar size={16} className="text-purple" />
                </div>
                <div className="azals-timeline__content">
                  <span className="font-medium">Date d'anciennete</span>
                  <span className="text-muted ml-2">{formatDate(employee.seniority_date)}</span>
                </div>
              </div>
            )}
            {employee.contract_end_date && (
              <div className="azals-timeline__entry">
                <div className="azals-timeline__icon">
                  <AlertTriangle size={16} className={isContractExpiringSoon(employee) ? 'text-warning' : 'text-muted'} />
                </div>
                <div className="azals-timeline__content">
                  <span className="font-medium">Fin de contrat</span>
                  <span className={`ml-2 ${isContractExpiringSoon(employee) ? 'text-warning font-semibold' : 'text-muted'}`}>
                    {formatDate(employee.contract_end_date)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </Card>

        {/* Coordonnees bancaires (ERP only) */}
        <Card title="Coordonnees bancaires" icon={<CreditCard size={18} />} className="azals-std-field--secondary">
          <div className="azals-field-group">
            {employee.bank_name && (
              <div className="azals-field">
                <label className="azals-field__label">Banque</label>
                <div className="azals-field__value">
                  <Building size={14} className="inline mr-1" />
                  {employee.bank_name}
                </div>
              </div>
            )}
            {employee.bank_iban && (
              <div className="azals-field">
                <label className="azals-field__label">IBAN</label>
                <div className="azals-field__value font-mono">{employee.bank_iban}</div>
              </div>
            )}
            {employee.bank_bic && (
              <div className="azals-field">
                <label className="azals-field__label">BIC</label>
                <div className="azals-field__value font-mono">{employee.bank_bic}</div>
              </div>
            )}
            {!employee.bank_iban && (
              <div className="azals-empty azals-empty--sm">
                <CreditCard size={32} className="text-muted" />
                <p className="text-muted">Coordonnees bancaires non renseignees</p>
              </div>
            )}
          </div>
        </Card>
      </Grid>

      {/* Informations administratives (ERP only) */}
      <Card title="Informations administratives" icon={<FileText size={18} />} className="mt-4 azals-std-field--secondary">
        <Grid cols={3} gap="md">
          {employee.social_security_number && (
            <div className="azals-field">
              <label className="azals-field__label">N Securite sociale</label>
              <div className="azals-field__value font-mono">{employee.social_security_number}</div>
            </div>
          )}
          {employee.birth_place && (
            <div className="azals-field">
              <label className="azals-field__label">Lieu de naissance</label>
              <div className="azals-field__value">{employee.birth_place}</div>
            </div>
          )}
          {employee.nationality && (
            <div className="azals-field">
              <label className="azals-field__label">Nationalite</label>
              <div className="azals-field__value">{employee.nationality}</div>
            </div>
          )}
        </Grid>
      </Card>
    </div>
  );
};

export default EmployeeContractTab;
