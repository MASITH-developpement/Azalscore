/**
 * AZALSCORE - Step 1: Personal Information
 * Collecte nom, prenom, email, telephone
 */

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowRight, User, Mail, Phone } from 'lucide-react';
import { personalInfoSchema, type PersonalInfoValues } from '../schemas';
import type { PersonalInfo } from '../types';

interface StepPersonalInfoProps {
  data: PersonalInfo;
  onNext: (data: PersonalInfo) => void;
}

export const StepPersonalInfo: React.FC<StepPersonalInfoProps> = ({
  data,
  onNext,
}) => {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PersonalInfoValues>({
    resolver: zodResolver(personalInfoSchema),
    defaultValues: data,
  });

  const onSubmit = (values: PersonalInfoValues) => {
    onNext(values as PersonalInfo);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="trial-form">
      <div className="trial-form-header">
        <h2>Vos informations personnelles</h2>
        <p>Ces informations nous permettront de creer votre compte administrateur.</p>
      </div>

      <div className="trial-form-grid">
        {/* First Name */}
        <div className="trial-form-field">
          <label htmlFor="firstName">
            <User size={16} />
            Prenom <span className="required">*</span>
          </label>
          <input
            id="firstName"
            type="text"
            placeholder="Jean"
            {...register('firstName')}
            className={errors.firstName ? 'error' : ''}
          />
          {errors.firstName && (
            <span className="trial-form-error">{errors.firstName.message}</span>
          )}
        </div>

        {/* Last Name */}
        <div className="trial-form-field">
          <label htmlFor="lastName">
            <User size={16} />
            Nom <span className="required">*</span>
          </label>
          <input
            id="lastName"
            type="text"
            placeholder="Dupont"
            {...register('lastName')}
            className={errors.lastName ? 'error' : ''}
          />
          {errors.lastName && (
            <span className="trial-form-error">{errors.lastName.message}</span>
          )}
        </div>

        {/* Email */}
        <div className="trial-form-field trial-form-field--full">
          <label htmlFor="email">
            <Mail size={16} />
            Email professionnel <span className="required">*</span>
          </label>
          <input
            id="email"
            type="email"
            placeholder="jean.dupont@entreprise.fr"
            {...register('email')}
            className={errors.email ? 'error' : ''}
          />
          {errors.email && (
            <span className="trial-form-error">{errors.email.message}</span>
          )}
        </div>

        {/* Phone */}
        <div className="trial-form-field">
          <label htmlFor="phone">
            <Phone size={16} />
            Telephone fixe
          </label>
          <input
            id="phone"
            type="tel"
            placeholder="01 23 45 67 89"
            {...register('phone')}
            className={errors.phone ? 'error' : ''}
          />
          {errors.phone && (
            <span className="trial-form-error">{errors.phone.message}</span>
          )}
        </div>

        {/* Mobile */}
        <div className="trial-form-field">
          <label htmlFor="mobile">
            <Phone size={16} />
            Telephone portable
          </label>
          <input
            id="mobile"
            type="tel"
            placeholder="06 12 34 56 78"
            {...register('mobile')}
            className={errors.mobile ? 'error' : ''}
          />
          {errors.mobile && (
            <span className="trial-form-error">{errors.mobile.message}</span>
          )}
        </div>
      </div>

      <div className="trial-form-actions">
        <button type="submit" className="trial-btn trial-btn-primary" disabled={isSubmitting}>
          Continuer
          <ArrowRight size={18} />
        </button>
      </div>
    </form>
  );
};

export default StepPersonalInfo;
