import React, { forwardRef } from 'react';
import { ChevronDown } from 'lucide-react';

export interface SelectOption {
  value: string;
  label: string;
}

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label?: string;
  error?: string;
  helperText?: string;
  options: SelectOption[];
}

export const Select = forwardRef<HTMLSelectElement, SelectProps>(({
  label,
  error,
  helperText,
  options,
  className = '',
  id,
  disabled,
  ...props
}, ref) => {
  const selectId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full space-y-1.5">
      {label && (
        <label
          htmlFor={selectId}
          className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300"
        >
          {label}
        </label>
      )}

      <div className="relative rounded-lg shadow-sm">
        <select
          ref={ref}
          id={selectId}
          disabled={disabled}
          className={`block w-full appearance-none rounded-lg border text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-offset-1 disabled:opacity-60 disabled:cursor-not-allowed pl-3.5 pr-10 py-2 ${
            error
              ? 'border-red-300 bg-red-50/30 text-red-900 focus:border-red-500 focus:ring-red-500 dark:border-red-800 dark:bg-red-950/20 dark:text-red-300'
              : 'border-slate-300 bg-white text-slate-900 hover:border-slate-400 focus:border-brand-500 focus:ring-brand-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100 dark:hover:border-slate-600'
          } ${className}`}
          {...props}
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="dark:bg-slate-900 dark:text-slate-100">
              {opt.label}
            </option>
          ))}
        </select>

        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3 text-slate-400">
          <ChevronDown className="w-4 h-4" />
        </div>
      </div>

      {error ? (
        <p className="text-xs text-red-600 dark:text-red-400 font-medium">{error}</p>
      ) : helperText ? (
        <p className="text-xs text-slate-500 dark:text-slate-400">{helperText}</p>
      ) : null}
    </div>
  );
});

Select.displayName = 'Select';
