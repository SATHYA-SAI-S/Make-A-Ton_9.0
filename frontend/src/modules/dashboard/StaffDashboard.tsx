import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import {
  Users,
  Package,
  Calendar,
  FileText,
  Repeat,
  ArrowRight,
  ShieldAlert,
  ClipboardList,
  CheckCircle
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
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-6 border-b border-slate-200">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Staff Operations Center</h1>
            <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-200">
              Staff Member Role
            </span>
          </div>
          <p className="text-sm text-slate-500">
            Operational workspace for customer quoting, subscription lifecycle, and customer management
          </p>
        </div>
      </div>

      {/* Operational Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div
          onClick={() => onNavigate("quotations")}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:border-blue-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Quotations Desk</span>
            <FileText size={20} className="text-blue-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {loading ? "..." : quotationsCount}
          </div>
          <p className="text-xs text-slate-500 mt-1">Quotes created and awaiting confirmation</p>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-blue-600 font-medium">
            <span>Manage Quotations</span>
            <ArrowRight size={14} />
          </div>
        </div>

        <div
          onClick={() => onNavigate("subscriptions")}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:border-emerald-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Active Subscriptions</span>
            <Repeat size={20} className="text-emerald-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {loading ? "..." : subscriptionsCount}
          </div>
          <p className="text-xs text-slate-500 mt-1">Active customer recurring contracts</p>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-emerald-600 font-medium">
            <span>Inspect Subscriptions</span>
            <ArrowRight size={14} />
          </div>
        </div>

        <div
          onClick={() => onNavigate("customers")}
          className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:border-indigo-300 hover:shadow-md transition-all cursor-pointer group"
        >
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider text-slate-500">Customer Directory</span>
            <Users size={20} className="text-indigo-600 group-hover:scale-110 transition-transform" />
          </div>
          <div className="text-3xl font-extrabold text-slate-900 font-mono">
            {loading ? "..." : customersCount}
          </div>
          <p className="text-xs text-slate-500 mt-1">Total registered customer organizations</p>
          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-indigo-600 font-medium">
            <span>Open Directory</span>
            <ArrowRight size={14} />
          </div>
        </div>
      </div>

      {/* Staff Operational Playbook */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-4">
            <ClipboardList className="text-blue-600" size={18} />
            Staff Operational Responsibilities
          </h2>
          <ul className="space-y-3 text-sm text-slate-600">
            <li className="flex items-start gap-2.5">
              <CheckCircle size={16} className="text-emerald-600 mt-0.5 shrink-0" />
              <span><strong>Quotation Pipeline:</strong> Build and draft quotations for customers, configure discount policies, and confirm quotes into active recurring subscriptions.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle size={16} className="text-emerald-600 mt-0.5 shrink-0" />
              <span><strong>Subscription Lifecycle:</strong> Execute pause, resume, renewal, and early close operations according to plan policy flags.</span>
            </li>
            <li className="flex items-start gap-2.5">
              <CheckCircle size={16} className="text-emerald-600 mt-0.5 shrink-0" />
              <span><strong>Catalogue Navigation:</strong> Inspect products, attributes, variants, and active recurring pricing tiers.</span>
            </li>
          </ul>
        </div>

        {/* RBAC Boundaries Alert */}
        <div className="bg-slate-50 border border-slate-200 rounded-2xl p-6 shadow-sm">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-4">
            <ShieldAlert className="text-amber-600" size={18} />
            Role-Based Access Boundaries
          </h2>
          <p className="text-sm text-slate-600 mb-3">
            In accordance with SubscriptIQ security rules and the Hackathon Person 1 specification:
          </p>
          <div className="space-y-2 text-xs text-slate-500">
            <div className="p-2.5 bg-white rounded-lg border border-slate-200 flex items-center justify-between">
              <span>Staff Provisioning (`/api/v1/staff`)</span>
              <span className="font-semibold text-rose-600">Admin Only (403 Forbidden)</span>
            </div>
            <div className="p-2.5 bg-white rounded-lg border border-slate-200 flex items-center justify-between">
              <span>System Telemetry & Metrics (`/api/v1/admin/stats`)</span>
              <span className="font-semibold text-rose-600">Admin Only (403 Forbidden)</span>
            </div>
            <div className="p-2.5 bg-white rounded-lg border border-slate-200 flex items-center justify-between">
              <span>Customer Self-Service Portal (`/portal`)</span>
              <span className="font-semibold text-slate-600">Customer Role Only</span>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Launch Buttons */}
      <div>
        <h2 className="text-lg font-bold text-slate-900 mb-4">Quick Navigation</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <button
            onClick={() => onNavigate("quotations")}
            className="p-4 bg-white border border-slate-200 hover:border-blue-400 rounded-xl shadow-sm text-left transition-all group"
          >
            <FileText size={20} className="text-blue-600 mb-2 group-hover:scale-110 transition-transform" />
            <p className="text-sm font-bold text-slate-900">Quotations</p>
            <p className="text-xs text-slate-400 mt-0.5">Draft & confirm quotes</p>
          </button>

          <button
            onClick={() => onNavigate("subscriptions")}
            className="p-4 bg-white border border-slate-200 hover:border-emerald-400 rounded-xl shadow-sm text-left transition-all group"
          >
            <Repeat size={20} className="text-emerald-600 mb-2 group-hover:scale-110 transition-transform" />
            <p className="text-sm font-bold text-slate-900">Subscriptions</p>
            <p className="text-xs text-slate-400 mt-0.5">Lifecycle state machine</p>
          </button>

          <button
            onClick={() => onNavigate("catalogue")}
            className="p-4 bg-white border border-slate-200 hover:border-amber-400 rounded-xl shadow-sm text-left transition-all group"
          >
            <Package size={20} className="text-amber-600 mb-2 group-hover:scale-110 transition-transform" />
            <p className="text-sm font-bold text-slate-900">Catalogue</p>
            <p className="text-xs text-slate-400 mt-0.5">Products and variants</p>
          </button>

          <button
            onClick={() => onNavigate("plans")}
            className="p-4 bg-white border border-slate-200 hover:border-sky-400 rounded-xl shadow-sm text-left transition-all group"
          >
            <Calendar size={20} className="text-sky-600 mb-2 group-hover:scale-110 transition-transform" />
            <p className="text-sm font-bold text-slate-900">Plans</p>
            <p className="text-xs text-slate-400 mt-0.5">Recurring billing tiers</p>
          </button>
        </div>
      </div>
    </div>
  );
};
