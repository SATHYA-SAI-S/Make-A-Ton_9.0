import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import { StatusBadge } from "../../components/StatusBadge";
import { FintechSphere3D } from "../../components/3d/FintechSphere3D";
import { Calendar, Receipt, ExternalLink, Activity } from "lucide-react";

export const CustomerPortalPage: React.FC = () => {
  const [profile, setProfile] = useState<any | null>(null);
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [invoices, setInvoices] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [profData, subData]: any = await Promise.all([
        apiRequest("/customers/me"),
        apiRequest("/subscriptions/me"),
      ]);
      setProfile(profData);
      setSubscriptions(subData || []);

      // Attempt to load Person 2 invoices if available, otherwise graceful fallback
      try {
        const invData: any = await apiRequest("/invoices");
        setInvoices(invData.items || invData || []);
      } catch (_) {
        setInvoices([]);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="p-6 lg:p-8 max-w-6xl mx-auto space-y-8 text-slate-100">
      {/* 3D Customer Portal Hero Banner */}
      <div className="relative rounded-3xl bg-gradient-to-r from-slate-900/90 via-slate-900/70 to-slate-950/90 border border-slate-800/80 p-6 lg:p-8 shadow-2xl backdrop-blur-xl overflow-hidden">
        <div className="absolute top-0 right-1/4 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
          <div className="space-y-3 max-w-xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-mono">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
              Customer Self-Service Portal • Active Entitlements
            </div>
            <h1 className="text-3xl lg:text-4xl font-extrabold text-white tracking-tight leading-tight">
              {profile?.name || "Customer Account"} <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 via-sky-300 to-emerald-400">
                Subscription Center
              </span>
            </h1>
            <p className="text-sm text-slate-400 leading-relaxed">
              Manage your active recurring plans, review term renewals, and inspect invoices and payment receipts in real time.
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-3">
              <button
                onClick={fetchData}
                className="px-4 py-2 text-xs font-medium bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl shadow-lg shadow-indigo-600/20 transition-all flex items-center gap-2 active:scale-95"
              >
                <Activity size={14} className={loading ? "animate-spin" : ""} /> Refresh Status
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
            <FintechSphere3D className="w-full h-full" accentColor="indigo" />
            <div className="absolute bottom-2 right-3 text-[10px] font-mono text-slate-500 pointer-events-none">
              Entitlement Shield 3D
            </div>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading your account details...</div>
      ) : (
        <div className="space-y-8">
          {/* Profile Overview Card */}
          <div className="bg-slate-900/70 border border-slate-800 rounded-2xl p-6 shadow-xl backdrop-blur-md">
            <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
              <div>
                <div className="flex items-center gap-3">
                  <h2 className="text-xl font-bold text-white">{profile?.name || "Customer Account"}</h2>
                  <StatusBadge status={profile?.status || "active"} />
                </div>
                <p className="text-xs text-slate-400 mt-1">{profile?.email} • {profile?.phone || "No phone provided"}</p>
                <p className="text-xs text-slate-400 mt-0.5">Billing Contact: <span className="text-slate-300">{profile?.billing_contact}</span></p>
              </div>
              <div className="text-left sm:text-right text-xs text-slate-400 font-mono space-y-0.5">
                <div>Tax ID: <span className="font-semibold text-slate-200">{profile?.tax_id || "Unregistered"}</span></div>
                <div>Timezone: <span className="text-slate-300">{profile?.timezone}</span></div>
                <div>Country: <span className="text-slate-300">{profile?.country}</span></div>
              </div>
            </div>
          </div>

          {/* Subscriptions Section */}
          <div>
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Calendar size={18} className="text-emerald-400" />
              <span>Your Subscriptions ({subscriptions.length})</span>
            </h3>

            {subscriptions.length === 0 ? (
              <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-8 text-center text-slate-400 text-sm">
                You do not have any active subscriptions yet. Quotations confirmed by staff will appear here.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {subscriptions.map((s) => (
                  <div key={s.id} className="bg-slate-900/70 border border-slate-800 hover:border-emerald-500/40 rounded-2xl p-5 shadow-lg backdrop-blur-md transition-all group">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-mono font-bold text-sm text-white group-hover:text-emerald-400 transition-colors">
                        {s.subscription_number}
                      </span>
                      <StatusBadge status={s.status} />
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-300">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Term Duration:</span>
                        <span className="font-mono text-slate-200">{s.start_date} to {s.end_date}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Next Renewal / Bill:</span>
                        <span className="font-bold text-emerald-400 font-mono">
                          {s.next_billing_at || "N/A"}
                        </span>
                      </div>
                      <div className="flex justify-between pt-2 border-t border-slate-800">
                        <span className="text-slate-400 font-medium">Recurring Amount:</span>
                        <span className="font-extrabold text-white font-mono text-sm">
                          ₹{parseFloat(s.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Invoices Section (Person 2 Integration) */}
          <div>
            <h3 className="text-base font-bold text-white mb-4 flex items-center gap-2">
              <Receipt size={18} className="text-cyan-400" />
              <span>Invoices & Statements</span>
            </h3>

            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 text-center shadow-lg backdrop-blur-md">
              <Receipt size={32} className="mx-auto text-slate-600 mb-2" />
              <p className="text-sm font-semibold text-white">Invoices & Payment Records ({invoices.length})</p>
              <p className="text-xs text-slate-400 mt-1 max-w-md mx-auto">
                Connected to Person 2 Billing Module API (<code className="text-cyan-400 font-mono">/api/v1/invoices</code>). Billing runs executed against due subscriptions will automatically post invoices here.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
