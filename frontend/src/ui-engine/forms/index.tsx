/**
 * AZALSCORE UI Engine - Form System
 * Formulaires génériques avec validation côté client
 * La validation métier reste côté backend
 */

import React, { useId } from 'react';
import { useForm, Controller, UseFormReturn, FieldValues, Path, DefaultValues, SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { clsx } from 'clsx';
import { Eye, EyeOff, Calendar, Upload, X } from 'lucide-react';
import type { FormField, SelectOption } from '@/types';

// ============================================================
// TYPES
// ============================================================

interface FormProps<T extends FieldValues> {
  fields: FormField[];
  onSubmit: (data: T) => void | Promise<void>;
  schema?: z.ZodSchema<T>;
  defaultValues?: Partial<T>;
  submitLabel?: string;
  cancelLabel?: string;
  onCancel?: () => void;
  isLoading?: boolean;
  className?: string;
  layout?: 'vertical' | 'horizontal' | 'inline';
}

interface FieldWrapperProps {
  label: string;
  name: string;
  required?: boolean;
  error?: string;
  helpText?: string;
  children: React.ReactNode;
  layout?: 'vertical' | 'horizontal' | 'inline';
}

// ============================================================
// FIELD WRAPPER
// ============================================================

const FieldWrapper: React.FC<FieldWrapperProps> = ({
  label,
  name,
  required,
  error,
  helpText,
  children,
  layout = 'vertical',
}) => {
  const id = useId();

  return (
    <div
      className={clsx('azals-field', `azals-field--${layout}`, {
        'azals-field--error': !!error,
      })}
    >
      <label htmlFor={`${id}-${name}`} className="azals-field__label">
        {label}
        {required && <span className="azals-field__required">*</span>}
      </label>
      <div className="azals-field__control">{children}</div>
      {error && <span className="azals-field__error">{error}</span>}
      {helpText && !error && <span className="azals-field__help">{helpText}</span>}
    </div>
  );
};

// ============================================================
// INPUT COMPONENTS
// ============================================================

// Text Input
interface TextInputProps {
  name: string;
  type?: 'text' | 'email' | 'password' | 'number';
  placeholder?: string;
  disabled?: boolean;
  value: string | number;
  onChange: (value: string | number) => void;
  onBlur?: () => void;
  error?: boolean;
}

const TextInput: React.FC<TextInputProps> = ({
  name,
  type = 'text',
  placeholder,
  disabled,
  value,
  onChange,
  onBlur,
  error,
}) => {
  const [showPassword, setShowPassword] = React.useState(false);
  const inputType = type === 'password' && showPassword ? 'text' : type;

  return (
    <div className="azals-input-wrapper">
      <input
        id={name}
        name={name}
        type={inputType}
        placeholder={placeholder}
        disabled={disabled}
        value={value}
        onChange={(e) =>
          onChange(type === 'number' ? Number(e.target.value) : e.target.value)
        }
        onBlur={onBlur}
        className={clsx('azals-input', {
          'azals-input--error': error,
          'azals-input--password': type === 'password',
        })}
      />
      {type === 'password' && (
        <button
          type="button"
          className="azals-input__toggle"
          onClick={() => setShowPassword(!showPassword)}
          tabIndex={-1}
        >
          {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
        </button>
      )}
    </div>
  );
};

// Select Input
interface SelectInputProps {
  name: string;
  options: SelectOption[];
  placeholder?: string;
  disabled?: boolean;
  value: string | number;
  onChange: (value: string | number) => void;
  onBlur?: () => void;
  error?: boolean;
}

const SelectInput: React.FC<SelectInputProps> = ({
  name,
  options,
  placeholder,
  disabled,
  value,
  onChange,
  onBlur,
  error,
}) => {
  return (
    <select
      id={name}
      name={name}
      disabled={disabled}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onBlur={onBlur}
      className={clsx('azals-select', {
        'azals-select--error': error,
        'azals-select--placeholder': !value,
      })}
    >
      {placeholder && (
        <option value="" disabled>
          {placeholder}
        </option>
      )}
      {options.map((option) => (
        <option key={option.value} value={option.value} disabled={option.disabled}>
          {option.label}
        </option>
      ))}
    </select>
  );
};

// Checkbox Input
interface CheckboxInputProps {
  name: string;
  label?: string;
  disabled?: boolean;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

const CheckboxInput: React.FC<CheckboxInputProps> = ({
  name,
  label,
  disabled,
  checked,
  onChange,
}) => {
  return (
    <label className="azals-checkbox-wrapper">
      <input
        id={name}
        name={name}
        type="checkbox"
        disabled={disabled}
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="azals-checkbox"
      />
      {label && <span className="azals-checkbox__label">{label}</span>}
    </label>
  );
};

// Textarea Input
interface TextareaInputProps {
  name: string;
  placeholder?: string;
  disabled?: boolean;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  error?: boolean;
  rows?: number;
}

const TextareaInput: React.FC<TextareaInputProps> = ({
  name,
  placeholder,
  disabled,
  value,
  onChange,
  onBlur,
  error,
  rows = 4,
}) => {
  return (
    <textarea
      id={name}
      name={name}
      placeholder={placeholder}
      disabled={disabled}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      onBlur={onBlur}
      rows={rows}
      className={clsx('azals-textarea', {
        'azals-textarea--error': error,
      })}
    />
  );
};

// Date Input
interface DateInputProps {
  name: string;
  disabled?: boolean;
  value: string;
  onChange: (value: string) => void;
  onBlur?: () => void;
  error?: boolean;
  min?: string;
  max?: string;
}

const DateInput: React.FC<DateInputProps> = ({
  name,
  disabled,
  value,
  onChange,
  onBlur,
  error,
  min,
  max,
}) => {
  return (
    <div className="azals-input-wrapper">
      <input
        id={name}
        name={name}
        type="date"
        disabled={disabled}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={onBlur}
        min={min}
        max={max}
        className={clsx('azals-input azals-input--date', {
          'azals-input--error': error,
        })}
      />
      <Calendar size={16} className="azals-input__icon" />
    </div>
  );
};

// ============================================================
// DYNAMIC FORM
// ============================================================

export function DynamicForm<T extends FieldValues>({
  fields,
  onSubmit,
  schema,
  defaultValues,
  submitLabel = 'Enregistrer',
  cancelLabel = 'Annuler',
  onCancel,
  isLoading,
  className,
  layout = 'vertical',
}: FormProps<T>) {
  const form = useForm<T>({
    resolver: schema ? zodResolver(schema) : undefined,
    defaultValues: defaultValues as DefaultValues<T>,
  });

  const {
    handleSubmit,
    control,
    formState: { errors },
  } = form;

  const renderField = (field: FormField) => {
    const error = errors[field.name as Path<T>]?.message as string | undefined;

    return (
      <Controller
        key={field.name}
        name={field.name as Path<T>}
        control={control}
        render={({ field: controllerField }) => (
          <FieldWrapper
            label={field.label}
            name={field.name}
            required={field.required}
            error={error}
            helpText={field.helpText}
            layout={layout}
          >
            {field.type === 'text' ||
            field.type === 'email' ||
            field.type === 'password' ||
            field.type === 'number' ? (
              <TextInput
                name={field.name}
                type={field.type}
                placeholder={field.placeholder}
                disabled={field.disabled || isLoading}
                value={controllerField.value ?? ''}
                onChange={controllerField.onChange}
                onBlur={controllerField.onBlur}
                error={!!error}
              />
            ) : field.type === 'select' ? (
              <SelectInput
                name={field.name}
                options={field.options || []}
                placeholder={field.placeholder}
                disabled={field.disabled || isLoading}
                value={controllerField.value ?? ''}
                onChange={controllerField.onChange}
                onBlur={controllerField.onBlur}
                error={!!error}
              />
            ) : field.type === 'checkbox' ? (
              <CheckboxInput
                name={field.name}
                disabled={field.disabled || isLoading}
                checked={controllerField.value ?? false}
                onChange={controllerField.onChange}
              />
            ) : field.type === 'textarea' ? (
              <TextareaInput
                name={field.name}
                placeholder={field.placeholder}
                disabled={field.disabled || isLoading}
                value={controllerField.value ?? ''}
                onChange={controllerField.onChange}
                onBlur={controllerField.onBlur}
                error={!!error}
              />
            ) : field.type === 'date' ? (
              <DateInput
                name={field.name}
                disabled={field.disabled || isLoading}
                value={controllerField.value ?? ''}
                onChange={controllerField.onChange}
                onBlur={controllerField.onBlur}
                error={!!error}
              />
            ) : null}
          </FieldWrapper>
        )}
      />
    );
  };

  return (
    <form
      onSubmit={handleSubmit(onSubmit as SubmitHandler<T>)}
      className={clsx('azals-form', `azals-form--${layout}`, className)}
    >
      <div className="azals-form__fields">{fields.map(renderField)}</div>

      <div className="azals-form__actions">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="azals-btn azals-btn--secondary"
            disabled={isLoading}
          >
            {cancelLabel}
          </button>
        )}
        <button
          type="submit"
          className="azals-btn azals-btn--primary"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <span className="azals-spinner azals-spinner--sm" />
              <span>Chargement...</span>
            </>
          ) : (
            submitLabel
          )}
        </button>
      </div>
    </form>
  );
}

// ============================================================
// FORM HOOKS
// ============================================================

export const useFormState = <T extends FieldValues>(
  schema?: z.ZodSchema<T>,
  defaultValues?: Partial<T>
): UseFormReturn<T> => {
  return useForm<T>({
    resolver: schema ? zodResolver(schema) : undefined,
    defaultValues: defaultValues as DefaultValues<T>,
  });
};

// ============================================================
// EXPORTS
// ============================================================

export {
  FieldWrapper,
  TextInput,
  SelectInput,
  CheckboxInput,
  TextareaInput,
  DateInput,
};

export default DynamicForm;
