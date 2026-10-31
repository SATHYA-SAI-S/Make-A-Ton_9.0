import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import { StatusBadge } from "../../components/StatusBadge";
import { useAuth } from "../../context/AuthContext";
import { Plus, X, Trash2 } from "lucide-react";

export const QuotationsPage: React.FC = () => {
  const { user } = useAuth();
  const isAdmin = user?.role === "admin";
  const [quotations, setQuotations] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [plans, setPlans] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showCreateModal, setShowCreateModal] = useState<boolean>(false);
  const [showExtendModal, setShowExtendModal] = useState<boolean>(false);
  const [selectedQuoteId, setSelectedQuoteId] = useState<string | null>(null);
  const [extendDays, setExtendDays] = useState<number>(30);
  const [extendReason, setExtendReason] = useState<string>("");

  // Builder State
  const [selectedCustomerId, setSelectedCustomerId] = useState<string>("");
  const [selectedPlanId, setSelectedPlanId] = useState<string>("");
  const [paymentTerms, setPaymentTerms] = useState<string>("Net 30");
  const [quoteLines, setQuoteLines] = useState<any[]>([
    { product_id: "", variant_id: "", quantity: 1 }
  ]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [qData, cData, pData, prData]: any = await Promise.all([
        apiRequest("/quotations"),
        apiRequest("/customers"),
        apiRequest("/plans"),
        apiRequest("/products"),
      ]);
      setQuotations(qData || []);
      setCustomers(cData.items || []);
      setPlans(pData || []);
      setProducts(prData || []);
      if (cData.items?.length > 0) setSelectedCustomerId(cData.items[0].id);
      if (pData?.length > 0) setSelectedPlanId(pData[0].id);
      if (prData?.length > 0) setQuoteLines([{ product_id: prData[0].id, variant_id: "", quantity: 1 }]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddLine = () => {
    if (products.length > 0) {
      setQuoteLines([...quoteLines, { product_id: products[0].id, variant_id: "", quantity: 1 }]);
    }
  };

  const handleRemoveLine = (index: number) => {
    if (quoteLines.length > 1) {
      setQuoteLines(quoteLines.filter((_, i) => i !== index));
    }
  };

  const handleLineChange = (index: number, field: string, value: any) => {
    const updated = [...quoteLines];
    updated[index][field] = value;
    if (field === "product_id") {
      updated[index]["variant_id"] = "";
    }
    setQuoteLines(updated);
  };

  // Compute live subtotal
  const computedSubtotal = quoteLines.reduce((acc, line) => {
    const prod = products.find((p) => p.id === line.product_id);
    if (!prod) return acc;
    let unit = parseFloat(prod.sales_price);
    if (line.variant_id) {
      const variant = prod.variants?.find((v: any) => v.id === line.variant_id);
      if (variant) unit += parseFloat(variant.price_adjustment);
    }
    return acc + unit * (line.quantity || 1);
  }, 0);

  const handleCreateQuotation = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload = {
        customer_id: selectedCustomerId,
        plan_id: selectedPlanId,
        payment_terms: paymentTerms,
        validity_days: 30,
        currency: "INR",
        lines: quoteLines.map((l) => ({
          product_id: l.product_id,
          variant_id: l.variant_id || null,
          quantity: parseInt(l.quantity, 10),
        })),
      };

      await apiRequest("/quotations", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setShowCreateModal(false);
      fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to create quotation");
    }
  };

  const handleConfirm = async (quoteId: string) => {
    if (!confirm("Confirm this quotation and generate an active subscription?")) return;
    try {
      await apiRequest(`/quotations/${quoteId}/confirm`, { method: "POST" });
      alert("Quotation successfully confirmed! Subscription created.");
      fetchData();
    } catch (err: any) {
      alert(err.message || "Confirmation failed");
    }
  };

  const handleSend = async (quoteId: string) => {
    try {
      await apiRequest(`/quotations/${quoteId}/send`, { method: "POST" });
      fetchData();
    } catch (err: any) {
      alert(err.message || "Send failed");
    }
  };

  const handleExtend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedQuoteId) return;
    try {
      await apiRequest(`/quotations/${selectedQuoteId}/extend-validity`, {
        method: "POST",
        body: JSON.stringify({ additional_days: extendDays, reason: extendReason }),
      });
      setShowExtendModal(false);
      setSelectedQuoteId(null);
      setExtendReason("");
      fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to extend validity");
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Quotations & Commercial Offers</h1>
          <p className="text-sm text-slate-500 mt-1">Generate proposals with dynamic snapshots and convert into subscriptions</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md shadow-emerald-600/20"
        >
          <Plus size={16} />
          <span>New Quotation</span>
        </button>
      </div>

      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <table className="w-full text-left text-sm text-slate-600">
          <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <tr>
              <th className="px-6 py-4">Quote Number</th>
              <th className="px-6 py-4">Customer</th>
              <th className="px-6 py-4">Valid Until</th>
              <th className="px-6 py-4">Total Amount</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-slate-400">Loading quotations...</td>
              </tr>
            ) : quotations.length === 0 ? (
              <tr>
                <td colSpan={6} className="text-center py-8 text-slate-400">No quotations found.</td>
              </tr>
            ) : (
              quotations.map((q) => {
                const customer = customers.find((c) => c.id === q.customer_id);
                return (
                  <tr key={q.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-6 py-4 font-mono font-bold text-slate-900">{q.number}</td>
                    <td className="px-6 py-4">
                      <div className="font-semibold text-slate-900">{customer?.name || "Client"}</div>
                      <div className="text-xs text-slate-400">{q.payment_terms}</div>
                    </td>
                    <td className="px-6 py-4 text-xs">
                      <span className={new Date(q.valid_until) < new Date() ? "text-rose-600 font-semibold" : "text-slate-600"}>
                        {q.valid_until}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono font-bold text-slate-900">
                      ₹{parseFloat(q.total).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={q.status} />
                    </td>
                    <td className="px-6 py-4 text-right space-x-2">
                      {q.status === "draft" && (
                        <button
                          onClick={() => handleSend(q.id)}
                          className="px-2.5 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-md transition-colors"
                        >
                          Send
                        </button>
                      )}
                      {(q.status === "draft" || q.status === "sent") && (
                        <button
                          onClick={() => handleConfirm(q.id)}
                          className="px-2.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold rounded-md transition-colors shadow-sm"
                        >
                          Confirm & Bill
                        </button>
                      )}
                      {q.status === "expired" && isAdmin && (
                        <button
                          onClick={() => {
                            setSelectedQuoteId(q.id);
                            setShowExtendModal(true);
                          }}
                          className="px-2.5 py-1.5 bg-amber-500 hover:bg-amber-400 text-white text-xs font-semibold rounded-md transition-colors"
                        >
                          Extend Validity
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Live Quotation Builder Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="text-lg font-bold text-slate-900">Create Quotation</h3>
                <p className="text-xs text-slate-500">Snapshots live product and variant prices into commercial terms</p>
              </div>
              <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreateQuotation} className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Select Customer</label>
                  <select
                    value={selectedCustomerId}
                    onChange={(e) => setSelectedCustomerId(e.target.value)}
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  >
                    {customers.map((c) => (
                      <option key={c.id} value={c.id}>{c.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Assigned Plan</label>
                  <select
                    value={selectedPlanId}
                    onChange={(e) => setSelectedPlanId(e.target.value)}
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  >
                    {plans.map((p) => (
                      <option key={p.id} value={p.id}>{p.name} ({p.billing_frequency} - Min Qty: {p.min_quantity})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Payment Terms</label>
                <input
                  type="text"
                  value={paymentTerms}
                  onChange={(e) => setPaymentTerms(e.target.value)}
                  placeholder="Net 30, Due Upon Receipt"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>

              {/* Line items builder */}
              <div className="pt-2">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Quotation Line Items</h4>
                  <button
                    type="button"
                    onClick={handleAddLine}
                    className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
                  >
                    <Plus size={13} /> Add Line
                  </button>
                </div>

                <div className="space-y-2">
                  {quoteLines.map((line, idx) => {
                    const prod = products.find((p) => p.id === line.product_id);
                    return (
                      <div key={idx} className="flex items-center gap-2 p-3 bg-slate-50 border border-slate-200 rounded-xl">
                        <div className="flex-1">
                          <select
                            value={line.product_id}
                            onChange={(e) => handleLineChange(idx, "product_id", e.target.value)}
                            className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-md text-xs focus:outline-none focus:border-emerald-500"
                          >
                            {products.map((p) => (
                              <option key={p.id} value={p.id}>{p.name} (Base ₹{p.sales_price})</option>
                            ))}
                          </select>
                        </div>

                        {prod?.variants && prod.variants.length > 0 && (
                          <div className="flex-1">
                            <select
                              value={line.variant_id}
                              onChange={(e) => handleLineChange(idx, "variant_id", e.target.value)}
                              className="w-full px-2.5 py-1.5 bg-white border border-slate-200 rounded-md text-xs focus:outline-none focus:border-emerald-500"
                            >
                              <option value="">Base Product (No Variant)</option>
                              {prod.variants.map((v: any) => (
                                <option key={v.id} value={v.id}>
                                  {v.name} (+₹{v.price_adjustment})
                                </option>
                              ))}
                            </select>
                          </div>
                        )}

                        <div className="w-20">
                          <input
                            type="number"
                            min="1"
                            value={line.quantity}
                            onChange={(e) => handleLineChange(idx, "quantity", e.target.value)}
                            className="w-full px-2 py-1.5 bg-white border border-slate-200 rounded-md text-xs text-center focus:outline-none focus:border-emerald-500"
                          />
                        </div>

                        {quoteLines.length > 1 && (
                          <button
                            type="button"
                            onClick={() => handleRemoveLine(idx)}
                            className="text-slate-400 hover:text-rose-500 p-1"
                          >
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Live Total Display */}
              <div className="mt-4 p-4 bg-slate-900 text-white rounded-xl flex items-center justify-between">
                <span className="text-sm font-semibold">Total Estimated Amount</span>
                <span className="text-xl font-mono font-extrabold text-emerald-400">
                  ₹{computedSubtotal.toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                </span>
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
                  Create Quotation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Admin Extend Validity Modal */}
      {showExtendModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-900 mb-1">Extend Quotation Validity</h3>
            <p className="text-xs text-slate-500 mb-4">
              Authorized admin action to extend an expired quotation so it can be confirmed.
            </p>
            <form onSubmit={handleExtend} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Additional Days</label>
                <input
                  type="number"
                  min="1"
                  max="365"
                  value={extendDays}
                  onChange={(e) => setExtendDays(parseInt(e.target.value, 10))}
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Reason for Extension</label>
                <textarea
                  required
                  rows={2}
                  value={extendReason}
                  onChange={(e) => setExtendReason(e.target.value)}
                  placeholder="Client procurement approval delay..."
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowExtendModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-amber-500 hover:bg-amber-400 text-white rounded-lg text-sm font-medium shadow-md shadow-amber-500/20"
                >
                  Extend Validity
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
