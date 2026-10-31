import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import { StatusBadge } from "../../components/StatusBadge";
import { Eye, X } from "lucide-react";

export const SubscriptionsPage: React.FC = () => {
  const [subscriptions, setSubscriptions] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [selectedSub, setSelectedSub] = useState<any | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [showEventModal, setShowEventModal] = useState<boolean>(false);
  const [actionModal, setActionModal] = useState<{ type: string; subId: string } | null>(null);
  const [actionReason, setActionReason] = useState<string>("");

  const fetchSubscriptions = async () => {
    try {
      setLoading(true);
      const data: any = await apiRequest("/subscriptions");
      setSubscriptions(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubscriptions();
  }, []);

  const handleAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!actionModal) return;
    try {
      if (actionModal.type === "activate") {
        await apiRequest(`/subscriptions/${actionModal.subId}/activate`, { method: "POST" });
      } else {
        await apiRequest(`/subscriptions/${actionModal.subId}/${actionModal.type}`, {
          method: "POST",
          body: JSON.stringify({ reason: actionReason }),
        });
      }
      setActionModal(null);
      setActionReason("");
      fetchSubscriptions();
    } catch (err: any) {
      alert(err.message || "Action failed");
    }
  };

  const openEvents = async (sub: any) => {
    try {
      const data: any = await apiRequest(`/subscriptions/${sub.id}/events`);
      setEvents(data || []);
      setSelectedSub(sub);
      setShowEventModal(true);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Subscription Operations</h1>
          <p className="text-sm text-slate-500 mt-1">Lifecycle state transitions, audit event history, and recurring billing dates</p>
        </div>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4">Subscription No</th>
              <th className="px-6 py-4">Term Dates</th>
              <th className="px-6 py-4">Next Billing Date</th>
              <th className="px-6 py-4">Agreed Amount</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Lifecycle Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-slate-400">Loading subscriptions...</td>
              </tr>
            ) : subscriptions.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-slate-400">No subscriptions created yet.</td>
              </tr>
            ) : (
              subscriptions.map((s) => (
                <tr key={s.id} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-6 py-4 font-mono font-bold text-slate-900">{s.subscription_number}</td>
                  <td className="px-6 py-4 text-xs">
                    <div>Start: <span className="font-medium text-slate-700">{s.start_date}</span></div>
                    <div>End: <span className="font-medium text-slate-700">{s.end_date}</span></div>
                  </td>
                  <td className="px-6 py-4 text-xs font-medium">
                    {s.next_billing_at ? (
                      <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100 font-mono">
                        {s.next_billing_at}
                      </span>
                    ) : (
                      <span className="text-slate-400">None (Inactive)</span>
                    )}
                  </td>
                  <td className="px-6 py-4 font-mono font-bold text-slate-900">
                    ₹{parseFloat(s.total_amount).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </td>
                  <td className="px-6 py-4">
                    <StatusBadge status={s.status} />
                  </td>
                  <td className="px-6 py-4 text-right space-x-1.5">
                    {/* Event History */}
                    <button
                      onClick={() => openEvents(s)}
                      className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors"
                      title="View Event History"
                    >
                      <Eye size={16} />
                    </button>

                    {/* Activate */}
                    {s.status === "confirmed" && (
                      <button
                        onClick={() => setActionModal({ type: "activate", subId: s.id })}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-md shadow-sm"
                      >
                        Activate
                      </button>
                    )}

                    {/* Pause */}
                    {s.status === "active" && (
                      <button
                        onClick={() => setActionModal({ type: "pause", subId: s.id })}
                        className="px-2.5 py-1 bg-amber-500 hover:bg-amber-400 text-white text-xs font-semibold rounded-md"
                      >
                        Pause
                      </button>
                    )}

                    {/* Resume */}
                    {s.status === "paused" && (
                      <button
                        onClick={() => setActionModal({ type: "resume", subId: s.id })}
                        className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-md"
                      >
                        Resume
                      </button>
                    )}

                    {/* Renew */}
                    {s.status === "active" && (
                      <button
                        onClick={() => setActionModal({ type: "renew", subId: s.id })}
                        className="px-2.5 py-1 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-md"
                      >
                        Renew
                      </button>
                    )}

                    {/* Close */}
                    {(s.status === "active" || s.status === "paused") && (
                      <button
                        onClick={() => setActionModal({ type: "close", subId: s.id })}
                        className="px-2.5 py-1 bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold rounded-md"
                      >
                        Close
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Action Reason Modal */}
      {actionModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-1 capitalize">
              {actionModal.type} Subscription
            </h3>
            <p className="text-xs text-slate-500 mb-4">
              All state transitions are validated by plan rules and written to the immutable event log.
            </p>
            <form onSubmit={handleAction} className="space-y-4">
              {actionModal.type !== "activate" && (
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                    Transition Reason
                  </label>
                  <textarea
                    required
                    rows={2}
                    value={actionReason}
                    onChange={(e) => setActionReason(e.target.value)}
                    placeholder="Provide operational context..."
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
              )}
              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setActionModal(null)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium shadow-md shadow-emerald-600/20 capitalize"
                >
                  Confirm {actionModal.type}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Event Timeline Modal */}
      {showEventModal && selectedSub && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Event Audit Timeline</h3>
                <p className="text-xs text-slate-500">{selectedSub.subscription_number}</p>
              </div>
              <button onClick={() => setShowEventModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
              {events.map((ev: any) => (
                <div key={ev.id} className="p-3 bg-slate-50 rounded-xl border border-slate-100">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">
                      {ev.from_state} → {ev.to_state}
                    </span>
                    <span className="text-[10px] text-slate-400 font-mono">
                      {new Date(ev.created_at).toLocaleString()}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1">{ev.reason}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
