import React from 'react';
import { Filter, RotateCcw } from 'lucide-react';
import { DateRangePicker, DateRange } from '@/shared/ui/DateRangePicker';
import { Select } from '@/shared/ui/Select';
import { Button } from '@/shared/ui/Button';

export interface AnalyticsFilters {
  dateRange: DateRange;
  frequency: string;
  planId: string;
  status: string;
  search?: string;
}

export interface FilterBarProps {
  filters: AnalyticsFilters;
  onChange: (filters: AnalyticsFilters) => void;
  onReset?: () => void;
  className?: string;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onChange,
  onReset,
  className = '',
}) => {
  const frequencyOptions = [
    { value: 'ALL', label: 'All Frequencies' },
    { value: 'MONTHLY', label: 'Monthly' },
    { value: 'YEARLY', label: 'Yearly' },
    { value: 'WEEKLY', label: 'Weekly' },
    { value: 'DAILY', label: 'Daily' },
  ];

  const statusOptions = [
    { value: 'ALL', label: 'All Statuses' },
    { value: 'ACTIVE', label: 'Active only' },
    { value: 'PAUSED', label: 'Paused' },
    { value: 'CLOSED', label: 'Closed' },
  ];

  const planOptions = [
    { value: 'ALL', label: 'All Plans' },
    { value: 'plan-ent-monthly', label: 'Enterprise Cloud' },
    { value: 'plan-growth-yearly', label: 'Growth Yearly' },
    { value: 'plan-support-monthly', label: '24/7 SLA Support' },
  ];

  return (
    <div
      className={`p-4 rounded-2xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm flex flex-wrap items-center justify-between gap-3 ${className}`}
    >
      <div className="flex flex-wrap items-center gap-2.5">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-slate-400 mr-1">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters:</span>
        </div>

        <DateRangePicker
          value={filters.dateRange}
          onChange={(dateRange) => onChange({ ...filters, dateRange })}
        />

        <div className="w-36">
          <Select
            options={frequencyOptions}
            value={filters.frequency}
            onChange={(e) => onChange({ ...filters, frequency: e.target.value })}
          />
        </div>

        <div className="w-40">
          <Select
            options={planOptions}
            value={filters.planId}
            onChange={(e) => onChange({ ...filters, planId: e.target.value })}
          />
        </div>

        <div className="w-32">
          <Select
            options={statusOptions}
            value={filters.status}
            onChange={(e) => onChange({ ...filters, status: e.target.value })}
          />
        </div>
      </div>

      {onReset && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onReset}
          leftIcon={<RotateCcw className="w-3.5 h-3.5" />}
        >
          Reset
        </Button>
      )}
    </div>
  );
};
