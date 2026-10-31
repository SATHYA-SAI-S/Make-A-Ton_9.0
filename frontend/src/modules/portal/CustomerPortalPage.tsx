import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import { StatusBadge } from "../../components/StatusBadge";
import { Calendar, Receipt } from "lucide-react";

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
    <div className="p-8 max-w-6xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Customer Self-Service Portal</h1>
        <p className="text-sm text-slate-500 mt-1">Review your active subscriptions, renewal dates, and billing history</p>
      </div>

      {loading ? (
        <div className="text-center py-12 text-slate-400">Loading your account details...</div>
      ) : (
        <div className="space-y-8">
          {/* Profile Overview Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h2 className="text-xl font-bold text-slate-900">{profile?.name || "Customer Account"}</h2>
                  <StatusBadge status={profile?.status || "active"} />
                </div>
                <p className="text-xs text-slate-500 mt-1">{profile?.email} • {profile?.phone || "No phone provided"}</p>
                <p className="text-xs text-slate-400 mt-0.5">Billing Contact: {profile?.billing_contact}</p>
              </div>
              <div className="text-right text-xs text-slate-500 font-mono">
                <div>Tax ID: <span className="font-semibold text-slate-700">{profile?.tax_id || "Unregistered"}</span></div>
                <div>Timezone: {profile?.timezone}</div>
              </div>
            </div>
          </div>

          {/* Subscriptions Section */}
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Calendar size={18} className="text-emerald-600" />
              <span>Your Subscriptions</span>
            </h3>

            {subscriptions.length === 0 ? (
              <div className="bg-white border border-slate-200 rounded-xl p-8 text-center text-slate-400 text-sm">
                You do not have any subscriptions active yet.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {subscriptions.map((s) => (
                  <div key={s.id} className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-mono font-bold text-sm text-slate-900">{s.subscription_number}</span>
                      <StatusBadge status={s.status} />
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-600">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Term Duration:</span>
                        <span className="font-medium text-slate-800">{s.start_date} to {s.end_date}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Next Renewal / Bill:</span>
                        <span className="font-bold text-emerald-600 font-mono">
                          {s.next_billing_at || "N/A"}
                        </span>
                      </div>
                      <div className="flex justify-between pt-2 border-t border-slate-100">
                        <span className="text-slate-500 font-semibold">Recurring Commitment:</span>
                        <span className="font-extrabold text-slate-900 font-mono text-sm">
                          ₹{parseFloat(s.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Invoices Section (Person 2 Integration Placeholder) */}
          <div>
            <h3 className="text-base font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Receipt size={18} className="text-emerald-600" />
              <span>Invoices & Statements</span>
            </h3>

            <div className="bg-white border border-slate-200 rounded-xl p-6 text-center shadow-sm">
              <Receipt size={32} className="mx-auto text-slate-300 mb-2" />
              <p className="text-sm font-semibold text-slate-700">Invoices & Payment Records ({invoices.length})</p>
              <p className="text-xs text-slate-400 mt-1">
                Connected to Person 2 Billing Module API (`/api/v1/invoices`). Invoices will reflect here automatically once issued.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
