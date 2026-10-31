import React, { useState, useEffect, useCallback } from 'react';
import {
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle,
  XCircle,
  Eye,
  Clock,
  Layers,
  ArrowRight,
  Filter,
  DollarSign,
  Info,
  CheckCircle2,
  ChevronRight,
  History,
  FileText
} from 'lucide-react';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Modal } from '@/shared/ui/Modal';
import { Input } from '@/shared/ui/Input';
import { guardianApi } from '../../api/guardianApi';
import {
  GuardianDashboardData,
  RiskAlertItem,
  RiskSeverity,
  RiskCategory,
  RiskStatus,
  RiskDetectionRunItem
} from '../../types/guardian';

export const RevenueGuardianDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<GuardianDashboardData | null>(null);
  const [alerts, setAlerts] = useState<RiskAlertItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [runningDetection, setRunningDetection] = useState<boolean>(false);
  const [detectionSuccess, setDetectionSuccess] = useState<string | null>(null);

  // Filters
  const [selectedSeverity, setSelectedSeverity] = useState<string>('ALL');
  const [selectedStatus, setSelectedStatus] = useState<string>('OPEN');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');

  // Action Modal
  const [selectedAlert, setSelectedAlert] = useState<RiskAlertItem | null>(null);
  const [actionType, setActionType] = useState<'RESOLVE' | 'DISMISS' | null>(null);
  const [actionNote, setActionNote] = useState<string>('');
  const [submittingAction, setSubmittingAction] = useState<boolean>(false);

  // Detail Modal
  const [detailAlert, setDetailAlert] = useState<RiskAlertItem | null>(null);
  const [isRunsModalOpen, setIsRunsModalOpen] = useState<boolean>(false);

  const fetchDashboardAndAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const [dash, alertRes] = await Promise.all([
        guardianApi.getDashboard(),
        guardianApi.listAlerts({
          severity: selectedSeverity !== 'ALL' ? selectedSeverity : undefined,
          status: selectedStatus !== 'ALL' ? selectedStatus : undefined,
          category: selectedCategory !== 'ALL' ? selectedCategory : undefined,
          page_size: 50,
        }),
      ]);
      setDashboardData(dash);
      setAlerts(alertRes.items);
    } catch (err) {
      console.error('Failed to load guardian dashboard', err);
    } finally {
      setLoading(false);
    }
  }, [selectedSeverity, selectedStatus, selectedCategory]);

  useEffect(() => {
    fetchDashboardAndAlerts();
  }, [fetchDashboardAndAlerts]);

  const handleRunDetection = async () => {
    try {
      setRunningDetection(true);
      setDetectionSuccess(null);
      const run = await guardianApi.triggerDetectionRun();
      setDetectionSuccess(`Detection cycle completed! ${run.alerts_created} new alert(s) detected across ${run.rules_run} rules.`);
      await fetchDashboardAndAlerts();
      setTimeout(() => setDetectionSuccess(null), 4000);
    } catch (err) {
      console.error('Failed to run detection cycle', err);
    } finally {
      setRunningDetection(false);
    }
  };

  const handleQuickAcknowledge = async (alertId: string) => {
    try {
      await guardianApi.executeAlertAction(alertId, 'ACKNOWLEDGE');
      await fetchDashboardAndAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert', err);
    }
  };

  const handleConfirmAction = async () => {
    if (!selectedAlert || !actionType) return;
    try {
      setSubmittingAction(true);
      await guardianApi.executeAlertAction(selectedAlert.id, actionType, actionNote);
      setSelectedAlert(null);
      setActionType(null);
      setActionNote('');
      await fetchDashboardAndAlerts();
    } catch (err) {
      console.error(`Failed to ${actionType} alert`, err);
    } finally {
      setSubmittingAction(false);
    }
  };

  const summary = dashboardData?.summary;

  const getSeverityBadge = (sev: RiskSeverity) => {
    switch (sev) {
      case 'CRITICAL':
        return <Badge variant="danger" className="bg-rose-600 text-white font-bold">CRITICAL</Badge>;
      case 'HIGH':
        return <Badge variant="warning" className="bg-amber-600 text-white font-bold">HIGH</Badge>;
      case 'MEDIUM':
        return <Badge variant="warning" className="bg-yellow-500 text-white">MEDIUM</Badge>;
      case 'LOW':
        return <Badge variant="default" className="bg-blue-500 text-white">LOW</Badge>;
    }
  };

  const getStatusBadge = (st: RiskStatus) => {
    switch (st) {
      case 'OPEN':
        return <Badge variant="danger" className="text-xs">OPEN</Badge>;
      case 'ACKNOWLEDGED':
        return <Badge variant="warning" className="text-xs">ACKNOWLEDGED</Badge>;
      case 'RESOLVED':
        return <Badge variant="success" className="text-xs">RESOLVED</Badge>;
      case 'DISMISSED':
        return <Badge variant="default" className="text-xs text-slate-500">DISMISSED</Badge>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner & Trigger Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
              <ShieldAlert className="h-7 w-7 text-rose-600 dark:text-rose-500" />
              Revenue Guardian
            </h1>
            <Badge variant="danger" className="text-xs font-mono tracking-wider">
              Autonomous Risk Engine
            </Badge>
          </div>
          <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
            Autonomous 8-rule revenue protection, duplicate invoice prevention, and audited triage workflows
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setIsRunsModalOpen(true)}
            className="text-xs"
          >
            <History className="h-4 w-4 mr-1 text-slate-500" />
            Detection Runs ({dashboardData?.recent_runs.length || 0})
          </Button>

          <Button
            variant="primary"
            size="sm"
            onClick={handleRunDetection}
            disabled={runningDetection}
            className="text-xs bg-rose-600 hover:bg-rose-700 text-white"
          >
            <Play className={`h-3.5 w-3.5 mr-1.5 ${runningDetection ? 'animate-spin' : ''}`} />
            {runningDetection ? 'Scanning 8 Rules...' : 'Run Detection Cycle'}
          </Button>
        </div>
      </div>

      {/* Detection Success Toast / Alert */}
      {detectionSuccess && (
        <div className="rounded-xl border border-emerald-300 bg-emerald-50 p-4 dark:border-emerald-800 dark:bg-emerald-950/30 flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-sm text-emerald-900 dark:text-emerald-200 font-medium">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <span>{detectionSuccess}</span>
          </div>
          <button onClick={() => setDetectionSuccess(null)} className="text-emerald-700 hover:text-emerald-900 text-xs font-bold">
            Dismiss
          </button>
        </div>
      )}

      {/* KPI Highlight Strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="p-3.5 bg-rose-50/40 dark:bg-rose-950/20 border-rose-200 dark:border-rose-900/40">
          <p className="text-xs font-semibold text-rose-700 dark:text-rose-400 uppercase tracking-wider">
            Total Open Alerts
          </p>
          <p className="text-2xl font-bold text-rose-950 dark:text-rose-200 mt-1">
            {summary?.total_open_alerts ?? 0}
          </p>
          <span className="text-[11px] text-rose-600 font-medium">Active Unresolved</span>
        </Card>

        <Card className="p-3.5 bg-red-50/50 dark:bg-red-950/30 border-red-300 dark:border-red-900/50">
          <p className="text-xs font-semibold text-red-700 dark:text-red-400 uppercase tracking-wider">
            Critical Alerts
          </p>
          <p className="text-2xl font-bold text-red-950 dark:text-red-200 mt-1">
            {summary?.critical_count ?? 0}
          </p>
          <span className="text-[11px] text-red-600 font-medium">Immediate Action</span>
        </Card>

        <Card className="p-3.5 bg-amber-50/40 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800/40">
          <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
            High Severity
          </p>
          <p className="text-2xl font-bold text-amber-950 dark:text-amber-200 mt-1">
            {summary?.high_count ?? 0}
          </p>
          <span className="text-[11px] text-amber-600 font-medium">High Exposure</span>
        </Card>

        <Card className="p-3.5 bg-yellow-50/40 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-800/40">
          <p className="text-xs font-semibold text-yellow-700 dark:text-yellow-500 uppercase tracking-wider">
            Medium & Low
          </p>
          <p className="text-2xl font-bold text-yellow-950 dark:text-yellow-200 mt-1">
            {(summary?.medium_count ?? 0) + (summary?.low_count ?? 0)}
          </p>
          <span className="text-[11px] text-yellow-600 font-medium">Operational Triage</span>
        </Card>

        <Card className="p-3.5 bg-slate-50 dark:bg-slate-900 border-slate-200 dark:border-slate-800 col-span-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Estimated Financial Exposure
          </p>
          <p className="text-2xl font-bold text-slate-900 dark:text-white mt-1">
            ₹{summary ? parseFloat(summary.total_estimated_impact).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </p>
          <span className="text-[11px] text-slate-400">Total potential revenue leakage / mismatch</span>
        </Card>
      </div>

      {/* Filter Strip */}
      <Card className="p-4 border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs">
          {/* Status Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-500 uppercase tracking-wider mr-1">Status:</span>
            {['OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'DISMISSED', 'ALL'].map((st) => (
              <button
                key={st}
                onClick={() => setSelectedStatus(st)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                  selectedStatus === st
                    ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                }`}
              >
                {st}
              </button>
            ))}
          </div>

          {/* Severity Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-500 uppercase tracking-wider mr-1">Severity:</span>
            {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map((sev) => (
              <button
                key={sev}
                onClick={() => setSelectedSeverity(sev)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                  selectedSeverity === sev
                    ? 'bg-rose-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                }`}
              >
                {sev}
              </button>
            ))}
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-1.5">
            <span className="font-semibold text-slate-500 uppercase tracking-wider mr-1">Category:</span>
            {['ALL', 'BILLING', 'PAYMENT', 'SUBSCRIPTION', 'REVENUE'].map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                  selectedCategory === cat
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* Alerts Table / List */}
      <Card className="p-5 border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShieldCheck className="h-5 w-5 text-indigo-600" />
            <h3 className="font-bold text-slate-900 dark:text-white">
              Detected Anomalies & Risk Queue ({alerts.length})
            </h3>
          </div>
          <span className="text-xs text-slate-500">
            Sorted by Score & Estimated Financial Exposure
          </span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-xs text-slate-500">
            Loading Revenue Guardian queue...
          </div>
        ) : alerts.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-500 space-y-2">
            <ShieldCheck className="h-10 w-10 text-emerald-500 mx-auto" />
            <p className="font-semibold text-slate-800 dark:text-slate-200 text-sm">
              All Clear! No anomalies detected for current filter.
            </p>
            <p className="text-slate-400">
              Trigger a detection cycle above to scan for missed billings, duplicate invoices, or payment mismatches.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider font-semibold">
                  <th className="py-2.5 px-3">Severity / Rule</th>
                  <th className="py-2.5 px-3">Category</th>
                  <th className="py-2.5 px-3">Risk Score</th>
                  <th className="py-2.5 px-3">Estimated Impact</th>
                  <th className="py-2.5 px-3 w-1/3">Explanation & Suggested Action</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3 text-right">Triage Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60">
                {alerts.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-slate-50/60 dark:hover:bg-slate-800/30 transition-colors"
                  >
                    <td className="py-3 px-3">
                      <div className="flex flex-col gap-1 items-start">
                        {getSeverityBadge(a.severity)}
                        <span className="font-mono text-[11px] font-bold text-slate-900 dark:text-white">
                          {a.rule_key}
                        </span>
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      <span className="rounded bg-slate-100 dark:bg-slate-800 px-2 py-0.5 font-mono text-[11px] text-slate-700 dark:text-slate-300">
                        {a.category}
                      </span>
                    </td>

                    <td className="py-3 px-3">
                      <div className="flex items-center gap-1.5 font-mono">
                        <span className={`text-xs font-bold ${
                          a.score >= 80 ? 'text-rose-600' : a.score >= 60 ? 'text-amber-600' : 'text-blue-600'
                        }`}>
                          {a.score}
                        </span>
                        <span className="text-[10px] text-slate-400">/ 100</span>
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      <span className="font-mono font-bold text-sm text-slate-900 dark:text-white">
                        ₹{parseFloat(a.estimated_impact).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </td>

                    <td className="py-3 px-3">
                      <div className="space-y-1">
                        <p className="text-xs text-slate-800 dark:text-slate-200 font-medium">
                          {a.explanation}
                        </p>
                        <p className="text-[11px] text-indigo-600 dark:text-indigo-400 italic">
                          💡 Action: {a.suggested_action}
                        </p>
                        {a.resolution_note && (
                          <p className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                            ✓ Note: {a.resolution_note}
                          </p>
                        )}
                      </div>
                    </td>

                    <td className="py-3 px-3">
                      {getStatusBadge(a.status)}
                    </td>

                    <td className="py-3 px-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setDetailAlert(a)}
                          className="text-[11px] px-2 py-1"
                          title="Inspect Details"
                        >
                          <Eye className="h-3.5 w-3.5" />
                        </Button>

                        {a.status === 'OPEN' && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleQuickAcknowledge(a.id)}
                            className="text-[11px] px-2 py-1 text-amber-700 border-amber-300"
                          >
                            Ack
                          </Button>
                        )}

                        {a.status !== 'RESOLVED' && (
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => {
                              setSelectedAlert(a);
                              setActionType('RESOLVE');
                            }}
                            className="text-[11px] px-2 py-1 bg-emerald-600 hover:bg-emerald-700 text-white"
                          >
                            Resolve
                          </Button>
                        )}

                        {a.status !== 'DISMISSED' && a.status !== 'RESOLVED' && (
                          <button
                            onClick={() => {
                              setSelectedAlert(a);
                              setActionType('DISMISS');
                            }}
                            className="p-1 text-slate-400 hover:text-slate-600 rounded"
                            title="Dismiss Alert"
                          >
                            <XCircle className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Action Confirmation Modal (Resolve / Dismiss) */}
      <Modal
        isOpen={Boolean(selectedAlert && actionType)}
        onClose={() => {
          setSelectedAlert(null);
          setActionType(null);
          setActionNote('');
        }}
        title={`${actionType === 'RESOLVE' ? 'Resolve' : 'Dismiss'} Revenue Anomaly`}
        description={`Record corrective audit note for alert ${selectedAlert?.id.substring(0, 8)}...`}
      >
        <div className="space-y-4 py-2">
          <div className="rounded-lg bg-slate-50 dark:bg-slate-800/40 p-3 text-xs space-y-1.5">
            <p className="font-semibold text-slate-800 dark:text-slate-200">
              Rule: {selectedAlert?.rule_key} ({selectedAlert?.severity})
            </p>
            <p className="text-slate-600 dark:text-slate-400">{selectedAlert?.explanation}</p>
            <p className="text-indigo-600 font-medium">Recommended: {selectedAlert?.suggested_action}</p>
          </div>

          <div>
            <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
              Audit Resolution Note (Mandatory)
            </label>
            <textarea
              rows={3}
              value={actionNote}
              onChange={(e) => setActionNote(e.target.value)}
              placeholder="e.g. Verified invoice INV-2026-0041 was re-issued and reconciled in payment ledger."
              className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setSelectedAlert(null);
                setActionType(null);
              }}
            >
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleConfirmAction}
              disabled={submittingAction || !actionNote.trim()}
              className={actionType === 'RESOLVE' ? 'bg-emerald-600 hover:bg-emerald-700 text-white' : 'bg-slate-700 text-white'}
            >
              Confirm {actionType}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Alert Detail Slide-Over Modal */}
      <Modal
        isOpen={Boolean(detailAlert)}
        onClose={() => setDetailAlert(null)}
        title="Anomaly Diagnostic Detail"
        description={`Diagnostic breakdown for risk fingerprint ${detailAlert?.fingerprint}`}
        size="lg"
      >
        {detailAlert && (
          <div className="space-y-4 py-2 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg bg-slate-50 dark:bg-slate-800/40 p-3">
                <span className="text-slate-500 uppercase font-semibold text-[10px]">Rule Key</span>
                <p className="font-mono font-bold text-sm text-slate-900 dark:text-white mt-0.5">{detailAlert.rule_key}</p>
              </div>
              <div className="rounded-lg bg-slate-50 dark:bg-slate-800/40 p-3">
                <span className="text-slate-500 uppercase font-semibold text-[10px]">Estimated Exposure</span>
                <p className="font-mono font-bold text-sm text-rose-600 mt-0.5">₹{parseFloat(detailAlert.estimated_impact).toLocaleString('en-IN', { minimumFractionDigits: 2 })}</p>
              </div>
            </div>

            <div className="rounded-lg border border-slate-200 dark:border-slate-700 p-3 space-y-2">
              <h4 className="font-bold text-slate-900 dark:text-white">Root-Cause Analysis</h4>
              <p className="text-slate-700 dark:text-slate-300">{detailAlert.explanation}</p>
              <div className="pt-2 border-t text-indigo-600 dark:text-indigo-400 font-medium">
                Suggested Action: {detailAlert.suggested_action}
              </div>
            </div>

            <div className="rounded-lg bg-slate-50 dark:bg-slate-800/40 p-3 space-y-1 font-mono text-[11px]">
              <p className="font-semibold text-slate-700 dark:text-slate-300">Entity Soft References:</p>
              <p className="text-slate-500">Customer ID: {detailAlert.customer_id || 'None'}</p>
              <p className="text-slate-500">Subscription ID: {detailAlert.subscription_id || 'None'}</p>
              <p className="text-slate-500">Invoice ID: {detailAlert.invoice_id || 'None'}</p>
              <p className="text-slate-500">Payment ID: {detailAlert.payment_id || 'None'}</p>
            </div>

            <div className="flex justify-end pt-2">
              <Button variant="outline" size="sm" onClick={() => setDetailAlert(null)}>
                Close
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Detection Runs History Modal */}
      <Modal
        isOpen={isRunsModalOpen}
        onClose={() => setIsRunsModalOpen(false)}
        title="Detection Run History"
        description="Audit log of autonomous risk detection cycles executed by the system."
        size="lg"
      >
        <div className="space-y-3 py-2 max-h-96 overflow-y-auto">
          {(!dashboardData?.recent_runs || dashboardData.recent_runs.length === 0) ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No detection runs logged yet.
            </p>
          ) : (
            dashboardData.recent_runs.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 flex items-center justify-between text-xs font-mono"
              >
                <div>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      r.status === 'SUCCESS' ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {r.status}
                    </span>
                    <span className="font-bold text-slate-900 dark:text-white">Run {r.id.substring(0, 8)}</span>
                  </div>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Started: {new Date(r.started_at).toLocaleString()}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-slate-700 dark:text-slate-300 font-bold">{r.rules_run} Rules Executed</p>
                  <p className="text-rose-600 font-bold">{r.alerts_created} New Anomalies</p>
                </div>
              </div>
            ))
          )}
        </div>
      </Modal>
    </div>
  );
};
