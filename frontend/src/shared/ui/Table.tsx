import React from 'react';
import { ChevronLeft, ChevronRight, ChevronsUpDown } from 'lucide-react';

export interface Column<T> {
  key: string;
  header: string;
  render?: (item: T, index: number) => React.ReactNode;
  align?: 'left' | 'center' | 'right';
  className?: string;
}

export interface TableProps<T> {
  columns: Column<T>[];
  data: T[];
  isLoading?: boolean;
  emptyMessage?: string;
  total?: number;
  page?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
  keyExtractor?: (item: T, index: number) => string;
}

export function Table<T extends Record<string, any>>({
  columns,
  data,
  isLoading = false,
  emptyMessage = "No records found.",
  total,
  page = 1,
  pageSize = 20,
  onPageChange,
  keyExtractor,
}: TableProps<T>) {
  const totalPages = total ? Math.ceil(total / pageSize) : 1;

  const getAlignClass = (align?: 'left' | 'center' | 'right') => {
    if (align === 'right') return 'text-right';
    if (align === 'center') return 'text-center';
    return 'text-left';
  };

  return (
    <div className="w-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm text-slate-600 dark:text-slate-300">
          <thead className="bg-slate-50/80 dark:bg-slate-800/50 text-xs uppercase tracking-wider font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className={`px-4 py-3.5 ${getAlignClass(col.align)} ${col.className || ''}`}
                >
                  <div className="inline-flex items-center gap-1.5">
                    <span>{col.header}</span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>

          <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
            {isLoading ? (
              Array.from({ length: 4 }).map((_, rIdx) => (
                <tr key={`skel-${rIdx}`} className="animate-pulse">
                  {columns.map((col) => (
                    <td key={`skel-td-${col.key}`} className="px-4 py-4">
                      <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
                    </td>
                  ))}
                </tr>
              ))
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-12 text-center text-slate-400 dark:text-slate-500"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((item, idx) => {
                const key = keyExtractor ? keyExtractor(item, idx) : item.id || `row-${idx}`;
                return (
                  <tr
                    key={key}
                    className="hover:bg-slate-50/60 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    {columns.map((col) => (
                      <td
                        key={`${key}-${col.key}`}
                        className={`px-4 py-3.5 whitespace-nowrap text-slate-800 dark:text-slate-200 ${getAlignClass(col.align)}`}
                      >
                        {col.render ? col.render(item, idx) : item[col.key] ?? '—'}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {total !== undefined && onPageChange && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 text-xs text-slate-500 dark:text-slate-400">
          <div>
            Showing <span className="font-semibold">{Math.min((page - 1) * pageSize + 1, total)}</span> to{' '}
            <span className="font-semibold">{Math.min(page * pageSize, total)}</span> of{' '}
            <span className="font-semibold">{total}</span> entries
          </div>

          <div className="flex items-center gap-1.5">
            <button
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
              className="p-1 rounded-md border border-slate-200 dark:border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-2 py-1 font-medium text-slate-700 dark:text-slate-300">
              {page} / {totalPages || 1}
            </span>
            <button
              disabled={page >= totalPages}
              onClick={() => onPageChange(page + 1)}
              className="p-1 rounded-md border border-slate-200 dark:border-slate-700 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 dark:hover:bg-slate-800"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
