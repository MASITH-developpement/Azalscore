/**
 * AZALS MODULE - Réseaux Sociaux - Formulaires par plateforme
 * ===========================================================
 */

import React from 'react';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { Input, Select, TextArea } from '@ui/forms';
import type {
  GoogleAnalyticsInput,
  GoogleAdsInput,
  GoogleSearchConsoleInput,
  GoogleMyBusinessInput,
  MetaBusinessInput,
  LinkedInInput,
  SolocalInput
} from '../types';

// === Schémas de validation Zod ===

const googleAnalyticsSchema = z.object({
  metrics_date: z.string().min(1, 'Date requise'),
  sessions: z.coerce.number().min(0),
  users: z.coerce.number().min(0),
  pageviews: z.coerce.number().min(0),
  bounce_rate: z.coerce.number().min(0).max(100),
  avg_session_duration: z.coerce.number().min(0),
  conversions: z.coerce.number().min(0),
  conversion_rate: z.coerce.number().min(0).max(100),
  notes: z.string().optional(),
});

const googleAdsSchema = z.object({
  metrics_date: z.string().min(1, 'Date requise'),
  impressions: z.coerce.number().min(0),
  clicks: z.coerce.number().min(0),
  cost: z.coerce.number().min(0),
  conversions: z.coerce.number().min(0),
  ctr: z.coerce.number().min(0).max(100),
  cpc: z.coerce.number().min(0),
  roas: z.coerce.number().min(0),
  notes: z.string().optional(),
});

const searchConsoleSchema = z.object({
  metrics_date: z.string().min(1, 'Date requise'),
  impressions: z.coerce.number().min(0),
  clicks: z.coerce.number().min(0),
  ctr: z.coerce.number().min(0).max(100),
  avg_position: z.coerce.number().min(0),
  notes: z.string().optional(),
});

const gmbSchema = z.object({
  metrics_date: z.string().min(1, 'Date requise'),
  views: z.coerce.number().min(0),
  clicks: z.coerce.number().min(0),
  calls: z.coerce.number().min(0),
  directions: z.coerce.number().min(0),
  reviews_count: z.coerce.number().min(0),
  rating: z.coerce.number().min(0).max(5),
  notes: z.string().optional(),
});

const metaSchema = z.object({
  metrics_date: z.string().min(1, 'Date requise'),
  platform: z.enum(['meta_facebook', 'meta_instagram']),
  reach: z.coerce.number().min(0),
  impressions: z.coerce.number().min(0),
  engagement: z.coerce.number().min(0),
  clicks: z.coerce.number().min(0),
  followers: z.coerce.number().min(0),
  cost: z.coerce.number().min(0),
  ctr: z.coerce.number().min(0).max(100),
  cpm: z.coerce.number().min(0),
  notes: z.string().optional(),
});

const linkedinSchema = z.object({
  metrics_date: z.string().min(1, 'Date requise'),
  followers: z.coerce.number().min(0),
  impressions: z.coerce.number().min(0),
  clicks: z.coerce.number().min(0),
  engagement: z.coerce.number().min(0),
  engagement_rate: z.coerce.number().min(0).max(100),
  reach: z.coerce.number().min(0),
  notes: z.string().optional(),
});

const solocalSchema = z.object({
  metrics_date: z.string().min(1, 'Date requise'),
  impressions: z.coerce.number().min(0),
  clicks: z.coerce.number().min(0),
  calls: z.coerce.number().min(0),
  directions: z.coerce.number().min(0),
  reviews_count: z.coerce.number().min(0),
  rating: z.coerce.number().min(0).max(5),
  notes: z.string().optional(),
});

// === Composants de formulaire ===

interface FormProps<T> {
  onSubmit: (data: T) => void;
  isLoading?: boolean;
  defaultDate?: string;
}

const today = () => new Date().toISOString().split('T')[0];

const FormActions: React.FC<{ isLoading?: boolean; onCancel?: () => void }> = ({ isLoading, onCancel }) => (
  <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-200">
    {onCancel && (
      <button
        type="button"
        onClick={onCancel}
        className="px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
      >
        Annuler
      </button>
    )}
    <button
      type="submit"
      disabled={isLoading}
      className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
    >
      {isLoading ? (
        <>
          <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
          Enregistrement...
        </>
      ) : (
        'Enregistrer'
      )}
    </button>
  </div>
);

const FormField: React.FC<{
  label: string;
  name: string;
  type?: string;
  placeholder?: string;
  helpText?: string;
  register: any;
  error?: string;
  className?: string;
}> = ({ label, name, type = 'text', placeholder, helpText, register, error, className = '' }) => (
  <div className={className}>
    <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
    <input
      type={type}
      {...register(name)}
      placeholder={placeholder}
      className={`w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors ${
        error ? 'border-red-500' : 'border-gray-300'
      }`}
    />
    {helpText && <p className="text-xs text-gray-500 mt-1">{helpText}</p>}
    {error && <p className="text-xs text-red-500 mt-1">{error}</p>}
  </div>
);

// === Google Analytics Form ===
export const GoogleAnalyticsForm: React.FC<FormProps<GoogleAnalyticsInput>> = ({
  onSubmit,
  isLoading,
  defaultDate
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<GoogleAnalyticsInput>({
    resolver: zodResolver(googleAnalyticsSchema),
    defaultValues: {
      metrics_date: defaultDate || today(),
      sessions: 0,
      users: 0,
      pageviews: 0,
      bounce_rate: 0,
      avg_session_duration: 0,
      conversions: 0,
      conversion_rate: 0,
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField
          label="Date"
          name="metrics_date"
          type="date"
          register={register}
          error={errors.metrics_date?.message}
          className="col-span-2"
        />
        <FormField
          label="Sessions"
          name="sessions"
          type="number"
          register={register}
          error={errors.sessions?.message}
        />
        <FormField
          label="Utilisateurs"
          name="users"
          type="number"
          register={register}
          error={errors.users?.message}
        />
        <FormField
          label="Pages vues"
          name="pageviews"
          type="number"
          register={register}
          error={errors.pageviews?.message}
        />
        <FormField
          label="Taux de rebond (%)"
          name="bounce_rate"
          type="number"
          register={register}
          error={errors.bounce_rate?.message}
          helpText="Entre 0 et 100"
        />
        <FormField
          label="Durée moyenne session (s)"
          name="avg_session_duration"
          type="number"
          register={register}
          error={errors.avg_session_duration?.message}
        />
        <FormField
          label="Conversions"
          name="conversions"
          type="number"
          register={register}
          error={errors.conversions?.message}
        />
        <FormField
          label="Taux de conversion (%)"
          name="conversion_rate"
          type="number"
          register={register}
          error={errors.conversion_rate?.message}
          className="col-span-2"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          {...register('notes')}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          placeholder="Notes optionnelles..."
        />
      </div>
      <FormActions isLoading={isLoading} />
    </form>
  );
};

// === Google Ads Form ===
export const GoogleAdsForm: React.FC<FormProps<GoogleAdsInput>> = ({
  onSubmit,
  isLoading,
  defaultDate
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<GoogleAdsInput>({
    resolver: zodResolver(googleAdsSchema),
    defaultValues: {
      metrics_date: defaultDate || today(),
      impressions: 0,
      clicks: 0,
      cost: 0,
      conversions: 0,
      ctr: 0,
      cpc: 0,
      roas: 0,
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField
          label="Date"
          name="metrics_date"
          type="date"
          register={register}
          error={errors.metrics_date?.message}
          className="col-span-2"
        />
        <FormField
          label="Impressions"
          name="impressions"
          type="number"
          register={register}
          error={errors.impressions?.message}
        />
        <FormField
          label="Clics"
          name="clicks"
          type="number"
          register={register}
          error={errors.clicks?.message}
        />
        <FormField
          label="Coût (€)"
          name="cost"
          type="number"
          register={register}
          error={errors.cost?.message}
        />
        <FormField
          label="Conversions"
          name="conversions"
          type="number"
          register={register}
          error={errors.conversions?.message}
        />
        <FormField
          label="CTR (%)"
          name="ctr"
          type="number"
          register={register}
          error={errors.ctr?.message}
        />
        <FormField
          label="CPC moyen (€)"
          name="cpc"
          type="number"
          register={register}
          error={errors.cpc?.message}
        />
        <FormField
          label="ROAS"
          name="roas"
          type="number"
          register={register}
          error={errors.roas?.message}
          helpText="Return On Ad Spend"
          className="col-span-2"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          {...register('notes')}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <FormActions isLoading={isLoading} />
    </form>
  );
};

// === Search Console Form ===
export const SearchConsoleForm: React.FC<FormProps<GoogleSearchConsoleInput>> = ({
  onSubmit,
  isLoading,
  defaultDate
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<GoogleSearchConsoleInput>({
    resolver: zodResolver(searchConsoleSchema),
    defaultValues: {
      metrics_date: defaultDate || today(),
      impressions: 0,
      clicks: 0,
      ctr: 0,
      avg_position: 0,
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField
          label="Date"
          name="metrics_date"
          type="date"
          register={register}
          error={errors.metrics_date?.message}
          className="col-span-2"
        />
        <FormField
          label="Impressions"
          name="impressions"
          type="number"
          register={register}
          error={errors.impressions?.message}
        />
        <FormField
          label="Clics"
          name="clicks"
          type="number"
          register={register}
          error={errors.clicks?.message}
        />
        <FormField
          label="CTR (%)"
          name="ctr"
          type="number"
          register={register}
          error={errors.ctr?.message}
        />
        <FormField
          label="Position moyenne"
          name="avg_position"
          type="number"
          register={register}
          error={errors.avg_position?.message}
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          {...register('notes')}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <FormActions isLoading={isLoading} />
    </form>
  );
};

// === Google My Business Form ===
export const GoogleMyBusinessForm: React.FC<FormProps<GoogleMyBusinessInput>> = ({
  onSubmit,
  isLoading,
  defaultDate
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<GoogleMyBusinessInput>({
    resolver: zodResolver(gmbSchema),
    defaultValues: {
      metrics_date: defaultDate || today(),
      views: 0,
      clicks: 0,
      calls: 0,
      directions: 0,
      reviews_count: 0,
      rating: 0,
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField
          label="Date"
          name="metrics_date"
          type="date"
          register={register}
          error={errors.metrics_date?.message}
          className="col-span-2"
        />
        <FormField
          label="Vues de la fiche"
          name="views"
          type="number"
          register={register}
          error={errors.views?.message}
        />
        <FormField
          label="Clics vers le site"
          name="clicks"
          type="number"
          register={register}
          error={errors.clicks?.message}
        />
        <FormField
          label="Appels"
          name="calls"
          type="number"
          register={register}
          error={errors.calls?.message}
        />
        <FormField
          label="Itinéraires"
          name="directions"
          type="number"
          register={register}
          error={errors.directions?.message}
        />
        <FormField
          label="Nombre d'avis"
          name="reviews_count"
          type="number"
          register={register}
          error={errors.reviews_count?.message}
        />
        <FormField
          label="Note moyenne (sur 5)"
          name="rating"
          type="number"
          register={register}
          error={errors.rating?.message}
          helpText="Entre 0 et 5"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          {...register('notes')}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <FormActions isLoading={isLoading} />
    </form>
  );
};

// === Meta Business Form ===
export const MetaBusinessForm: React.FC<FormProps<MetaBusinessInput> & { defaultPlatform?: 'meta_facebook' | 'meta_instagram' }> = ({
  onSubmit,
  isLoading,
  defaultDate,
  defaultPlatform = 'meta_facebook'
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<MetaBusinessInput>({
    resolver: zodResolver(metaSchema),
    defaultValues: {
      metrics_date: defaultDate || today(),
      platform: defaultPlatform,
      reach: 0,
      impressions: 0,
      engagement: 0,
      clicks: 0,
      followers: 0,
      cost: 0,
      ctr: 0,
      cpm: 0,
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField
          label="Date"
          name="metrics_date"
          type="date"
          register={register}
          error={errors.metrics_date?.message}
        />
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Plateforme</label>
          <select
            {...register('platform')}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          >
            <option value="meta_facebook">Facebook</option>
            <option value="meta_instagram">Instagram</option>
          </select>
        </div>
        <FormField
          label="Portée"
          name="reach"
          type="number"
          register={register}
          error={errors.reach?.message}
        />
        <FormField
          label="Impressions"
          name="impressions"
          type="number"
          register={register}
          error={errors.impressions?.message}
        />
        <FormField
          label="Engagements"
          name="engagement"
          type="number"
          register={register}
          error={errors.engagement?.message}
        />
        <FormField
          label="Clics"
          name="clicks"
          type="number"
          register={register}
          error={errors.clicks?.message}
        />
        <FormField
          label="Abonnés"
          name="followers"
          type="number"
          register={register}
          error={errors.followers?.message}
        />
        <FormField
          label="Budget pub (€)"
          name="cost"
          type="number"
          register={register}
          error={errors.cost?.message}
        />
        <FormField
          label="CTR (%)"
          name="ctr"
          type="number"
          register={register}
          error={errors.ctr?.message}
        />
        <FormField
          label="CPM (€)"
          name="cpm"
          type="number"
          register={register}
          error={errors.cpm?.message}
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          {...register('notes')}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <FormActions isLoading={isLoading} />
    </form>
  );
};

// === LinkedIn Form ===
export const LinkedInForm: React.FC<FormProps<LinkedInInput>> = ({
  onSubmit,
  isLoading,
  defaultDate
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<LinkedInInput>({
    resolver: zodResolver(linkedinSchema),
    defaultValues: {
      metrics_date: defaultDate || today(),
      followers: 0,
      impressions: 0,
      clicks: 0,
      engagement: 0,
      engagement_rate: 0,
      reach: 0,
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField
          label="Date"
          name="metrics_date"
          type="date"
          register={register}
          error={errors.metrics_date?.message}
          className="col-span-2"
        />
        <FormField
          label="Abonnés"
          name="followers"
          type="number"
          register={register}
          error={errors.followers?.message}
        />
        <FormField
          label="Impressions"
          name="impressions"
          type="number"
          register={register}
          error={errors.impressions?.message}
        />
        <FormField
          label="Clics"
          name="clicks"
          type="number"
          register={register}
          error={errors.clicks?.message}
        />
        <FormField
          label="Engagements"
          name="engagement"
          type="number"
          register={register}
          error={errors.engagement?.message}
        />
        <FormField
          label="Taux d'engagement (%)"
          name="engagement_rate"
          type="number"
          register={register}
          error={errors.engagement_rate?.message}
        />
        <FormField
          label="Visiteurs uniques"
          name="reach"
          type="number"
          register={register}
          error={errors.reach?.message}
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          {...register('notes')}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <FormActions isLoading={isLoading} />
    </form>
  );
};

// === Solocal Form ===
export const SolocalForm: React.FC<FormProps<SolocalInput>> = ({
  onSubmit,
  isLoading,
  defaultDate
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<SolocalInput>({
    resolver: zodResolver(solocalSchema),
    defaultValues: {
      metrics_date: defaultDate || today(),
      impressions: 0,
      clicks: 0,
      calls: 0,
      directions: 0,
      reviews_count: 0,
      rating: 0,
    }
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <FormField
          label="Date"
          name="metrics_date"
          type="date"
          register={register}
          error={errors.metrics_date?.message}
          className="col-span-2"
        />
        <FormField
          label="Vues de la fiche"
          name="impressions"
          type="number"
          register={register}
          error={errors.impressions?.message}
        />
        <FormField
          label="Clics vers le site"
          name="clicks"
          type="number"
          register={register}
          error={errors.clicks?.message}
        />
        <FormField
          label="Appels"
          name="calls"
          type="number"
          register={register}
          error={errors.calls?.message}
        />
        <FormField
          label="Itinéraires"
          name="directions"
          type="number"
          register={register}
          error={errors.directions?.message}
        />
        <FormField
          label="Nombre d'avis"
          name="reviews_count"
          type="number"
          register={register}
          error={errors.reviews_count?.message}
        />
        <FormField
          label="Note (sur 5)"
          name="rating"
          type="number"
          register={register}
          error={errors.rating?.message}
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
        <textarea
          {...register('notes')}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
        />
      </div>
      <FormActions isLoading={isLoading} />
    </form>
  );
};

export default {
  GoogleAnalyticsForm,
  GoogleAdsForm,
  SearchConsoleForm,
  GoogleMyBusinessForm,
  MetaBusinessForm,
  LinkedInForm,
  SolocalForm,
};
