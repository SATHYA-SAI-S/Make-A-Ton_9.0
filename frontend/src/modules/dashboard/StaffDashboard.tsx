import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import { FintechSphere3D } from "../../components/3d/FintechSphere3D";
import {
  Users,
  Package,
  FileText,
  Repeat,
  ArrowRight,
  ShieldAlert,
  ClipboardList,
  ExternalLink,
  Activity
} from "lucide-react";

interface StaffDashboardProps {
  onNavigate: (tab: string) => void;
}

export const StaffDashboard: React.FC<StaffDashboardProps> = ({ onNavigate }) => {
  const [quotationsCount, setQuotationsCount] = useState<number>(0);
  const [subscriptionsCount, setSubscriptionsCount] = useState<number>(0);
  const [customersCount, setCustomersCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchStaffData = async () => {
    try {
      setLoading(true);
      const [quotes, subs, custs]: any = await Promise.all([
        apiRequest("/quotations"),
        apiRequest("/subscriptions"),
        apiRequest("/customers"),
      ]);
      setQuotationsCount(quotes?.length || 0);
      setSubscriptionsCount(subs?.length || 0);
      setCustomersCount(custs?.length || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaffData();
  }, []);

  return (
    <div className="p-6 lg:p-8 max-w-7xl mx-auto space-y-8 text-slate-100">
      {/* 3D Operations Header Banner */}
      <div className="relative rounded-3xl bg-gradient-to-r from-slate-900/90 via-slate-900/70 to-slate-950/90 border border-slate-800/80 p-6 lg:p-8 shadow-2xl backdrop-blur-xl overflow-hidden">
        <div className="absolute top-0 right-1/4 w-80 h-80 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-3 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
              Staff Operations Console • Active Duty
            </div>
            <h1 className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight">
              Customer Quotes & <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400">
                Subscription Operations
              </span>
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              Staff workspace for building quotations with snapshot line pricing, executing subscription lifecycle transitions (pause, resume, close), and customer management.
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <button
                onClick={fetchStaffData}
                className="px-4 py-2 text-xs font-medium bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl shadow-lg shadow-cyan-600/20 transition-all flex items-center gap-2 active:scale-95"
              >
                <Activity size={14} className={loading ? "animate-spin" : ""} /> Refresh Workspace
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
            <FintechSphere3D className="w-full h-full" accentColor="cyan" />
            <div className="absolute bottom-2 right-3 text-[10px] font-mono text-slate-500 pointer-events-none">
              Operations Telemetry 3D
            </div>
          </div>
        </div>
      </div>

      {/* Operational Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          onClick={() => onNavigate("quotations")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-6 rounded-2xl border border-slate-800 hover:border-cyan-500/40 shadow-lg hover:shadow-cyan-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Quotations Desk</span>
            <FileText size={20} className="text-cyan-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono">
            {loading ? "..." : quotationsCount}
          </div>
          <p className="text-xs text-slate-400 mt-1">Quotes created and awaiting confirmation</p>
          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-cyan-400 font-medium group-hover:text-cyan-300">
            <span>Manage Quotations</span>
            <ArrowRight size={14} />
          </div>
        </div>

        <div
          onClick={() => onNavigate("subscriptions")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-6 rounded-2xl border border-slate-800 hover:border-emerald-500/40 shadow-lg hover:shadow-emerald-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Active Subscriptions</span>
            <Repeat size={20} className="text-emerald-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono">
            {loading ? "..." : subscriptionsCount}
          </div>
          <p className="text-xs text-slate-400 mt-1">Active customer recurring contracts</p>
          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-emerald-400 font-medium group-hover:text-emerald-300">
            <span>Inspect Subscriptions</span>
            <ArrowRight size={14} />
          </div>
        </div>

        <div
          onClick={() => onNavigate("customers")}
          className="bg-slate-900/60 hover:bg-slate-900/90 p-6 rounded-2xl border border-slate-800 hover:border-indigo-500/40 shadow-lg hover:shadow-indigo-500/5 transition-all cursor-pointer group backdrop-blur-md"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Customer Accounts</span>
            <Users size={20} className="text-indigo-400 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-white font-mono">
            {loading ? "..." : customersCount}
          </div>
          <p className="text-xs text-slate-400 mt-1">Total active customer profiles</p>
          <div className="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between text-xs text-indigo-400 font-medium group-hover:text-indigo-300">
            <span>Search Customer Directory</span>
            <ArrowRight size={14} />
          </div>
        </div>
      </div>

      {/* Staff Operational Quick Tasks */}
      <div>
        <h2 className="text-lg font-bold text-white mb-4">Operations Fast Actions</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigate("quotations")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 hover:border-cyan-500/40 rounded-2xl shadow-lg transition-all group backdrop-blur-md"
          >
            <ClipboardList size={24} className="text-cyan-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Issue Customer Quotation</h3>
            <p className="text-xs text-slate-400 mt-1">
              Select customer, plan, and product variants to create a formal quotation.
            </p>
          </button>

          <button
            onClick={() => onNavigate("catalogue")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 hover:border-amber-500/40 rounded-2xl shadow-lg transition-all group backdrop-blur-md"
          >
            <Package size={24} className="text-amber-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Inspect Catalogue & Variants</h3>
            <p className="text-xs text-slate-400 mt-1">
              Check dynamic variant adjustments and base product pricing.
            </p>
          </button>

          <button
            onClick={() => onNavigate("subscriptions")}
            className="p-5 text-left bg-gradient-to-br from-slate-900 to-slate-950 border border-slate-800 hover:border-emerald-500/40 rounded-2xl shadow-lg transition-all group backdrop-blur-md"
          >
            <Repeat size={24} className="text-emerald-400 mb-3 group-hover:scale-110 transition-transform" />
            <h3 className="font-semibold text-white">Subscription Lifecycle</h3>
            <p className="text-xs text-slate-400 mt-1">
              Manage transitions: pause with reason, resume, or execute early closure.
            </p>
          </button>
        </div>
      </div>

      {/* Security & RBAC Boundary Banner */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md shadow-lg">
        <div className="flex items-start gap-4">
          <div className="p-3 bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 rounded-xl mt-0.5">
            <ShieldAlert size={22} />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-white">Role-Based Security Boundary (Staff Level)</h3>
            <p className="text-xs text-slate-400 mt-1 leading-relaxed">
              As a staff member, you have access to create and confirm customer quotations, manage catalogue items, and execute allowed subscription transitions. Staff management and user provisioning are restricted to Administrator accounts.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
