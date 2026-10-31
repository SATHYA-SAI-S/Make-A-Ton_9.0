import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import {
  Users,
  ShieldCheck,
  Package,
  Calendar,
  FileText,
  Repeat,
  CheckCircle2,
  PauseCircle,
  XCircle,
  ArrowRight,
  Database,
  Activity,
  Layers
} from "lucide-react";

interface AdminStats {
  total_customers: number;
  total_staff: number;
  total_products: number;
  total_plans: number;
  total_quotations: number;
  total_subscriptions: number;
  active_subscriptions: number;
  paused_subscriptions: number;
  closed_subscriptions: number;
}

interface AdminDashboardProps {
  onNavigate: (tab: string) => void;
}

export const AdminDashboard: React.FC<AdminDashboardProps> = ({ onNavigate }) => {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      setLoading(true);
      setError(null);
      const data: any = await apiRequest("/admin/stats");
      setStats(data);
    } catch (err: any) {
      setError(err.message || "Failed to load admin statistics.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Admin Executive Overview</h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-200">
              Admin Role Active
            </span>
          </div>
          <p className="text-sm text-slate-500">
            Real-time telemetry and management controls for catalogue, customers, quotations, and subscriptions
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchStats}
            className="px-3.5 py-2 text-xs font-medium bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 rounded-lg shadow-sm transition-colors flex items-center gap-1.5"
          >
            <Activity size={14} className="text-emerald-600" /> Refresh Telemetry
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-sm">
          {error}
        </div>
      )}

      {/* KPI Stat Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Customers */}
        <div
          onClick={() => onNavigate("customers")}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Customers</span>
            <Users size={18} className="text-emerald-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {loading ? "..." : stats?.total_customers ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            View directory <ArrowRight size={10} />
          </p>
        </div>

        {/* Staff Members */}
        <div
          onClick={() => onNavigate("staff")}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Staff</span>
            <ShieldCheck size={18} className="text-indigo-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {loading ? "..." : stats?.total_staff ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            Manage staff <ArrowRight size={10} />
          </p>
        </div>

        {/* Products */}
        <div
          onClick={() => onNavigate("catalogue")}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Products</span>
            <Package size={18} className="text-amber-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {loading ? "..." : stats?.total_products ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            Catalogue & variants <ArrowRight size={10} />
          </p>
        </div>

        {/* Plans */}
        <div
          onClick={() => onNavigate("plans")}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Plans</span>
            <Calendar size={18} className="text-sky-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {loading ? "..." : stats?.total_plans ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            Pricing tiers <ArrowRight size={10} />
          </p>
        </div>

        {/* Quotations */}
        <div
          onClick={() => onNavigate("quotations")}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Quotes</span>
            <FileText size={18} className="text-purple-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {loading ? "..." : stats?.total_quotations ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            Sales pipeline <ArrowRight size={10} />
          </p>
        </div>

        {/* Total Subscriptions */}
        <div
          onClick={() => onNavigate("subscriptions")}
          className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Subscriptions</span>
            <Repeat size={18} className="text-emerald-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono">
            {loading ? "..." : stats?.total_subscriptions ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1">
            Lifecycle engine <ArrowRight size={10} />
          </p>
        </div>
      </div>

      {/* Subscription Breakdown Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-emerald-700">Active Subscriptions</p>
            <p className="text-3xl font-extrabold text-slate-900 font-mono mt-1">
              {loading ? "..." : stats?.active_subscriptions ?? 0}
            </p>
            <p className="text-xs text-slate-500 mt-1">Generating recurring billing cycles</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <CheckCircle2 size={26} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-amber-700">Paused Subscriptions</p>
            <p className="text-3xl font-extrabold text-slate-900 font-mono mt-1">
              {loading ? "..." : stats?.paused_subscriptions ?? 0}
            </p>
            <p className="text-xs text-slate-500 mt-1">Temporarily suspended by policy</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center">
            <PauseCircle size={26} />
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-slate-600">Closed Subscriptions</p>
            <p className="text-3xl font-extrabold text-slate-900 font-mono mt-1">
              {loading ? "..." : stats?.closed_subscriptions ?? 0}
            </p>
            <p className="text-xs text-slate-500 mt-1">Terminated or expired contracts</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center">
            <XCircle size={26} />
          </div>
        </div>
      </div>

      {/* Quick Access Action Hub */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 mb-4">Core Management Fast Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigate("quotations")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl shadow-sm hover:shadow-lg transition-all group"
          >
            <FileText size={24} className="text-emerald-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Create New Quotation</h3>
            <p className="text-xs text-slate-300 mt-1">
              Generate quotation with line item snapshots and expiration date.
            </p>
          </button>

          <button
            onClick={() => onNavigate("catalogue")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl shadow-sm hover:shadow-lg transition-all group"
          >
            <Package size={24} className="text-amber-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Add Catalogue Product</h3>
            <p className="text-xs text-slate-300 mt-1">
              Define product SKUs, attributes, and variant price adjustments.
            </p>
          </button>

          <button
            onClick={() => onNavigate("staff")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl shadow-sm hover:shadow-lg transition-all group"
          >
            <ShieldCheck size={24} className="text-indigo-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Provision Staff Member</h3>
            <p className="text-xs text-slate-300 mt-1">
              Create and manage operational staff credentials (Admin only).
            </p>
          </button>
        </div>
      </div>

      {/* Inter-Service Contract Architecture Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 text-white">
        <div className="flex items-center gap-3 mb-4">
          <Database className="text-emerald-400" size={20} />
          <div>
            <h3 className="text-base font-bold">Monolith Architecture & Team Inter-Service Contracts</h3>
            <p className="text-xs text-slate-400">Status of Person 1 contracts serving Person 2 & Person 3</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
            <span className="font-bold text-emerald-400 flex items-center gap-1.5 mb-1">
              <Layers size={14} /> Person 1 (Core Module)
            </span>
            <p className="text-slate-300">
              Owns Identity, RBAC, Customer Master, Catalogue, Plans with Price Versions, Quotations, and Subscriptions State Machine.
            </p>
          </div>

          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
            <span className="font-bold text-sky-400 flex items-center gap-1.5 mb-1">
              <Repeat size={14} /> Person 2 Contract (Billing)
            </span>
            <p className="text-slate-300 font-mono text-[11px]">
              GET /api/v1/internal/subscriptions/due
            </p>
            <p className="text-slate-400 mt-1">
              Guarded by <code className="text-sky-300">X-Internal-Service-Key</code>. Clamps month-end dates (Jan 31 → Feb 28).
            </p>
          </div>

          <div className="p-4 bg-slate-950/60 rounded-xl border border-slate-800">
            <span className="font-bold text-purple-400 flex items-center gap-1.5 mb-1">
              <Activity size={14} /> Person 3 Contract (Analytics)
            </span>
            <p className="text-slate-300 font-mono text-[11px]">
              table: subscription_events
            </p>
            <p className="text-slate-400 mt-1">
              Event audit trail recording all lifecycle transitions with actor ID, status diffs, and UTC timestamps.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
