import React from 'react';

export type BadgeVariant = 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'brand';
export type BadgeSize = 'sm' | 'md';

export interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  dot?: boolean;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'neutral',
  size = 'md',
  dot = false,
  className = '',
}) => {
  const variantStyles: Record<BadgeVariant, { bg: string; text: string; dot: string }> = {
    success: {
      bg: 'bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800/60',
      text: 'text-emerald-700 dark:text-emerald-300',
      dot: 'bg-emerald-500',
    },
    warning: {
      bg: 'bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60',
      text: 'text-amber-700 dark:text-amber-300',
      dot: 'bg-amber-500',
    },
    danger: {
      bg: 'bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60',
      text: 'text-rose-700 dark:text-rose-300',
      dot: 'bg-rose-500',
    },
    info: {
      bg: 'bg-sky-50 dark:bg-sky-950/40 border border-sky-200 dark:border-sky-800/60',
      text: 'text-sky-700 dark:text-sky-300',
      dot: 'bg-sky-500',
    },
    neutral: {
      bg: 'bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700',
      text: 'text-slate-700 dark:text-slate-300',
      dot: 'bg-slate-400',
    },
    brand: {
      bg: 'bg-brand-50 dark:bg-brand-950/40 border border-brand-200 dark:border-brand-800/60',
      text: 'text-brand-700 dark:text-brand-300',
      dot: 'bg-brand-500',
    },
  };

  const sizeStyles: Record<BadgeSize, string> = {
    sm: 'text-[11px] px-2 py-0.5 gap-1 font-medium',
    md: 'text-xs px-2.5 py-1 gap-1.5 font-semibold',
  };

  const current = variantStyles[variant];

  return (
    <span
      className={`inline-flex items-center rounded-full select-none ${current.bg} ${current.text} ${sizeStyles[size]} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${current.dot}`} />}
      <span>{children}</span>
    </span>
  );
};
