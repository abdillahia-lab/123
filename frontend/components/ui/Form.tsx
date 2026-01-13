'use client';

// Enterprise-Grade Accessible Form Components
// WCAG 2.2 AA Compliant with full keyboard navigation

import React, { forwardRef, useId, useState, useCallback } from 'react';
import { AlertCircle, Check, Eye, EyeOff, Info, ChevronDown } from 'lucide-react';

// ============================================================================
// FORM CONTEXT
// ============================================================================

interface FormFieldContextValue {
  id: string;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}

const FormFieldContext = React.createContext<FormFieldContextValue | null>(null);

function useFormField() {
  const context = React.useContext(FormFieldContext);
  if (!context) {
    throw new Error('Form field components must be used within a FormField');
  }
  return context;
}

// ============================================================================
// FORM FIELD WRAPPER
// ============================================================================

interface FormFieldProps {
  children: React.ReactNode;
  error?: string;
  required?: boolean;
  disabled?: boolean;
  className?: string;
}

export function FormField({
  children,
  error,
  required,
  disabled,
  className = '',
}: FormFieldProps) {
  const id = useId();

  return (
    <FormFieldContext.Provider value={{ id, error, required, disabled }}>
      <div className={`space-y-1.5 ${className}`}>{children}</div>
    </FormFieldContext.Provider>
  );
}

// ============================================================================
// LABEL
// ============================================================================

interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  hint?: string;
}

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  ({ children, hint, className = '', ...props }, ref) => {
    const { id, required } = useFormField();

    return (
      <div className="flex items-center gap-2">
        <label
          ref={ref}
          htmlFor={id}
          className={`text-sm font-medium text-gray-700 dark:text-gray-300 ${className}`}
          {...props}
        >
          {children}
          {required && (
            <span className="text-red-500 ml-1" aria-hidden="true">
              *
            </span>
          )}
        </label>
        {hint && (
          <span className="group relative">
            <Info className="w-4 h-4 text-gray-400 cursor-help" aria-hidden="true" />
            <span
              role="tooltip"
              className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 px-2 py-1 text-xs text-white bg-gray-900 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none"
            >
              {hint}
            </span>
            <span className="sr-only">{hint}</span>
          </span>
        )}
      </div>
    );
  }
);
Label.displayName = 'Label';

// ============================================================================
// TEXT INPUT
// ============================================================================

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  leadingIcon?: React.ReactNode;
  trailingIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className = '', leadingIcon, trailingIcon, type = 'text', ...props }, ref) => {
    const { id, error, required, disabled } = useFormField();
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === 'password';

    return (
      <div className="relative">
        {leadingIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
            {leadingIcon}
          </div>
        )}
        <input
          ref={ref}
          id={id}
          type={isPassword && showPassword ? 'text' : type}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          aria-required={required}
          disabled={disabled}
          className={`
            w-full px-3 py-2.5 rounded-lg border transition-colors
            text-gray-900 dark:text-white
            bg-white dark:bg-gray-800
            placeholder:text-gray-400 dark:placeholder:text-gray-500
            focus:outline-none focus:ring-2 focus:ring-terra-500 focus:border-transparent
            disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 dark:disabled:bg-gray-900
            ${leadingIcon ? 'pl-10' : ''}
            ${trailingIcon || isPassword ? 'pr-10' : ''}
            ${
              error
                ? 'border-red-500 focus:ring-red-500'
                : 'border-gray-300 dark:border-gray-600'
            }
            ${className}
          `}
          {...props}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none focus:text-gray-600"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? (
              <EyeOff className="w-5 h-5" aria-hidden="true" />
            ) : (
              <Eye className="w-5 h-5" aria-hidden="true" />
            )}
          </button>
        )}
        {trailingIcon && !isPassword && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 pointer-events-none">
            {trailingIcon}
          </div>
        )}
      </div>
    );
  }
);
Input.displayName = 'Input';

// ============================================================================
// TEXTAREA
// ============================================================================

interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  resize?: boolean;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className = '', resize = true, ...props }, ref) => {
    const { id, error, required, disabled } = useFormField();

    return (
      <textarea
        ref={ref}
        id={id}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        aria-required={required}
        disabled={disabled}
        className={`
          w-full px-3 py-2.5 rounded-lg border transition-colors
          text-gray-900 dark:text-white
          bg-white dark:bg-gray-800
          placeholder:text-gray-400 dark:placeholder:text-gray-500
          focus:outline-none focus:ring-2 focus:ring-terra-500 focus:border-transparent
          disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 dark:disabled:bg-gray-900
          ${resize ? 'resize-y' : 'resize-none'}
          ${
            error
              ? 'border-red-500 focus:ring-red-500'
              : 'border-gray-300 dark:border-gray-600'
          }
          ${className}
        `}
        {...props}
      />
    );
  }
);
Textarea.displayName = 'Textarea';

// ============================================================================
// SELECT
// ============================================================================

interface SelectOption {
  value: string;
  label: string;
  disabled?: boolean;
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'children'> {
  options: SelectOption[];
  placeholder?: string;
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className = '', options, placeholder, ...props }, ref) => {
    const { id, error, required, disabled } = useFormField();

    return (
      <div className="relative">
        <select
          ref={ref}
          id={id}
          aria-invalid={!!error}
          aria-describedby={error ? `${id}-error` : undefined}
          aria-required={required}
          disabled={disabled}
          className={`
            w-full px-3 py-2.5 pr-10 rounded-lg border transition-colors appearance-none
            text-gray-900 dark:text-white
            bg-white dark:bg-gray-800
            focus:outline-none focus:ring-2 focus:ring-terra-500 focus:border-transparent
            disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-gray-100 dark:disabled:bg-gray-900
            ${
              error
                ? 'border-red-500 focus:ring-red-500'
                : 'border-gray-300 dark:border-gray-600'
            }
            ${className}
          `}
          {...props}
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
        <ChevronDown
          className="absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400 pointer-events-none"
          aria-hidden="true"
        />
      </div>
    );
  }
);
Select.displayName = 'Select';

// ============================================================================
// CHECKBOX
// ============================================================================

interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  label: string;
  description?: string;
}

export const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(
  ({ label, description, className = '', ...props }, ref) => {
    const { id, error, disabled } = useFormField();

    return (
      <div className={`flex items-start ${className}`}>
        <div className="flex items-center h-5">
          <input
            ref={ref}
            id={id}
            type="checkbox"
            aria-invalid={!!error}
            aria-describedby={
              [error ? `${id}-error` : '', description ? `${id}-description` : '']
                .filter(Boolean)
                .join(' ') || undefined
            }
            disabled={disabled}
            className="
              w-4 h-4 rounded border-gray-300 dark:border-gray-600
              text-terra-600 focus:ring-terra-500 focus:ring-2
              disabled:opacity-50 disabled:cursor-not-allowed
            "
            {...props}
          />
        </div>
        <div className="ml-3">
          <label
            htmlFor={id}
            className={`text-sm font-medium ${
              disabled ? 'text-gray-400' : 'text-gray-700 dark:text-gray-300'
            }`}
          >
            {label}
          </label>
          {description && (
            <p id={`${id}-description`} className="text-sm text-gray-500 dark:text-gray-400">
              {description}
            </p>
          )}
        </div>
      </div>
    );
  }
);
Checkbox.displayName = 'Checkbox';

// ============================================================================
// RADIO GROUP
// ============================================================================

interface RadioOption {
  value: string;
  label: string;
  description?: string;
  disabled?: boolean;
}

interface RadioGroupProps {
  name: string;
  options: RadioOption[];
  value?: string;
  onChange?: (value: string) => void;
  orientation?: 'horizontal' | 'vertical';
  className?: string;
}

export function RadioGroup({
  name,
  options,
  value,
  onChange,
  orientation = 'vertical',
  className = '',
}: RadioGroupProps) {
  const { id, error, disabled: groupDisabled } = useFormField();

  return (
    <div
      role="radiogroup"
      aria-labelledby={`${id}-label`}
      aria-invalid={!!error}
      className={`
        ${orientation === 'horizontal' ? 'flex flex-wrap gap-4' : 'space-y-3'}
        ${className}
      `}
    >
      {options.map((option) => {
        const optionId = `${id}-${option.value}`;
        const isDisabled = groupDisabled || option.disabled;

        return (
          <div key={option.value} className="flex items-start">
            <div className="flex items-center h-5">
              <input
                id={optionId}
                name={name}
                type="radio"
                value={option.value}
                checked={value === option.value}
                onChange={(e) => onChange?.(e.target.value)}
                disabled={isDisabled}
                className="
                  w-4 h-4 border-gray-300 dark:border-gray-600
                  text-terra-600 focus:ring-terra-500 focus:ring-2
                  disabled:opacity-50 disabled:cursor-not-allowed
                "
              />
            </div>
            <div className="ml-3">
              <label
                htmlFor={optionId}
                className={`text-sm font-medium ${
                  isDisabled ? 'text-gray-400' : 'text-gray-700 dark:text-gray-300'
                }`}
              >
                {option.label}
              </label>
              {option.description && (
                <p className="text-sm text-gray-500 dark:text-gray-400">{option.description}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// ERROR MESSAGE
// ============================================================================

export function ErrorMessage({ className = '' }: { className?: string }) {
  const { id, error } = useFormField();

  if (!error) return null;

  return (
    <div
      id={`${id}-error`}
      role="alert"
      aria-live="polite"
      className={`flex items-center gap-1.5 text-sm text-red-600 dark:text-red-400 ${className}`}
    >
      <AlertCircle className="w-4 h-4 flex-shrink-0" aria-hidden="true" />
      <span>{error}</span>
    </div>
  );
}

// ============================================================================
// HELPER TEXT
// ============================================================================

export function HelperText({
  children,
  className = '',
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const { id, error } = useFormField();

  if (error) return null;

  return (
    <p
      id={`${id}-helper`}
      className={`text-sm text-gray-500 dark:text-gray-400 ${className}`}
    >
      {children}
    </p>
  );
}

// ============================================================================
// SWITCH / TOGGLE
// ============================================================================

interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export function Switch({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  className = '',
}: SwitchProps) {
  const id = useId();

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        if (!disabled) {
          onChange(!checked);
        }
      }
    },
    [checked, disabled, onChange]
  );

  return (
    <div className={`flex items-start ${className}`}>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        aria-labelledby={`${id}-label`}
        aria-describedby={description ? `${id}-description` : undefined}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        onKeyDown={handleKeyDown}
        className={`
          relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent
          transition-colors duration-200 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-terra-500 focus:ring-offset-2
          disabled:opacity-50 disabled:cursor-not-allowed
          ${checked ? 'bg-terra-600' : 'bg-gray-200 dark:bg-gray-700'}
        `}
      >
        <span
          aria-hidden="true"
          className={`
            pointer-events-none inline-block h-5 w-5 transform rounded-full
            bg-white shadow ring-0 transition duration-200 ease-in-out
            ${checked ? 'translate-x-5' : 'translate-x-0'}
          `}
        />
      </button>
      <div className="ml-3">
        <span
          id={`${id}-label`}
          className={`text-sm font-medium ${
            disabled ? 'text-gray-400' : 'text-gray-700 dark:text-gray-300'
          }`}
        >
          {label}
        </span>
        {description && (
          <p id={`${id}-description`} className="text-sm text-gray-500 dark:text-gray-400">
            {description}
          </p>
        )}
      </div>
    </div>
  );
}

// ============================================================================
// BUTTON
// ============================================================================

type ButtonVariant = 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const variantStyles: Record<ButtonVariant, string> = {
  primary: `
    bg-terra-600 text-white
    hover:bg-terra-700
    focus:ring-terra-500
    disabled:bg-terra-400
  `,
  secondary: `
    bg-gray-600 text-white
    hover:bg-gray-700
    focus:ring-gray-500
    disabled:bg-gray-400
  `,
  outline: `
    border-2 border-terra-600 text-terra-600
    hover:bg-terra-50 dark:hover:bg-terra-900/20
    focus:ring-terra-500
    disabled:border-gray-300 disabled:text-gray-400
  `,
  ghost: `
    text-gray-700 dark:text-gray-300
    hover:bg-gray-100 dark:hover:bg-gray-800
    focus:ring-gray-500
  `,
  danger: `
    bg-red-600 text-white
    hover:bg-red-700
    focus:ring-red-500
    disabled:bg-red-400
  `,
};

const sizeStyles: Record<ButtonSize, string> = {
  sm: 'px-3 py-1.5 text-sm',
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3 text-base',
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      leftIcon,
      rightIcon,
      children,
      disabled,
      className = '',
      ...props
    },
    ref
  ) => {
    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`
          inline-flex items-center justify-center gap-2
          font-medium rounded-lg
          transition-colors duration-200
          focus:outline-none focus:ring-2 focus:ring-offset-2
          disabled:cursor-not-allowed
          ${variantStyles[variant]}
          ${sizeStyles[size]}
          ${className}
        `}
        {...props}
      >
        {loading ? (
          <svg
            className="animate-spin h-4 w-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        ) : (
          leftIcon
        )}
        <span>{children}</span>
        {!loading && rightIcon}
      </button>
    );
  }
);
Button.displayName = 'Button';
