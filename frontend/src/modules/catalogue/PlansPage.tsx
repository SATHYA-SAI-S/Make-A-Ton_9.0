import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import { StatusBadge } from "../../components/StatusBadge";
import { Plus, History, Check, X, ArrowUpRight } from "lucide-react";

export const PlansPage: React.FC = () => {
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showPriceModal, setShowPriceModal] = useState<boolean>(false);
  const [showHistoryModal, setShowHistoryModal] = useState<boolean>(false);
  const [selectedPlan, setSelectedPlan] = useState<any | null>(null);
  const [newPrice, setNewPrice] = useState<string>("");

  const [newPlan, setNewPlan] = useState({
    name: "",
    billing_frequency: "monthly",
    price: "",
    min_quantity: 1,
    available_from: new Date().toISOString().split("T")[0],
    available_to: new Date(Date.now() + 365 * 24 * 60 * 60 * 1000).toISOString().split("T")[0],
    allow_pause: true,
    allow_early_close: true,
    allow_renewal: true,
    status: "active",
  });

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const data: any = await apiRequest("/plans");
      setPlans(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPlans();
  }, []);

  const handleCreatePlan = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/plans", {
        method: "POST",
        body: JSON.stringify(newPlan),
      });
      setShowCreateModal(false);
      fetchPlans();
    } catch (err: any) {
      alert(err.message || "Failed to create plan");
    }
  };

  const handleUpdatePrice = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPlan) return;
    try {
      await apiRequest(`/plans/${selectedPlan.id}/price`, {
        method: "POST",
        body: JSON.stringify({ new_price: newPrice }),
      });
      setShowPriceModal(false);
      setNewPrice("");
      fetchPlans();
    } catch (err: any) {
      alert(err.message || "Failed to change price");
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Subscription Plans</h1>
          <p className="text-sm text-slate-500 mt-1">Configure frequencies, policies, and immutable price versions</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md shadow-emerald-600/20"
        >
          <Plus size={16} />
          <span>New Plan</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-3 text-center py-12 text-slate-400">Loading plans...</div>
        ) : plans.length === 0 ? (
          <div className="col-span-3 text-center py-12 text-slate-400">No subscription plans found.</div>
        ) : (
          plans.map((p) => (
            <div key={p.id} className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-100">
                    {p.billing_frequency}
                  </span>
                  <StatusBadge status={p.status} />
                </div>

                <h3 className="text-lg font-bold text-slate-900">{p.name}</h3>

                <div className="mt-4 flex items-baseline gap-1">
                  <span className="text-3xl font-extrabold text-slate-900">
                    ₹{parseFloat(p.current_price).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                  </span>
                  <span className="text-xs text-slate-400 font-medium">/ {p.billing_frequency}</span>
                </div>

                <div className="mt-1 flex items-center gap-1.5 text-xs text-slate-500">
                  <span className="font-semibold text-slate-700">Version {p.current_version_no}</span>
                  <span>•</span>
                  <span>Min Qty: {p.min_quantity}</span>
                </div>

                <div className="mt-5 space-y-2 border-t border-slate-100 pt-4 text-xs text-slate-600">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Availability</span>
                    <span className="font-medium text-slate-700">{p.available_from} to {p.available_to}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Pause Permitted</span>
                    <span>{p.allow_pause ? <Check size={14} className="text-emerald-500" /> : <X size={14} className="text-rose-400" />}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Early Close</span>
                    <span>{p.allow_early_close ? <Check size={14} className="text-emerald-500" /> : <X size={14} className="text-rose-400" />}</span>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Renewal Permitted</span>
                    <span>{p.allow_renewal ? <Check size={14} className="text-emerald-500" /> : <X size={14} className="text-rose-400" />}</span>
                  </div>
                </div>
              </div>

              <div className="mt-6 pt-4 border-t border-slate-100 flex items-center justify-between gap-2">
                <button
                  onClick={() => {
                    setSelectedPlan(p);
                    setShowPriceModal(true);
                  }}
                  className="flex-1 py-2 px-3 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold transition-colors flex items-center justify-center gap-1.5"
                >
                  <ArrowUpRight size={13} />
                  <span>Update Price</span>
                </button>
                <button
                  onClick={() => {
                    setSelectedPlan(p);
                    setShowHistoryModal(true);
                  }}
                  className="py-2 px-3 border border-slate-200 hover:bg-slate-50 text-slate-600 rounded-lg text-xs font-semibold transition-colors flex items-center gap-1"
                  title="View Price Version History"
                >
                  <History size={13} />
                  <span>History ({p.versions?.length || 1})</span>
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Create Plan Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-slate-900">Create Subscription Plan</h3>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreatePlan} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Plan Name</label>
                <input
                  required
                  type="text"
                  value={newPlan.name}
                  onChange={(e) => setNewPlan({ ...newPlan, name: e.target.value })}
                  placeholder="Enterprise Growth Suite"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Billing Frequency</label>
                  <select
                    value={newPlan.billing_frequency}
                    onChange={(e) => setNewPlan({ ...newPlan, billing_frequency: e.target.value })}
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  >
                    <option value="daily">Daily</option>
                    <option value="weekly">Weekly</option>
                    <option value="monthly">Monthly</option>
                    <option value="yearly">Yearly</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Initial Price (₹)</label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    value={newPlan.price}
                    onChange={(e) => setNewPlan({ ...newPlan, price: e.target.value })}
                    placeholder="4999.00"
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Available From</label>
                  <input
                    required
                    type="date"
                    value={newPlan.available_from}
                    onChange={(e) => setNewPlan({ ...newPlan, available_from: e.target.value })}
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Available To</label>
                  <input
                    required
                    type="date"
                    value={newPlan.available_to}
                    onChange={(e) => setNewPlan({ ...newPlan, available_to: e.target.value })}
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
              <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 space-y-2 text-xs">
                <label className="flex items-center gap-2 text-slate-700 font-medium">
                  <input
                    type="checkbox"
                    checked={newPlan.allow_pause}
                    onChange={(e) => setNewPlan({ ...newPlan, allow_pause: e.target.checked })}
                    className="rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  Allow Customer to Pause Subscription
                </label>
                <label className="flex items-center gap-2 text-slate-700 font-medium">
                  <input
                    type="checkbox"
                    checked={newPlan.allow_early_close}
                    onChange={(e) => setNewPlan({ ...newPlan, allow_early_close: e.target.checked })}
                    className="rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  Allow Early Closure Before End Date
                </label>
                <label className="flex items-center gap-2 text-slate-700 font-medium">
                  <input
                    type="checkbox"
                    checked={newPlan.allow_renewal}
                    onChange={(e) => setNewPlan({ ...newPlan, allow_renewal: e.target.checked })}
                    className="rounded text-emerald-600 focus:ring-emerald-500"
                  />
                  Allow Subscription Renewal
                </label>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium shadow-md shadow-emerald-600/20"
                >
                  Save Plan
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Change Price Modal */}
      {showPriceModal && selectedPlan && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Update Plan Price</h3>
            <p className="text-xs text-slate-500 mb-4">
              Updating the price creates an immutable <strong>Version {selectedPlan.current_version_no + 1}</strong>. Existing subscriptions will retain their current agreed price.
            </p>
            <form onSubmit={handleUpdatePrice} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">New Price (₹)</label>
                <input
                  required
                  type="number"
                  step="0.01"
                  value={newPrice}
                  onChange={(e) => setNewPrice(e.target.value)}
                  placeholder="5999.00"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowPriceModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium shadow-md shadow-emerald-600/20"
                >
                  Create New Version
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Version History Modal */}
      {showHistoryModal && selectedPlan && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Price Version History</h3>
                <p className="text-xs text-slate-500">{selectedPlan.name}</p>
              </div>
              <button onClick={() => setShowHistoryModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            <div className="space-y-2 max-h-72 overflow-y-auto pr-1">
              {selectedPlan.versions?.map((v: any) => (
                <div key={v.id} className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between">
                  <div>
                    <span className="text-xs font-bold text-slate-900">Version {v.version_no}</span>
                    <p className="text-[11px] text-slate-400">Effective: {new Date(v.effective_from).toLocaleDateString()}</p>
                  </div>
                  <span className="text-sm font-extrabold text-emerald-700 font-mono">
                    ₹{parseFloat(v.price).toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
