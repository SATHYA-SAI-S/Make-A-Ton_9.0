import React, { useState, useEffect } from "react";
import { apiRequest } from "../../api/client";
import { Plus, Layers, X } from "lucide-react";

export const CataloguePage: React.FC = () => {
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showProductModal, setShowProductModal] = useState<boolean>(false);
  const [showVariantModal, setShowVariantModal] = useState<boolean>(false);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(null);

  const [newProduct, setNewProduct] = useState({
    name: "",
    type: "service",
    sales_price: "",
    cost_price: "0.00",
    notes: "",
    currency: "INR",
  });

  const [newVariant, setNewVariant] = useState({
    name: "",
    price_adjustment: "0.00",
  });

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const data: any = await apiRequest("/products");
      setProducts(data || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const handleCreateProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await apiRequest("/products", {
        method: "POST",
        body: JSON.stringify(newProduct),
      });
      setShowProductModal(false);
      setNewProduct({
        name: "",
        type: "service",
        sales_price: "",
        cost_price: "0.00",
        notes: "",
        currency: "INR",
      });
      fetchProducts();
    } catch (err: any) {
      alert(err.message || "Failed to create product");
    }
  };

  const handleCreateVariant = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductId) return;
    try {
      await apiRequest(`/products/${selectedProductId}/variants`, {
        method: "POST",
        body: JSON.stringify(newVariant),
      });
      setShowVariantModal(false);
      setNewVariant({ name: "", price_adjustment: "0.00" });
      fetchProducts();
    } catch (err: any) {
      alert(err.message || "Failed to add variant");
    }
  };

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">Product Catalogue</h1>
          <p className="text-sm text-slate-500 mt-1">Configure offerings, base sales prices, and variant price adjustments</p>
        </div>
        <button
          onClick={() => setShowProductModal(true)}
          className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2.5 rounded-lg text-sm font-semibold transition-all shadow-md shadow-emerald-600/20"
        >
          <Plus size={16} />
          <span>New Product</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {loading ? (
          <div className="col-span-2 text-center py-12 text-slate-400">Loading catalogue...</div>
        ) : products.length === 0 ? (
          <div className="col-span-2 text-center py-12 text-slate-400">No products configured yet.</div>
        ) : (
          products.map((p) => {
            const basePrice = parseFloat(p.sales_price);
            return (
              <div key={p.id} className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm hover:border-slate-300 transition-all">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-xs font-bold text-emerald-600 uppercase tracking-wider">{p.type}</span>
                    <h3 className="text-lg font-bold text-slate-900 mt-0.5">{p.name}</h3>
                    <p className="text-xs text-slate-500 mt-1">{p.notes || "No description provided."}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-slate-400">Base Price</span>
                    <div className="text-xl font-extrabold text-slate-900">
                      ₹{parseFloat(p.sales_price).toLocaleString("en-IN", { minimumFractionDigits: 2 })}
                    </div>
                  </div>
                </div>

                <div className="mt-5 pt-4 border-t border-slate-100">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                      <Layers size={13} /> Variants & Price Adjustments
                    </h4>
                    <button
                      onClick={() => {
                        setSelectedProductId(p.id);
                        setShowVariantModal(true);
                      }}
                      className="text-xs font-semibold text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
                    >
                      <Plus size={12} /> Add Variant
                    </button>
                  </div>

                  {p.variants && p.variants.length > 0 ? (
                    <div className="space-y-2">
                      {p.variants.map((v: any) => {
                        const adj = parseFloat(v.price_adjustment);
                        const effective = basePrice + adj;
                        return (
                          <div
                            key={v.id}
                            className="flex items-center justify-between p-2.5 bg-slate-50 rounded-lg text-xs border border-slate-100"
                          >
                            <span className="font-semibold text-slate-800">{v.name}</span>
                            <div className="flex items-center gap-3">
                              <span className="text-slate-400 font-mono">
                                {adj >= 0 ? `+₹${adj.toFixed(2)}` : `-₹${Math.abs(adj).toFixed(2)}`}
                              </span>
                              <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200 font-mono">
                                Eff: ₹{effective.toFixed(2)}
                              </span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="text-xs text-slate-400 italic">No variants configured. Base price applies.</p>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Add Product Modal */}
      {showProductModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-slate-900">Create Product</h3>
              <button onClick={() => setShowProductModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreateProduct} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Product Name</label>
                <input
                  required
                  type="text"
                  value={newProduct.name}
                  onChange={(e) => setNewProduct({ ...newProduct, name: e.target.value })}
                  placeholder="Enterprise ERP Suite"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Sales Price (₹)</label>
                  <input
                    required
                    type="number"
                    step="0.01"
                    value={newProduct.sales_price}
                    onChange={(e) => setNewProduct({ ...newProduct, sales_price: e.target.value })}
                    placeholder="2000.00"
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Cost Price (₹)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={newProduct.cost_price}
                    onChange={(e) => setNewProduct({ ...newProduct, cost_price: e.target.value })}
                    placeholder="750.00"
                    className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Type</label>
                <select
                  value={newProduct.type}
                  onChange={(e) => setNewProduct({ ...newProduct, type: e.target.value })}
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                >
                  <option value="service">Service</option>
                  <option value="digital">Digital Product</option>
                  <option value="physical">Physical Product</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Notes</label>
                <textarea
                  rows={2}
                  value={newProduct.notes}
                  onChange={(e) => setNewProduct({ ...newProduct, notes: e.target.value })}
                  placeholder="Additional delivery or commercial details..."
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowProductModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium shadow-md shadow-emerald-600/20"
                >
                  Save Product
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Variant Modal */}
      {showVariantModal && (
        <div className="fixed inset-0 bg-slate-950/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between mb-5">
              <h3 className="text-lg font-bold text-slate-900">Add Product Variant</h3>
              <button onClick={() => setShowVariantModal(false)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>
            <form onSubmit={handleCreateVariant} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">Variant Name</label>
                <input
                  required
                  type="text"
                  value={newVariant.name}
                  onChange={(e) => setNewVariant({ ...newVariant, name: e.target.value })}
                  placeholder="Odoo Pro Edition"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1">
                  Price Adjustment (₹)
                </label>
                <input
                  required
                  type="number"
                  step="0.01"
                  value={newVariant.price_adjustment}
                  onChange={(e) => setNewVariant({ ...newVariant, price_adjustment: e.target.value })}
                  placeholder="560.00"
                  className="w-full px-3.5 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:border-emerald-500"
                />
                <p className="text-xs text-slate-400 mt-1">Delta relative to base price. Enter negative for discount.</p>
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowVariantModal(false)}
                  className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-sm font-medium shadow-md shadow-emerald-600/20"
                >
                  Add Variant
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
