/**
 * AZALSCORE - Trial Registration Schemas
 * Validation Zod pour le formulaire d'inscription
 */

import { z } from 'zod';

// Personal Info Schema (Step 1)
export const personalInfoSchema = z.object({
  firstName: z
    .string()
    .min(1, 'Le prenom est requis')
    .max(100, 'Le prenom ne doit pas depasser 100 caracteres'),
  lastName: z
    .string()
    .min(1, 'Le nom est requis')
    .max(100, 'Le nom ne doit pas depasser 100 caracteres'),
  email: z
    .string()
    .min(1, "L'email est requis")
    .email('Veuillez entrer une adresse email valide'),
  phone: z
    .string()
    .max(50, 'Le telephone ne doit pas depasser 50 caracteres')
    .optional()
    .or(z.literal('')),
  mobile: z
    .string()
    .max(50, 'Le portable ne doit pas depasser 50 caracteres')
    .optional()
    .or(z.literal('')),
});

// Company Info Schema (Step 2)
export const companyInfoSchema = z.object({
  companyName: z
    .string()
    .min(1, 'La raison sociale est requise')
    .max(255, 'La raison sociale ne doit pas depasser 255 caracteres'),
  addressLine1: z
    .string()
    .min(1, "L'adresse est requise")
    .max(255, "L'adresse ne doit pas depasser 255 caracteres"),
  addressLine2: z
    .string()
    .max(255, "L'adresse ligne 2 ne doit pas depasser 255 caracteres")
    .optional()
    .or(z.literal('')),
  postalCode: z
    .string()
    .min(1, 'Le code postal est requis')
    .max(20, 'Le code postal ne doit pas depasser 20 caracteres'),
  city: z
    .string()
    .min(1, 'La ville est requise')
    .max(100, 'La ville ne doit pas depasser 100 caracteres'),
  country: z
    .string()
    .length(2, 'Veuillez selectionner un pays'),
  language: z
    .string()
    .min(2, 'Veuillez selectionner une langue'),
  activity: z
    .string()
    .max(255, "L'activite ne doit pas depasser 255 caracteres")
    .optional()
    .or(z.literal('')),
  revenueRange: z
    .string()
    .optional()
    .or(z.literal('')),
  maxUsers: z
    .number()
    .min(1, 'Minimum 1 utilisateur')
    .max(5, 'Maximum 5 utilisateurs en essai gratuit'),
  siret: z
    .string()
    .regex(/^(\d{14})?$/, 'Le SIRET doit contenir exactement 14 chiffres')
    .optional()
    .or(z.literal('')),
});

// Validation Schema (Step 4)
export const validationSchema = z.object({
  cgvAccepted: z
    .boolean()
    .refine((val) => val === true, 'Vous devez accepter les CGV'),
  cguAccepted: z
    .boolean()
    .refine((val) => val === true, 'Vous devez accepter les CGU'),
  captchaToken: z
    .string()
    .min(1, 'Veuillez completer le CAPTCHA'),
});

// Combined schema for full form
export const trialFormSchema = z.object({
  personal: personalInfoSchema,
  company: companyInfoSchema,
  validation: validationSchema,
});

// Type exports
export type PersonalInfoValues = z.infer<typeof personalInfoSchema>;
export type CompanyInfoValues = z.infer<typeof companyInfoSchema>;
export type ValidationValues = z.infer<typeof validationSchema>;
export type TrialFormValues = z.infer<typeof trialFormSchema>;
