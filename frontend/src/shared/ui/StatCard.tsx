import React from 'react';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { Card } from './Card';

export interface StatCardProps {
  title: string;
  value: string | number;
  changePct?: number;
  comparisonLabel?: string;
  icon?: React.ReactNode;
  subtitle?: string;
  isLoading?: boolean;
  className?: string;
  invertColors?: boolean; // When lower is better (e.g. churn or overdue)
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  changePct,
  comparisonLabel = 'vs last period',
  icon,
  subtitle,
  isLoading = false,
  className = '',
  invertColors = false,
}) => {
  const isPositive = changePct !== undefined && changePct > 0;
  const isNegative = changePct !== undefined && changePct < 0;
  const isZero = changePct !== undefined && changePct === 0;

  // Good vs bad depending on invertColors
  const isGood = invertColors ? isNegative : isPositive;
  const isBad = invertColors ? isPositive : isNegative;

  return (
    <Card className={`p-5 relative overflow-hidden ${className}`}>
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
            {title}
          </p>
          
          {isLoading ? (
            <div className="mt-2 h-7 w-28 bg-slate-200 dark:bg-slate-800 animate-pulse rounded"></div>
          ) : (
            <h3 className="mt-1 text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
              {value}
            </h3>
          )}

          {subtitle && (
            <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">{subtitle}</p>
          )}
        </div>

        {icon && (
          <div className="p-2.5 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 shrink-0">
            {icon}
          </div>
        )}
      </div>

      {changePct !== undefined && !isLoading && (
        <div className="mt-4 flex items-center gap-2 text-xs">
          <span
            className={`inline-flex items-center gap-1 font-semibold px-2 py-0.5 rounded-md ${
              isGood
                ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300'
                : isBad
                ? 'bg-rose-50 text-rose-700 dark:bg-rose-950/40 dark:text-rose-300'
                : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'
            }`}
          >
            {isPositive && <TrendingUp className="w-3.5 h-3.5" />}
            {isNegative && <TrendingDown className="w-3.5 h-3.5" />}
            {isZero && <Minus className="w-3.5 h-3.5" />}
            <span>
              {isPositive ? '+' : ''}
              {changePct.toFixed(1)}%
            </span>
          </span>
          <span className="text-slate-400 dark:text-slate-500">{comparisonLabel}</span>
        </div>
      )}
    </Card>
  );
};
