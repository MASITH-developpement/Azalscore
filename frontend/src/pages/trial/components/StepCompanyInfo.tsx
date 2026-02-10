/**
 * AZALSCORE - Step 2: Company Information
 * Collecte raison sociale, adresse, activite, etc.
 */

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowRight, ArrowLeft, Building2, MapPin, Users } from 'lucide-react';
import { companyInfoSchema, type CompanyInfoValues } from '../schemas';
import type { CompanyInfo } from '../types';
import { COUNTRY_OPTIONS, LANGUAGE_OPTIONS, REVENUE_RANGE_OPTIONS } from '../types';

interface StepCompanyInfoProps {
  data: CompanyInfo;
  onNext: (data: CompanyInfo) => void;
  onBack: () => void;
}

export const StepCompanyInfo: React.FC<StepCompanyInfoProps> = ({
  data,
  onNext,
  onBack,
}) => {
  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CompanyInfoValues>({
    resolver: zodResolver(companyInfoSchema),
    defaultValues: data,
  });

  const maxUsers = watch('maxUsers');

  const onSubmit = (values: CompanyInfoValues) => {
    onNext(values as CompanyInfo);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="trial-form">
      <div className="trial-form-header">
        <h2>Votre entreprise</h2>
        <p>Ces informations seront utilisees pour configurer votre espace de travail.</p>
      </div>

      <div className="trial-form-grid">
        {/* Company Name */}
        <div className="trial-form-field trial-form-field--full">
          <label htmlFor="companyName">
            <Building2 size={16} />
            Raison sociale <span className="required">*</span>
          </label>
          <input
            id="companyName"
            type="text"
            placeholder="Ma Societe SAS"
            {...register('companyName')}
            className={errors.companyName ? 'error' : ''}
          />
          {errors.companyName && (
            <span className="trial-form-error">{errors.companyName.message}</span>
          )}
        </div>

        {/* Address Line 1 */}
        <div className="trial-form-field trial-form-field--full">
          <label htmlFor="addressLine1">
            <MapPin size={16} />
            Adresse <span className="required">*</span>
          </label>
          <input
            id="addressLine1"
            type="text"
            placeholder="123 rue de la Paix"
            {...register('addressLine1')}
            className={errors.addressLine1 ? 'error' : ''}
          />
          {errors.addressLine1 && (
            <span className="trial-form-error">{errors.addressLine1.message}</span>
          )}
        </div>

        {/* Address Line 2 */}
        <div className="trial-form-field trial-form-field--full">
          <label htmlFor="addressLine2">
            Complement d'adresse
          </label>
          <input
            id="addressLine2"
            type="text"
            placeholder="Batiment A, 2eme etage"
            {...register('addressLine2')}
          />
        </div>

        {/* Postal Code */}
        <div className="trial-form-field">
          <label htmlFor="postalCode">
            Code postal <span className="required">*</span>
          </label>
          <input
            id="postalCode"
            type="text"
            placeholder="75001"
            {...register('postalCode')}
            className={errors.postalCode ? 'error' : ''}
          />
          {errors.postalCode && (
            <span className="trial-form-error">{errors.postalCode.message}</span>
          )}
        </div>

        {/* City */}
        <div className="trial-form-field">
          <label htmlFor="city">
            Ville <span className="required">*</span>
          </label>
          <input
            id="city"
            type="text"
            placeholder="Paris"
            {...register('city')}
            className={errors.city ? 'error' : ''}
          />
          {errors.city && (
            <span className="trial-form-error">{errors.city.message}</span>
          )}
        </div>

        {/* Country */}
        <div className="trial-form-field">
          <label htmlFor="country">
            Pays <span className="required">*</span>
          </label>
          <select
            id="country"
            {...register('country')}
            className={errors.country ? 'error' : ''}
          >
            {COUNTRY_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          {errors.country && (
            <span className="trial-form-error">{errors.country.message}</span>
          )}
        </div>

        {/* Language */}
        <div className="trial-form-field">
          <label htmlFor="language">
            Langue <span className="required">*</span>
          </label>
          <select
            id="language"
            {...register('language')}
            className={errors.language ? 'error' : ''}
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Activity */}
        <div className="trial-form-field">
          <label htmlFor="activity">
            Activite
          </label>
          <input
            id="activity"
            type="text"
            placeholder="Commerce, Services, Industrie..."
            {...register('activity')}
          />
        </div>

        {/* Revenue Range */}
        <div className="trial-form-field">
          <label htmlFor="revenueRange">
            Chiffre d'affaires
          </label>
          <select id="revenueRange" {...register('revenueRange')}>
            <option value="">Selectionnez...</option>
            {REVENUE_RANGE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
        </div>

        {/* Max Users */}
        <div className="trial-form-field">
          <label htmlFor="maxUsers">
            <Users size={16} />
            Nombre d'utilisateurs <span className="required">*</span>
          </label>
          <div className="trial-form-slider">
            <input
              id="maxUsers"
              type="range"
              min={1}
              max={5}
              {...register('maxUsers', { valueAsNumber: true })}
            />
            <span className="trial-form-slider-value">{maxUsers} utilisateur(s)</span>
          </div>
          <span className="trial-form-hint">Maximum 5 utilisateurs en essai gratuit</span>
        </div>

        {/* SIRET */}
        <div className="trial-form-field">
          <label htmlFor="siret">
            SIRET
          </label>
          <input
            id="siret"
            type="text"
            placeholder="12345678901234"
            maxLength={14}
            {...register('siret')}
            className={errors.siret ? 'error' : ''}
          />
          {errors.siret && (
            <span className="trial-form-error">{errors.siret.message}</span>
          )}
        </div>
      </div>

      <div className="trial-form-actions">
        <button
          type="button"
          className="trial-btn trial-btn-outline"
          onClick={onBack}
        >
          <ArrowLeft size={18} />
          Retour
        </button>
        <button type="submit" className="trial-btn trial-btn-primary" disabled={isSubmitting}>
          Continuer
          <ArrowRight size={18} />
        </button>
      </div>
    </form>
  );
};

export default StepCompanyInfo;
