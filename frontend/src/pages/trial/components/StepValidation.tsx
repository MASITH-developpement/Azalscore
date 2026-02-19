/**
 * AZALSCORE - Step 4: Validation
 * Acceptation CGV/CGU + CAPTCHA hCaptcha
 */

import React, { useCallback, useState } from 'react';
import HCaptcha from '@hcaptcha/react-hcaptcha';
import { zodResolver } from '@hookform/resolvers/zod';
import { ArrowRight, ArrowLeft, FileText, AlertCircle, Loader2 } from 'lucide-react';
import { useForm, Controller } from 'react-hook-form';
import { Link } from 'react-router-dom';
import { useCreateRegistration } from '../api';
import { validationSchema, type ValidationValues } from '../schemas';
import type { ValidationInfo, TrialFormData, TrialRegistrationRequest } from '../types';

// hCaptcha site key from environment
const HCAPTCHA_SITE_KEY = import.meta.env.VITE_HCAPTCHA_SITE_KEY || '10000000-ffff-ffff-ffff-000000000001';

interface StepValidationProps {
  data: ValidationInfo;
  formData: TrialFormData;
  onNext: (registrationId: string) => void;
  onBack: () => void;
}

export const StepValidation: React.FC<StepValidationProps> = ({
  data,
  formData,
  onNext,
  onBack,
}) => {
  const [captchaRef, setCaptchaRef] = useState<HCaptcha | null>(null);
  const createRegistration = useCreateRegistration();

  const {
    control,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<ValidationValues>({
    resolver: zodResolver(validationSchema),
    defaultValues: data,
  });

  const onCaptchaVerify = useCallback(
    (token: string) => {
      setValue('captchaToken', token, { shouldValidate: true });
    },
    [setValue]
  );

  const onCaptchaExpire = useCallback(() => {
    setValue('captchaToken', '', { shouldValidate: true });
  }, [setValue]);

  const onSubmit = async (values: ValidationValues) => {
    // Build the full registration request
    const request: TrialRegistrationRequest = {
      first_name: formData.personal.firstName,
      last_name: formData.personal.lastName,
      email: formData.personal.email,
      phone: formData.personal.phone || null,
      mobile: formData.personal.mobile || null,
      company_name: formData.company.companyName,
      address_line1: formData.company.addressLine1,
      address_line2: formData.company.addressLine2 || null,
      postal_code: formData.company.postalCode,
      city: formData.company.city,
      country: formData.company.country,
      language: formData.company.language,
      activity: formData.company.activity || null,
      revenue_range: formData.company.revenueRange || null,
      max_users: formData.company.maxUsers,
      siret: formData.company.siret || null,
      selected_plan: formData.pricing.selectedPlan,
      cgv_accepted: values.cgvAccepted,
      cgu_accepted: values.cguAccepted,
      captcha_token: values.captchaToken,
    };

    try {
      const response = await createRegistration.mutateAsync(request);
      onNext(response.registration_id);
    } catch (error) {
      // Reset captcha on error
      captchaRef?.resetCaptcha();
      setValue('captchaToken', '');
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="trial-form">
      <div className="trial-form-header">
        <h2>Validation de votre inscription</h2>
        <p>Veuillez accepter les conditions et verifier que vous n'etes pas un robot.</p>
      </div>

      {/* Error display */}
      {createRegistration.error && (
        <div className="trial-form-error-banner">
          <AlertCircle size={20} />
          <span>{createRegistration.error.message}</span>
        </div>
      )}

      {/* Summary */}
      <div className="trial-validation-summary">
        <h4>Recapitulatif</h4>
        <dl>
          <dt>Nom</dt>
          <dd>{formData.personal.firstName} {formData.personal.lastName}</dd>
          <dt>Email</dt>
          <dd>{formData.personal.email}</dd>
          <dt>Entreprise</dt>
          <dd>{formData.company.companyName}</dd>
          <dt>Adresse</dt>
          <dd>
            {formData.company.addressLine1}, {formData.company.postalCode} {formData.company.city}
          </dd>
        </dl>
      </div>

      {/* CGV Acceptance */}
      <div className="trial-form-field trial-form-field--checkbox">
        <Controller
          name="cgvAccepted"
          control={control}
          render={({ field }) => (
            <label className="trial-checkbox">
              <input
                type="checkbox"
                checked={field.value}
                onChange={(e) => field.onChange(e.target.checked)}
              />
              <span className="trial-checkbox-mark" />
              <span className="trial-checkbox-label">
                <FileText size={14} />
                J'accepte les{' '}
                <Link to="/cgv" target="_blank" rel="noopener noreferrer">
                  Conditions Generales de Vente
                </Link>{' '}
                <span className="required">*</span>
              </span>
            </label>
          )}
        />
        {errors.cgvAccepted && (
          <span className="trial-form-error">{errors.cgvAccepted.message}</span>
        )}
      </div>

      {/* CGU Acceptance */}
      <div className="trial-form-field trial-form-field--checkbox">
        <Controller
          name="cguAccepted"
          control={control}
          render={({ field }) => (
            <label className="trial-checkbox">
              <input
                type="checkbox"
                checked={field.value}
                onChange={(e) => field.onChange(e.target.checked)}
              />
              <span className="trial-checkbox-mark" />
              <span className="trial-checkbox-label">
                <FileText size={14} />
                J'accepte les{' '}
                <Link to="/mentions-legales" target="_blank" rel="noopener noreferrer">
                  Conditions Generales d'Utilisation
                </Link>{' '}
                <span className="required">*</span>
              </span>
            </label>
          )}
        />
        {errors.cguAccepted && (
          <span className="trial-form-error">{errors.cguAccepted.message}</span>
        )}
      </div>

      {/* hCaptcha */}
      <div className="trial-form-field trial-form-field--captcha">
        <label>Verification anti-robot <span className="required">*</span></label>
        <div className="trial-captcha-container">
          <HCaptcha
            ref={(ref) => setCaptchaRef(ref)}
            sitekey={HCAPTCHA_SITE_KEY}
            onVerify={onCaptchaVerify}
            onExpire={onCaptchaExpire}
            languageOverride="fr"
          />
        </div>
        {errors.captchaToken && (
          <span className="trial-form-error">{errors.captchaToken.message}</span>
        )}
      </div>

      <div className="trial-form-actions">
        <button
          type="button"
          className="trial-btn trial-btn-outline"
          onClick={onBack}
          disabled={createRegistration.isPending}
        >
          <ArrowLeft size={18} />
          Retour
        </button>
        <button
          type="submit"
          className="trial-btn trial-btn-primary"
          disabled={createRegistration.isPending}
        >
          {createRegistration.isPending ? (
            <>
              <Loader2 size={18} className="spinning" />
              Envoi en cours...
            </>
          ) : (
            <>
              Valider et continuer
              <ArrowRight size={18} />
            </>
          )}
        </button>
      </div>
    </form>
  );
};

export default StepValidation;
