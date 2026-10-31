import React, { useState, useEffect, useCallback, useMemo } from 'react';
import {
  FileText,
  Download,
  Calendar,
  Filter,
  RefreshCw,
  Search,
  CheckCircle,
  AlertCircle,
  FileSpreadsheet,
  FileDown,
  ChevronRight,
  TrendingUp,
  CreditCard,
  DollarSign,
  Layers,
  Tag
} from 'lucide-react';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Input } from '@/shared/ui/Input';
import { Select } from '@/shared/ui/Select';
import { reportsApi } from '../../api/reportsApi';
import { ReportMetadata, ReportResult } from '../../types/reports';

const REPORT_ICONS: Record<string, React.ReactNode> = {
  'monthly-financial': <TrendingUp className="w-5 h-5 text-indigo-500" />,
  'revenue': <DollarSign className="w-5 h-5 text-emerald-500" />,
  'outstanding-invoices': <AlertCircle className="w-5 h-5 text-amber-500" />,
  'payments': <CreditCard className="w-5 h-5 text-blue-500" />,
  'subscriptions': <Layers className="w-5 h-5 text-purple-500" />,
  'discount-performance': <Tag className="w-5 h-5 text-rose-500" />,
};

export const FinancialReportsPage: React.FC = () => {
  const [catalog, setCatalog] = useState<ReportMetadata[]>([]);
  const [selectedReportId, setSelectedReportId] = useState<string>('monthly-financial');
  const [reportData, setReportData] = useState<ReportResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [downloading, setDownloading] = useState<'csv' | 'pdf' | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [startDate, setStartDate] = useState<string>(
    new Date(Date.now() - 180 * 86400000).toISOString().slice(0, 10)
  );
  const [endDate, setEndDate] = useState<string>(
    new Date().toISOString().slice(0, 10)
  );
  const [asOfDate, setAsOfDate] = useState<string>(
    new Date().toISOString().slice(0, 10)
  );
  const [subStatus, setSubStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Pagination for preview table
  const [page, setPage] = useState<number>(1);
  const pageSize = 15;

  // Load catalog on mount
  useEffect(() => {
    async function loadCatalog() {
      try {
        const res = await reportsApi.getCatalog();
        setCatalog(res.reports);
      } catch (err: any) {
        console.error('Failed to load report catalog:', err);
      }
    }
    loadCatalog();
  }, []);

  // Fetch report data
  const fetchReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, any> = {};
      if (selectedReportId === 'outstanding-invoices') {
        if (asOfDate) params.as_of_date = asOfDate;
      } else if (selectedReportId === 'subscriptions') {
        if (subStatus && subStatus !== 'ALL') params.status = subStatus;
      } else {
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;
      }

      const data = await reportsApi.getReportData(selectedReportId, params);
      setReportData(data);
      setPage(1);
    } catch (err: any) {
      setError(err.message || 'Failed to generate report');
    } finally {
      setLoading(false);
    }
  }, [selectedReportId, startDate, endDate, asOfDate, subStatus]);

  useEffect(() => {
    fetchReport();
  }, [fetchReport]);

  // Handle CSV / PDF download
  const handleDownload = async (format: 'csv' | 'pdf') => {
    setDownloading(format);
    try {
      const params: Record<string, any> = {};
      if (selectedReportId === 'outstanding-invoices') {
        if (asOfDate) params.as_of_date = asOfDate;
      } else if (selectedReportId === 'subscriptions') {
        if (subStatus && subStatus !== 'ALL') params.status = subStatus;
      } else {
        if (startDate) params.start_date = startDate;
        if (endDate) params.end_date = endDate;
      }

      await reportsApi.downloadReport(selectedReportId, format, params);
    } catch (err: any) {
      alert(`Download failed: ${err.message}`);
    } finally {
      setDownloading(null);
    }
  };

  // Filter rows by search query
  const filteredRows = useMemo(() => {
    if (!reportData?.rows) return [];
    if (!searchQuery.trim()) return reportData.rows;
    const q = searchQuery.toLowerCase();
    return reportData.rows.filter((row) =>
      row.some((cell) => String(cell).toLowerCase().includes(q))
    );
  }, [reportData, searchQuery]);

  // Paginated slice
  const paginatedRows = useMemo(() => {
    const start = (page - 1) * pageSize;
    return filteredRows.slice(start, start + pageSize);
  }, [filteredRows, page, pageSize]);

  const totalPages = Math.ceil(filteredRows.length / pageSize) || 1;

  const currentMeta = catalog.find((c) => c.id === selectedReportId);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Financial Reports & Accounting Ledgers
            </h1>
            <Badge variant="outline" className="text-xs font-mono uppercase bg-slate-50 dark:bg-slate-800">
              P3-T14
            </Badge>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Export audit-ready financial statements, streaming CSV ledgers, and ReportLab PDF packs.
          </p>
        </div>

        {/* Global Export Actions */}
        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            onClick={() => handleDownload('csv')}
            disabled={downloading !== null || loading}
            className="flex items-center gap-2 border-emerald-600 text-emerald-700 hover:bg-emerald-50 dark:border-emerald-500 dark:text-emerald-400 dark:hover:bg-emerald-950/40"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
            <span>{downloading === 'csv' ? 'Streaming CSV...' : 'Download CSV'}</span>
          </Button>

          <Button
            variant="outline"
            onClick={() => handleDownload('pdf')}
            disabled={downloading !== null || loading}
            className="flex items-center gap-2 border-rose-600 text-rose-700 hover:bg-rose-50 dark:border-rose-500 dark:text-rose-400 dark:hover:bg-rose-950/40"
          >
            <FileDown className="w-4 h-4 text-rose-600 dark:text-rose-400" />
            <span>{downloading === 'pdf' ? 'Building PDF...' : 'Download PDF'}</span>
          </Button>

          <Button
            variant="ghost"
            onClick={fetchReport}
            disabled={loading}
            className="p-2"
            title="Refresh Data"
          >
            <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Report Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {(catalog.length > 0 ? catalog : [
          { id: 'monthly-financial', name: 'Monthly Financial Pack', description: 'Revenue & collections' },
          { id: 'revenue', name: 'Revenue Ledger', description: 'Itemized invoices' },
          { id: 'outstanding-invoices', name: 'Outstanding AR', description: 'Aging balances' },
          { id: 'payments', name: 'Payments Ledger', description: 'Cash receipts' },
          { id: 'subscriptions', name: 'Subscriptions', description: 'Contract portfolio' },
          { id: 'discount-performance', name: 'Discounts', description: 'Promos & leakage' },
        ]).map((rep) => {
          const isSelected = rep.id === selectedReportId;
          return (
            <button
              key={rep.id}
              onClick={() => {
                setSelectedReportId(rep.id);
                setSearchQuery('');
              }}
              className={`text-left p-3.5 rounded-xl border transition-all text-xs flex flex-col justify-between ${
                isSelected
                  ? 'border-indigo-600 bg-indigo-50/60 dark:bg-indigo-950/30 dark:border-indigo-500 ring-2 ring-indigo-500/20'
                  : 'border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 hover:border-slate-300 dark:hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between w-full mb-2">
                <div className="p-1.5 rounded-lg bg-slate-100 dark:bg-slate-800">
                  {REPORT_ICONS[rep.id] || <FileText className="w-4 h-4 text-slate-500" />}
                </div>
                {isSelected && (
                  <Badge variant="default" className="text-[10px] py-0 px-1.5 bg-indigo-600">
                    Active
                  </Badge>
                )}
              </div>
              <div>
                <p className="font-semibold text-slate-900 dark:text-white line-clamp-1">
                  {rep.name}
                </p>
                <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5 line-clamp-2">
                  {rep.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>

      {/* Filter and Configuration Bar */}
      <Card className="p-4 bg-slate-50/70 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
              <Filter className="w-3.5 h-3.5" /> Filters:
            </span>

            {selectedReportId === 'outstanding-invoices' ? (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500">As of Date:</span>
                <input
                  type="date"
                  value={asOfDate}
                  onChange={(e) => setAsOfDate(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            ) : selectedReportId === 'subscriptions' ? (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500">Status:</span>
                <select
                  value={subStatus}
                  onChange={(e) => setSubStatus(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                >
                  <option value="ALL">All Statuses</option>
                  <option value="ACTIVE">ACTIVE</option>
                  <option value="PAST_DUE">PAST_DUE</option>
                  <option value="CANCELLED">CANCELLED</option>
                  <option value="EXPIRED">EXPIRED</option>
                </select>
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-slate-500">Date Range:</span>
                <input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
                <span className="text-slate-400">to</span>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="px-2.5 py-1.5 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-xs text-slate-800 dark:text-slate-200 focus:outline-none focus:ring-1 focus:ring-indigo-500"
                />
              </div>
            )}

            <Button
              size="sm"
              variant="outline"
              onClick={fetchReport}
              disabled={loading}
              className="text-xs px-3 py-1.5 h-auto"
            >
              Apply Filter
            </Button>
          </div>

          {/* Table Search */}
          <div className="relative w-64">
            <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search table rows..."
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full pl-8 pr-3 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-indigo-500"
            />
          </div>
        </div>
      </Card>

      {/* Summary KPI Strip */}
      {reportData?.summary && Object.keys(reportData.summary).length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
          {Object.entries(reportData.summary).map(([kpiName, kpiValue]) => (
            <div
              key={kpiName}
              className="p-3.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm"
            >
              <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400 truncate">
                {kpiName}
              </p>
              <p className="text-base font-bold text-slate-900 dark:text-white mt-1">
                {kpiValue}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/30 dark:text-rose-300 text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-500" />
          <span>{error}</span>
        </div>
      )}

      {/* Report Live Preview Table */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs text-slate-500 px-1">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-800 dark:text-slate-200">
              {reportData?.title || 'Report Preview'}
            </span>
            <span>•</span>
            <span>{reportData?.subtitle}</span>
          </div>
          <div>
            Showing <span className="font-medium">{filteredRows.length}</span> records
          </div>
        </div>

        <div className="w-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800/60 uppercase tracking-wider font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 text-[11px]">
                <tr>
                  {reportData?.headers.map((h, hIdx) => (
                    <th key={hIdx} className="px-3.5 py-3 whitespace-nowrap">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
                {loading ? (
                  Array.from({ length: 6 }).map((_, rIdx) => (
                    <tr key={`skel-${rIdx}`} className="animate-pulse">
                      {reportData?.headers.map((_, cIdx) => (
                        <td key={`skel-td-${cIdx}`} className="px-3.5 py-3">
                          <div className="h-3.5 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
                        </td>
                      )) || (
                        <td className="px-3.5 py-3">
                          <div className="h-3.5 bg-slate-200 dark:bg-slate-800 rounded w-3/4"></div>
                        </td>
                      )}
                    </tr>
                  ))
                ) : paginatedRows.length === 0 ? (
                  <tr>
                    <td
                      colSpan={reportData?.headers.length || 1}
                      className="px-4 py-12 text-center text-slate-400 dark:text-slate-500"
                    >
                      No records found for the selected parameters.
                    </td>
                  </tr>
                ) : (
                  paginatedRows.map((row, rIdx) => (
                    <tr
                      key={rIdx}
                      className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                    >
                      {row.map((cell, cIdx) => {
                        const str = String(cell ?? '—');
                        const isCurrency = str.startsWith('₹') || str.startsWith('$');
                        const isStatus = ['ACTIVE', 'PAID', 'OVERDUE', 'CANCELLED', 'PAST_DUE'].includes(str);
                        return (
                          <td
                            key={cIdx}
                            className={`px-3.5 py-3 whitespace-nowrap text-slate-800 dark:text-slate-200 ${
                              isCurrency ? 'font-mono text-right font-medium' : ''
                            }`}
                          >
                            {isStatus ? (
                              <Badge
                                variant={
                                  str === 'ACTIVE' || str === 'PAID'
                                    ? 'success'
                                    : str === 'OVERDUE' || str === 'CANCELLED'
                                    ? 'danger'
                                    : 'warning'
                                }
                                className="text-[10px] py-0 px-2 uppercase font-semibold"
                              >
                                {str}
                              </Badge>
                            ) : (
                              str
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination Controls */}
          {filteredRows.length > pageSize && (
            <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 text-xs text-slate-500 dark:text-slate-400">
              <div>
                Showing <span className="font-semibold">{(page - 1) * pageSize + 1}</span> to{' '}
                <span className="font-semibold">{Math.min(page * pageSize, filteredRows.length)}</span> of{' '}
                <span className="font-semibold">{filteredRows.length}</span> rows
              </div>

              <div className="flex items-center gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="text-xs h-7 px-2"
                >
                  Previous
                </Button>
                <span className="px-2 font-medium text-slate-700 dark:text-slate-300">
                  {page} / {totalPages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  className="text-xs h-7 px-2"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
