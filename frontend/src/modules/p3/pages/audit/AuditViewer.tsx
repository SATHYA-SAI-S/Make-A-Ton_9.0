import React, { useState, useEffect, useCallback } from 'react';
import {
  Shield,
  Search,
  Filter,
  Eye,
  Calendar,
  User,
  Clock,
  ArrowRight,
  RefreshCw,
  Tag,
  FileText,
  DollarSign,
  AlertTriangle,
  Layers,
  CheckCircle2,
  XCircle,
  Hash
} from 'lucide-react';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Modal } from '@/shared/ui/Modal';
import { auditApi } from '../../api/auditApi';
import { AuditLog, AuditFieldDiff } from '../../types/audit';

type AuditTab = 'all' | 'prices' | 'plans' | 'cancellations' | 'lifecycle';

export const AuditViewer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<AuditTab>('all');
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(20);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [entityType, setEntityType] = useState<string>('ALL');
  const [actorRole, setActorRole] = useState<string>('ALL');
  const [actionFilter, setActionFilter] = useState<string>('');
  const [entityIdFilter, setEntityIdFilter] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');

  // Selected Log for Diff Modal
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [logDetailLoading, setLogDetailLoading] = useState<boolean>(false);

  const fetchLogs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let resp;
      if (activeTab === 'prices') {
        resp = await auditApi.getPriceHistory({ page, page_size: pageSize });
      } else if (activeTab === 'plans') {
        resp = await auditApi.getPlanHistory({ page, page_size: pageSize });
      } else if (activeTab === 'cancellations') {
        resp = await auditApi.getInvoiceCancellations({ page, page_size: pageSize });
      } else if (activeTab === 'lifecycle') {
        resp = await auditApi.getSubscriptionLifecycle({ page, page_size: pageSize });
      } else {
        resp = await auditApi.getLogs({
          entity_type: entityType !== 'ALL' ? entityType : undefined,
          actor_role: actorRole !== 'ALL' ? actorRole : undefined,
          action: actionFilter || undefined,
          entity_id: entityIdFilter || undefined,
          start_date: startDate ? new Date(startDate).toISOString() : undefined,
          end_date: endDate ? new Date(endDate).toISOString() : undefined,
          page,
          page_size: pageSize,
        });
      }
      setLogs(resp.items);
      setTotal(resp.total);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch audit records');
    } finally {
      setLoading(false);
    }
  }, [activeTab, entityType, actorRole, actionFilter, entityIdFilter, startDate, endDate, page, pageSize]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  // Inspect specific log with complete field-level diff
  const handleInspectLog = async (logItem: AuditLog) => {
    setSelectedLog(logItem);
    setLogDetailLoading(true);
    try {
      const detail = await auditApi.getLogDetail(logItem.id);
      setSelectedLog(detail);
    } catch (err) {
      console.error('Failed to load log detail diff:', err);
    } finally {
      setLogDetailLoading(false);
    }
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
              Immutable Audit Log & Compliance Ledger
            </h1>
            <Badge variant="outline" className="text-xs font-mono uppercase bg-slate-50 dark:bg-slate-800">
              P3-T14
            </Badge>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Complete, tamper-evident audit trail with field-level delta diffing for compliance verification.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <Button
            variant="outline"
            onClick={fetchLogs}
            disabled={loading}
            className="flex items-center gap-2 text-xs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>Refresh Ledger</span>
          </Button>
        </div>
      </div>

      {/* Preset View Tabs */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-3">
        {[
          { id: 'all', label: 'All Audit Records', icon: Shield },
          { id: 'prices', label: 'Price Modification History', icon: DollarSign },
          { id: 'plans', label: 'Plan Configuration Changes', icon: Layers },
          { id: 'cancellations', label: 'Invoice Cancellations', icon: AlertTriangle },
          { id: 'lifecycle', label: 'Subscription Lifecycles', icon: Clock },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                setActiveTab(tab.id as AuditTab);
                setPage(1);
              }}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 dark:text-slate-400 dark:hover:text-white dark:hover:bg-slate-800'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Multi-Dimensional Filter Bar (Visible in 'all' view) */}
      {activeTab === 'all' && (
        <Card className="p-4 bg-slate-50/70 dark:bg-slate-900/40 border border-slate-200 dark:border-slate-800">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
            <div>
              <label className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
                Entity Type
              </label>
              <select
                value={entityType}
                onChange={(e) => {
                  setEntityType(e.target.value);
                  setPage(1);
                }}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:ring-1 focus:ring-indigo-500"
              >
                <option value="ALL">All Entities</option>
                <option value="subscription">Subscription</option>
                <option value="invoice">Invoice</option>
                <option value="plan">Plan</option>
                <option value="product">Product</option>
                <option value="payment">Payment</option>
                <option value="risk_alert">Risk Alert</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
                Actor Role
              </label>
              <select
                value={actorRole}
                onChange={(e) => {
                  setActorRole(e.target.value);
                  setPage(1);
                }}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 focus:ring-1 focus:ring-indigo-500"
              >
                <option value="ALL">All Roles</option>
                <option value="admin">Admin</option>
                <option value="staff">Staff</option>
                <option value="customer">Customer</option>
                <option value="system">System / Engine</option>
              </select>
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
                Action Filter
              </label>
              <input
                type="text"
                placeholder="e.g. cancelled, updated"
                value={actionFilter}
                onChange={(e) => {
                  setActionFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 placeholder:text-slate-400 focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div>
              <label className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block mb-1">
                Entity ID
              </label>
              <input
                type="text"
                placeholder="Search UUID..."
                value={entityIdFilter}
                onChange={(e) => {
                  setEntityIdFilter(e.target.value);
                  setPage(1);
                }}
                className="w-full px-2.5 py-1.5 text-xs rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-800 dark:text-slate-200 placeholder:text-slate-400 focus:ring-1 focus:ring-indigo-500"
              />
            </div>

            <div className="flex items-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setEntityType('ALL');
                  setActorRole('ALL');
                  setActionFilter('');
                  setEntityIdFilter('');
                  setStartDate('');
                  setEndDate('');
                  setPage(1);
                }}
                className="w-full text-xs h-[30px]"
              >
                Reset Filters
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Main Audit Records Table */}
      <div className="w-full overflow-hidden rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
            <thead className="bg-slate-50 dark:bg-slate-800/60 uppercase tracking-wider font-semibold text-slate-500 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800 text-[11px]">
              <tr>
                <th className="px-4 py-3 whitespace-nowrap">Timestamp</th>
                <th className="px-4 py-3 whitespace-nowrap">Actor</th>
                <th className="px-4 py-3 whitespace-nowrap">Action</th>
                <th className="px-4 py-3 whitespace-nowrap">Entity</th>
                <th className="px-4 py-3 whitespace-nowrap">Entity ID</th>
                <th className="px-4 py-3 whitespace-nowrap text-right">Inspection</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/80">
              {loading ? (
                Array.from({ length: 6 }).map((_, rIdx) => (
                  <tr key={`skel-${rIdx}`} className="animate-pulse">
                    <td colSpan={6} className="px-4 py-3.5">
                      <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-full"></div>
                    </td>
                  </tr>
                ))
              ) : logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-slate-400 dark:text-slate-500">
                    No audit records match the selected filter criteria.
                  </td>
                </tr>
              ) : (
                logs.map((log) => (
                  <tr
                    key={log.id}
                    className="hover:bg-slate-50/70 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <td className="px-4 py-3 whitespace-nowrap text-slate-500 font-mono text-[11px]">
                      {new Date(log.occurred_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span className="font-medium text-slate-900 dark:text-white">
                          {log.actor_id}
                        </span>
                        <Badge
                          variant={
                            log.actor_role === 'admin'
                              ? 'default'
                              : log.actor_role === 'system'
                              ? 'secondary'
                              : 'outline'
                          }
                          className="text-[9px] py-0 px-1 uppercase"
                        >
                          {log.actor_role}
                        </Badge>
                      </div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <Badge variant="outline" className="font-mono text-[10px] text-slate-700 dark:text-slate-300">
                        {log.action}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <span className="capitalize font-medium text-slate-700 dark:text-slate-300">
                        {log.entity_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap font-mono text-slate-400 text-[11px]">
                      {log.entity_id.length > 12 ? `${log.entity_id.slice(0, 12)}...` : log.entity_id}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap text-right">
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleInspectLog(log)}
                        className="text-xs h-7 px-2.5 text-indigo-600 hover:text-indigo-700 hover:bg-indigo-50 dark:text-indigo-400 dark:hover:bg-indigo-950/40"
                      >
                        <Eye className="w-3.5 h-3.5 mr-1" />
                        <span>Inspect Diff</span>
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {total > pageSize && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-900/50 text-xs text-slate-500 dark:text-slate-400">
            <div>
              Showing <span className="font-semibold">{(page - 1) * pageSize + 1}</span> to{' '}
              <span className="font-semibold">{Math.min(page * pageSize, total)}</span> of{' '}
              <span className="font-semibold">{total}</span> records
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

      {/* Visual Diff & Inspection Modal */}
      {selectedLog && (
        <Modal
          isOpen={true}
          onClose={() => setSelectedLog(null)}
          title={`Audit Record: ${selectedLog.action}`}
        >
          <div className="space-y-5 text-xs text-slate-700 dark:text-slate-300">
            {/* Meta summary */}
            <div className="grid grid-cols-2 gap-3 p-3 rounded-lg bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-800 text-[11px]">
              <div>
                <span className="text-slate-400 block">Record ID</span>
                <span className="font-mono text-slate-800 dark:text-slate-200 select-all">{selectedLog.id}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Timestamp (UTC)</span>
                <span className="font-mono text-slate-800 dark:text-slate-200">{selectedLog.occurred_at}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Actor ({selectedLog.actor_role})</span>
                <span className="font-semibold text-slate-900 dark:text-white">{selectedLog.actor_id}</span>
              </div>
              <div>
                <span className="text-slate-400 block">Target Entity</span>
                <span className="font-mono text-slate-900 dark:text-white">
                  {selectedLog.entity_type} ({selectedLog.entity_id})
                </span>
              </div>
            </div>

            {/* Field-level Delta Diff View (CHANGED FIELDS ONLY) */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <span className="font-semibold text-slate-900 dark:text-white text-xs uppercase tracking-wide">
                  Field-Level Delta (Changed Fields Only)
                </span>
                <Badge variant="outline" className="text-[10px]">
                  {selectedLog.diff ? `${Object.keys(selectedLog.diff).length} Fields Modified` : 'No State Changes'}
                </Badge>
              </div>

              {logDetailLoading ? (
                <div className="p-8 text-center text-slate-400">Computing field-level diff...</div>
              ) : selectedLog.diff && Object.keys(selectedLog.diff).length > 0 ? (
                <div className="divide-y divide-slate-200 dark:divide-slate-800 rounded-lg border border-slate-200 dark:border-slate-800 overflow-hidden bg-slate-50/50 dark:bg-slate-900">
                  {Object.entries(selectedLog.diff).map(([fieldName, delta]) => (
                    <div key={fieldName} className="p-3 grid grid-cols-1 md:grid-cols-3 gap-2 items-center">
                      <div className="font-mono font-medium text-slate-900 dark:text-white">
                        {fieldName}
                      </div>
                      <div className="p-2 rounded bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900/60 font-mono text-rose-700 dark:text-rose-300 break-all">
                        <span className="text-[10px] uppercase font-bold text-rose-500 block mb-0.5">Before:</span>
                        {delta.before !== null && delta.before !== undefined ? JSON.stringify(delta.before) : '— (null)'}
                      </div>
                      <div className="p-2 rounded bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-900/60 font-mono text-emerald-700 dark:text-emerald-300 break-all">
                        <span className="text-[10px] uppercase font-bold text-emerald-500 block mb-0.5">After:</span>
                        {delta.after !== null && delta.after !== undefined ? JSON.stringify(delta.after) : '— (null)'}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-4 rounded-lg border border-slate-200 dark:border-slate-800 text-center text-slate-500 text-xs">
                  This action did not mutate prior state (e.g. read event, initial creation without prior state, or immutable log).
                </div>
              )}
            </div>

            {/* Additional Metadata / Request ID */}
            {selectedLog.meta && Object.keys(selectedLog.meta).length > 0 && (
              <div>
                <span className="font-semibold text-slate-900 dark:text-white text-xs uppercase tracking-wide block mb-1">
                  Contextual Metadata
                </span>
                <pre className="p-3 rounded-lg bg-slate-100 dark:bg-slate-800 text-[11px] font-mono overflow-x-auto text-slate-800 dark:text-slate-200">
                  {JSON.stringify(selectedLog.meta, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <Button variant="outline" size="sm" onClick={() => setSelectedLog(null)}>
                Close Inspector
              </Button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
