import { useState, useEffect, useTransition } from 'react';
import { useSearchParams } from 'react-router-dom';
import { format, subDays } from 'date-fns';
import { AnalyticsFilters } from './FilterBar';

export function useChartFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [, startTransition] = useTransition();

  const initialFilters: AnalyticsFilters = {
    dateRange: {
      startDate: searchParams.get('start_date') || format(subDays(new Date(), 30), 'yyyy-MM-dd'),
      endDate: searchParams.get('end_date') || format(new Date(), 'yyyy-MM-dd'),
    },
    frequency: searchParams.get('frequency') || 'ALL',
    planId: searchParams.get('plan_id') || 'ALL',
    status: searchParams.get('status') || 'ALL',
  };

  const [filters, setFilters] = useState<AnalyticsFilters>(initialFilters);

  // Sync state changes into URL Search Params
  const updateFilters = (newFilters: AnalyticsFilters) => {
    setFilters(newFilters);
    startTransition(() => {
      const params = new URLSearchParams();
      params.set('start_date', newFilters.dateRange.startDate);
      params.set('end_date', newFilters.dateRange.endDate);
      if (newFilters.frequency !== 'ALL') params.set('frequency', newFilters.frequency);
      if (newFilters.planId !== 'ALL') params.set('plan_id', newFilters.planId);
      if (newFilters.status !== 'ALL') params.set('status', newFilters.status);
      setSearchParams(params, { replace: true });
    });
  };

  const resetFilters = () => {
    updateFilters({
      dateRange: {
        startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
        endDate: format(new Date(), 'yyyy-MM-dd'),
      },
      frequency: 'ALL',
      planId: 'ALL',
      status: 'ALL',
    });
  };

  return {
    filters,
    updateFilters,
    resetFilters,
  };
}
