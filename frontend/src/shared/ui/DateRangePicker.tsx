import React, { useState } from 'react';
import { Calendar as CalendarIcon, ChevronDown } from 'lucide-react';
import { subDays, startOfMonth, startOfQuarter, startOfYear, format } from 'date-fns';

export interface DateRange {
  startDate: string; // YYYY-MM-DD
  endDate: string;   // YYYY-MM-DD
}

export interface DateRangePickerProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
  className?: string;
}

export const DateRangePicker: React.FC<DateRangePickerProps> = ({
  value,
  onChange,
  className = '',
}) => {
  const [isOpen, setIsOpen] = useState(false);

  const presets = [
    {
      label: 'Last 7 Days',
      getRange: () => ({
        startDate: format(subDays(new Date(), 7), 'yyyy-MM-dd'),
        endDate: format(new Date(), 'yyyy-MM-dd'),
      }),
    },
    {
      label: 'Last 30 Days',
      getRange: () => ({
        startDate: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
        endDate: format(new Date(), 'yyyy-MM-dd'),
      }),
    },
    {
      label: 'This Month',
      getRange: () => ({
        startDate: format(startOfMonth(new Date()), 'yyyy-MM-dd'),
        endDate: format(new Date(), 'yyyy-MM-dd'),
      }),
    },
    {
      label: 'This Quarter',
      getRange: () => ({
        startDate: format(startOfQuarter(new Date()), 'yyyy-MM-dd'),
        endDate: format(new Date(), 'yyyy-MM-dd'),
      }),
    },
    {
      label: 'Year to Date',
      getRange: () => ({
        startDate: format(startOfYear(new Date()), 'yyyy-MM-dd'),
        endDate: format(new Date(), 'yyyy-MM-dd'),
      }),
    },
  ];

  return (
    <div className={`relative inline-block text-left ${className}`}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-700 dark:text-slate-200 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors shadow-sm"
      >
        <CalendarIcon className="w-4 h-4 text-slate-400" />
        <span>
          {value.startDate} — {value.endDate}
        </span>
        <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-1" />
      </button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 z-50 mt-2 w-64 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 p-3 shadow-xl space-y-3">
            <div className="space-y-1">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 px-2">
                Presets
              </span>
              <div className="grid grid-cols-1 gap-1">
                {presets.map((p) => (
                  <button
                    key={p.label}
                    onClick={() => {
                      onChange(p.getRange());
                      setIsOpen(false);
                    }}
                    className="w-full text-left px-2.5 py-1.5 text-xs rounded-md text-slate-700 dark:text-slate-200 hover:bg-slate-100 dark:hover:bg-slate-800 font-medium transition-colors"
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="border-t border-slate-100 dark:border-slate-800 pt-2 space-y-2">
              <span className="text-[10px] uppercase font-bold tracking-wider text-slate-400 px-2">
                Custom Range
              </span>
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">From</label>
                  <input
                    type="date"
                    value={value.startDate}
                    onChange={(e) => onChange({ ...value, startDate: e.target.value })}
                    className="w-full text-xs p-1.5 border border-slate-200 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-[10px] text-slate-500 block mb-1">To</label>
                  <input
                    type="date"
                    value={value.endDate}
                    onChange={(e) => onChange({ ...value, endDate: e.target.value })}
                    className="w-full text-xs p-1.5 border border-slate-200 dark:border-slate-700 rounded bg-slate-50 dark:bg-slate-800 text-slate-800 dark:text-slate-200"
                  />
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
