import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import { FintechSphere3D } from "../../components/3d/FintechSphere3D";
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
  Layers,
  Sparkles,
  ExternalLink
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
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 text-slate-100">
      {/* 3D Interactive Telemetry Hero Header */}
      <div className="relative rounded-3xl bg-gradient-to-r from-slate-900/90 via-slate-900/70 to-slate-950/90 border border-slate-800/80 p-6 lg:p-8 shadow-2xl backdrop-blur-xl overflow-hidden">
        {/* Subtle background glow */}
        <div className="absolute top-0 right-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-3 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              SubscriptIQ Core Engine • Admin Telemetry
            </div>
            <h1 className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Enterprise Subscription <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400">
                Command & Telemetry
              </span>
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              Real-time synchronization across identity RBAC, customer ledger, catalogue pricing versions, quotation lifecycles, and recurring billing contracts.
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <button
                onClick={fetchStats}
                className="px-4 py-2 text-xs font-medium bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl shadow-lg shadow-emerald-600/20 transition-all flex items-center gap-2 active:scale-95"
              >
                <Activity size={14} className={loading ? "animate-spin" : ""} /> Refresh Telemetry
              </button>
              <a
                href="http://127.0.0.1:8025"
                target="_blank"
                rel="noreferrer"
                className="px-4 py-2 text-xs font-mono text-slate-300 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/80 rounded-xl transition-colors flex items-center gap-1.5"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" /> Mailpit :8025 <ExternalLink size={12} />
              </a>
            </div>
          </div>

          {/* Interactive 3D Sphere Widget */}
          <div className="w-full lg:w-72 h-56 lg:h-64 relative rounded-2xl bg-slate-950/60 border border-slate-800/80 overflow-hidden shadow-inner flex items-center justify-center">
            <FintechSphere3D className="w-full h-full" accentColor="emerald" />
            <div className="absolute bottom-2 right-3 text-[10px] font-mono text-slate-500 pointer-events-none">
              Interactive 3D Node Mesh
            </div>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-500/10 border border-rose-500/20 rounded-2xl text-rose-400 text-sm">
          {error}
        </div>
      )}

      {/* KPI Stat Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {/* Customers */}
        <div
          onClick={() => onNavigate("customers")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-5 rounded-2xl border border-slate-800 hover:border-emerald-500/40 shadow-lg hover:shadow-emerald-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Customers</span>
            <Users size={18} className="text-emerald-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {loading ? "..." : stats?.total_customers ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1 group-hover:text-emerald-400 transition-colors">
            Directory <ArrowRight size={10} />
          </p>
        </div>

        {/* Staff Members */}
        <div
          onClick={() => onNavigate("staff")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-5 rounded-2xl border border-slate-800 hover:border-indigo-500/40 shadow-lg hover:shadow-indigo-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Staff</span>
            <ShieldCheck size={18} className="text-indigo-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {loading ? "..." : stats?.total_staff ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1 group-hover:text-indigo-400 transition-colors">
            RBAC users <ArrowRight size={10} />
          </p>
        </div>

        {/* Products */}
        <div
          onClick={() => onNavigate("catalogue")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-5 rounded-2xl border border-slate-800 hover:border-amber-500/40 shadow-lg hover:shadow-amber-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Products</span>
            <Package size={18} className="text-amber-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {loading ? "..." : stats?.total_products ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1 group-hover:text-amber-400 transition-colors">
            Variants <ArrowRight size={10} />
          </p>
        </div>

        {/* Plans */}
        <div
          onClick={() => onNavigate("plans")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-5 rounded-2xl border border-slate-800 hover:border-sky-500/40 shadow-lg hover:shadow-sky-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Plans</span>
            <Calendar size={18} className="text-sky-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {loading ? "..." : stats?.total_plans ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1 group-hover:text-sky-400 transition-colors">
            Price tiers <ArrowRight size={10} />
          </p>
        </div>

        {/* Quotations */}
        <div
          onClick={() => onNavigate("quotations")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-5 rounded-2xl border border-slate-800 hover:border-purple-500/40 shadow-lg hover:shadow-purple-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Quotes</span>
            <FileText size={18} className="text-purple-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {loading ? "..." : stats?.total_quotations ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1 group-hover:text-purple-400 transition-colors">
            Pipeline <ArrowRight size={10} />
          </p>
        </div>

        {/* Total Subscriptions */}
        <div
          onClick={() => onNavigate("subscriptions")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-5 rounded-2xl border border-slate-800 hover:border-emerald-500/40 shadow-lg hover:shadow-emerald-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Subscriptions</span>
            <Repeat size={18} className="text-emerald-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">
            {loading ? "..." : stats?.total_subscriptions ?? 0}
          </div>
          <p className="text-[11px] text-slate-400 mt-1 flex items-center gap-1 group-hover:text-emerald-400 transition-colors">
            Lifecycle <ArrowRight size={10} />
          </p>
        </div>
      </div>

      {/* Subscription Breakdown Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-2xl shadow-lg flex items-center justify-between backdrop-blur-md relative overflow-hidden group hover:border-emerald-500/30 transition-all">
          <div className="absolute top-0 right-0 w-32 h-32 bg-emerald-500/5 rounded-full blur-2xl pointer-events-none" />
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-emerald-400 font-mono">Active Subscriptions</p>
            <p className="text-3xl font-extrabold text-white font-mono mt-2">
              {loading ? "..." : stats?.active_subscriptions ?? 0}
            </p>
            <p className="text-xs text-slate-400 mt-1">Generating recurring billing cycles</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center shadow-inner">
            <CheckCircle2 size={24} />
          </div>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-2xl shadow-lg flex items-center justify-between backdrop-blur-md relative overflow-hidden group hover:border-amber-500/30 transition-all">
          <div className="absolute top-0 right-0 w-32 h-32 bg-amber-500/5 rounded-full blur-2xl pointer-events-none" />
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-amber-400 font-mono">Paused Subscriptions</p>
            <p className="text-3xl font-extrabold text-white font-mono mt-2">
              {loading ? "..." : stats?.paused_subscriptions ?? 0}
            </p>
            <p className="text-xs text-slate-400 mt-1">Temporarily suspended by policy</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-400 flex items-center justify-center shadow-inner">
            <PauseCircle size={24} />
          </div>
        </div>

        <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-2xl shadow-lg flex items-center justify-between backdrop-blur-md relative overflow-hidden group hover:border-slate-700 transition-all">
          <div>
            <p className="text-xs font-medium uppercase tracking-wider text-slate-400 font-mono">Closed Subscriptions</p>
            <p className="text-3xl font-extrabold text-white font-mono mt-2">
              {loading ? "..." : stats?.closed_subscriptions ?? 0}
            </p>
            <p className="text-xs text-slate-400 mt-1">Terminated or expired contracts</p>
          </div>
          <div className="w-12 h-12 rounded-xl bg-slate-800/80 border border-slate-700 text-slate-400 flex items-center justify-center">
            <XCircle size={24} />
          </div>
        </div>
      </div>

      {/* Quick Access Action Hub */}
      <div>
        <h2 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
          <Sparkles size={18} className="text-emerald-400" />
          <span>Core Management Action Hub</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigate("quotations")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 hover:border-emerald-500/40 rounded-2xl shadow-lg transition-all group backdrop-blur-md"
          >
            <FileText size={24} className="text-emerald-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Create New Quotation</h3>
            <p className="text-xs text-slate-400 mt-1">
              Generate quotation with snapshot pricing, taxes, and expiration dates.
            </p>
          </button>

          <button
            onClick={() => onNavigate("customers")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 hover:border-indigo-500/40 rounded-2xl shadow-lg transition-all group backdrop-blur-md"
          >
            <Users size={24} className="text-indigo-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Register New Customer</h3>
            <p className="text-xs text-slate-400 mt-1">
              Onboard corporate or individual clients with billing profiles.
            </p>
          </button>

          <button
            onClick={() => onNavigate("plans")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 hover:border-sky-500/40 rounded-2xl shadow-lg transition-all group backdrop-blur-md"
          >
            <Layers size={24} className="text-sky-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Configure Plans & Tiers</h3>
            <p className="text-xs text-slate-400 mt-1">
              Define billing cadences, pause allowances, and immutable price versions.
            </p>
          </button>
        </div>
      </div>

      {/* Inter-Service Contract Live Status (Person 2 & Person 3) */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-lg">
        <div className="flex items-center gap-2 mb-4">
          <Database size={18} className="text-emerald-400" />
          <h2 className="text-base font-bold text-white">Cross-Module Integration Health (Person 2 & Person 3)</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Person 2: Recurring Billing Engine Contract</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">READY</span>
            </div>
            <p className="text-xs text-slate-400">
              Internal contract endpoint <code className="text-emerald-400 font-mono">/api/v1/internal/subscriptions/due</code> is frozen and authenticated via service key.
            </p>
          </div>

          <div className="p-4 bg-slate-950/60 border border-slate-800/80 rounded-xl space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs font-semibold text-slate-300">Person 3: Finance Analytics Engine Readiness</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">READY</span>
            </div>
            <p className="text-xs text-slate-400">
              Audit logs in <code className="text-emerald-400 font-mono">subscription_events</code> and versioned prices in <code className="text-emerald-400 font-mono">plan_versions</code> are indexed for MRR/ARR analytics.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
