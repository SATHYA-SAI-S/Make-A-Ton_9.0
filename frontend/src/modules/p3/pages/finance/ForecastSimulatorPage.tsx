import React, { useState, useEffect, useCallback, useTransition } from 'react';
import {
  TrendingUp,
  Sliders,
  Save,
  RotateCcw,
  Sparkles,
  Calculator,
  AlertCircle,
  FolderOpen,
  Trash2,
  CheckCircle2,
  Info,
  Calendar,
  Layers,
  Percent,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';

import { Card } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';
import { Badge } from '@/shared/ui/Badge';
import { Modal } from '@/shared/ui/Modal';
import { Input } from '@/shared/ui/Input';
import { financeApi } from '../../api/financeApi';
import {
  ForecastAssumptions,
  ForecastSimulationResult,
  SavedForecastScenario,
  ForecastProjectionPoint
} from '../../types/finance';

const DEFAULT_ASSUMPTIONS: ForecastAssumptions = {
  new_growth_pct: 10.0,
  churn_pct: 3.0,
  expansion_pct: 2.0,
  contraction_pct: 1.0,
  collection_rate_pct: 92.0,
  price_increase_pct: 0.0,
  discount_pct: 0.0,
};

export const ForecastSimulatorPage: React.FC = () => {
  const [horizonMonths, setHorizonMonths] = useState<number>(12);
  const [assumptions, setAssumptions] = useState<ForecastAssumptions>(DEFAULT_ASSUMPTIONS);
  const [baselineAssumptions, setBaselineAssumptions] = useState<ForecastAssumptions | null>(null);
  const [simulationData, setSimulationData] = useState<ForecastSimulationResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [simulating, setSimulating] = useState<boolean>(false);
  const [isPending, startTransition] = useTransition();

  // Scenarios modal & saved list
  const [savedScenarios, setSavedScenarios] = useState<SavedForecastScenario[]>([]);
  const [isSaveModalOpen, setIsSaveModalOpen] = useState<boolean>(false);
  const [isLoadModalOpen, setIsLoadModalOpen] = useState<boolean>(false);
  const [scenarioName, setScenarioName] = useState<string>('');
  const [scenarioDescription, setScenarioDescription] = useState<string>('');
  const [saveSuccessMsg, setSaveSuccessMsg] = useState<string | null>(null);

  // Load initial baseline
  useEffect(() => {
    let isMounted = true;
    async function initBaseline() {
      try {
        setLoading(true);
        const res = await financeApi.getForecastBaselineDetailed(horizonMonths);
        if (isMounted) {
          setSimulationData(res);
          setBaselineAssumptions(res.baseline_assumptions);
          // initialize assumptions to baseline if available
          setAssumptions(res.baseline_assumptions || DEFAULT_ASSUMPTIONS);
        }
      } catch (err) {
        console.error('Failed to load baseline forecast', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }
    initBaseline();
    return () => {
      isMounted = false;
    };
  }, []);

  // Fetch saved scenarios
  const fetchScenarios = useCallback(async () => {
    try {
      const list = await financeApi.listForecastScenarios();
      setSavedScenarios(list);
    } catch (err) {
      console.error('Failed to fetch scenarios', err);
    }
  }, []);

  useEffect(() => {
    fetchScenarios();
  }, [fetchScenarios]);

  // Debounced run simulation
  useEffect(() => {
    if (loading) return;
    setSimulating(true);
    const handler = setTimeout(async () => {
      try {
        const res = await financeApi.simulateForecast({
          horizon_months: horizonMonths,
          assumptions,
        });
        startTransition(() => {
          setSimulationData(res);
        });
      } catch (err) {
        console.error('Simulation calculation failed', err);
      } finally {
        setSimulating(false);
      }
    }, 250);

    return () => clearTimeout(handler);
  }, [assumptions, horizonMonths, loading]);

  const updateAssumption = (key: keyof ForecastAssumptions, val: number) => {
    setAssumptions((prev) => ({
      ...prev,
      [key]: val,
    }));
  };

  const handleResetToBaseline = () => {
    if (baselineAssumptions) {
      setAssumptions(baselineAssumptions);
    } else {
      setAssumptions(DEFAULT_ASSUMPTIONS);
    }
  };

  const handleApplyPreset = (preset: 'aggressive' | 'conservative' | 'stress') => {
    if (preset === 'aggressive') {
      setAssumptions({
        new_growth_pct: 15.0,
        churn_pct: 2.0,
        expansion_pct: 5.0,
        contraction_pct: 0.5,
        collection_rate_pct: 95.0,
        price_increase_pct: 5.0,
        discount_pct: 0.0,
      });
    } else if (preset === 'conservative') {
      setAssumptions({
        new_growth_pct: 3.0,
        churn_pct: 3.5,
        expansion_pct: 1.0,
        contraction_pct: 1.5,
        collection_rate_pct: 90.0,
        price_increase_pct: 0.0,
        discount_pct: 0.0,
      });
    } else {
      setAssumptions({
        new_growth_pct: -2.0,
        churn_pct: 8.0,
        expansion_pct: 0.5,
        contraction_pct: 3.0,
        collection_rate_pct: 82.0,
        price_increase_pct: 0.0,
        discount_pct: 5.0,
      });
    }
  };

  const handleSaveScenario = async () => {
    if (!scenarioName.trim()) return;
    try {
      await financeApi.saveForecastScenario({
        name: scenarioName,
        description: scenarioDescription,
        horizon_months: horizonMonths,
        assumptions,
      });
      setSaveSuccessMsg('Scenario saved successfully!');
      fetchScenarios();
      setTimeout(() => {
        setSaveSuccessMsg(null);
        setIsSaveModalOpen(false);
        setScenarioName('');
        setScenarioDescription('');
      }, 1200);
    } catch (err) {
      console.error('Failed to save scenario', err);
    }
  };

  const handleLoadScenario = (sc: SavedForecastScenario) => {
    setHorizonMonths(sc.horizon_months);
    setAssumptions(sc.assumptions);
    setIsLoadModalOpen(false);
  };

  const handleDeleteScenario = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await financeApi.deleteForecastScenario(id);
      fetchScenarios();
    } catch (err) {
      console.error('Failed to delete scenario', err);
    }
  };

  // Combine baseline and projected curves for Recharts
  const chartData = (simulationData?.projection || []).map((proj, idx) => {
    const base = simulationData?.baseline[idx];
    return {
      month: proj.month,
      baseline_mrr: base ? parseFloat(base.mrr) : 0,
      projected_mrr: parseFloat(proj.mrr),
      projected_invoiced: parseFloat(proj.projected_invoiced),
      projected_collected: parseFloat(proj.projected_collected),
      projected_outstanding: parseFloat(proj.projected_outstanding),
      step_explanation: proj.step_explanation,
    };
  });

  const summary = simulationData?.summary;

  return (
    <div className="space-y-6">
      {/* Non-Destructive Banner */}
      <div className="rounded-xl border border-amber-300 bg-amber-50 p-4 dark:border-amber-800/60 dark:bg-amber-950/30">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-amber-500/20 text-amber-600 dark:text-amber-400">
              <Sparkles className="h-5 w-5" />
            </span>
            <div>
              <div className="flex items-center gap-2">
                <h4 className="font-semibold text-amber-950 dark:text-amber-200">
                  Simulation & Scenario Sandbox
                </h4>
                <Badge variant="warning" className="text-xs uppercase tracking-wider font-mono">
                  Projection Model
                </Badge>
              </div>
              <p className="text-xs text-amber-800/90 dark:text-amber-300/80 mt-0.5">
                All metrics and curves on this page represent non-destructive mathematical what-if models.
                Simulated values are never written to live financial transactions or accounting ledgers.
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsLoadModalOpen(true)}
              className="text-xs bg-white dark:bg-slate-900"
            >
              <FolderOpen className="h-3.5 w-3.5 mr-1 text-slate-500" />
              Saved Scenarios ({savedScenarios.length})
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setIsSaveModalOpen(true)}
              className="text-xs bg-amber-600 hover:bg-amber-700 text-white"
            >
              <Save className="h-3.5 w-3.5 mr-1" />
              Save Scenario
            </Button>
          </div>
        </div>
      </div>

      {/* Page Title & Controls Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white flex items-center gap-2">
            <Calculator className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            Financial Forecasting & Scenario Simulator
          </h1>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Explainable forward-looking MRR, ARR, and cash collections projection engine
          </p>
        </div>

        {/* Horizon Selector */}
        <div className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white p-1 dark:border-slate-800 dark:bg-slate-900 shadow-sm">
          <span className="text-xs font-medium text-slate-500 px-2 flex items-center gap-1">
            <Calendar className="h-3 w-3" /> Horizon:
          </span>
          {[3, 6, 12, 24].map((m) => (
            <button
              key={m}
              onClick={() => setHorizonMonths(m)}
              className={`rounded-md px-2.5 py-1 text-xs font-semibold transition-all ${
                horizonMonths === m
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white'
              }`}
            >
              {m}M
            </button>
          ))}
        </div>
      </div>

      {/* KPI Highlight Strip */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <Card className="p-3.5 bg-slate-50/50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Starting MRR</p>
          <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            ₹{summary ? parseFloat(summary.starting_mrr).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </p>
          <span className="text-[11px] text-slate-400">Live Actual Baseline</span>
        </Card>

        <Card className="p-3.5 bg-indigo-50/40 dark:bg-indigo-950/20 border-indigo-200 dark:border-indigo-800/40">
          <p className="text-xs font-semibold text-indigo-700 dark:text-indigo-400 uppercase tracking-wider">
            Projected Ending MRR
          </p>
          <p className="text-lg font-bold text-indigo-950 dark:text-indigo-200 mt-1">
            ₹{summary ? parseFloat(summary.ending_mrr).toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
          </p>
          <span className="text-[11px] text-indigo-600 dark:text-indigo-400 font-medium">
            Month +{horizonMonths} Projection
          </span>
        </Card>

        <Card className="p-3.5 bg-emerald-50/40 dark:bg-emerald-950/20 border-emerald-200 dark:border-emerald-800/40">
          <p className="text-xs font-semibold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider">
            Annualized Growth
          </p>
          <p className="text-lg font-bold text-emerald-950 dark:text-emerald-200 mt-1 flex items-center gap-1">
            {summary && summary.projected_annual_growth_pct >= 0 ? (
              <ArrowUpRight className="h-4 w-4 text-emerald-600" />
            ) : (
              <ArrowDownRight className="h-4 w-4 text-rose-600" />
            )}
            {summary ? summary.projected_annual_growth_pct.toFixed(1) : '0.0'}%
          </p>
          <span className="text-[11px] text-emerald-600 dark:text-emerald-400">
            {summary?.projected_growth_pct.toFixed(1)}% over {horizonMonths}m
          </span>
        </Card>

        <Card className="p-3.5 bg-slate-50/50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-800">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Projected Invoiced</p>
          <p className="text-lg font-bold text-slate-900 dark:text-white mt-1">
            ₹{summary ? parseFloat(summary.total_projected_invoiced).toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '0'}
          </p>
          <span className="text-[11px] text-slate-400">Total Billed ({horizonMonths}m)</span>
        </Card>

        <Card className="p-3.5 bg-teal-50/40 dark:bg-teal-950/20 border-teal-200 dark:border-teal-800/40">
          <p className="text-xs font-semibold text-teal-700 dark:text-teal-400 uppercase tracking-wider">
            Projected Collections
          </p>
          <p className="text-lg font-bold text-teal-950 dark:text-teal-200 mt-1">
            ₹{summary ? parseFloat(summary.total_projected_collected).toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '0'}
          </p>
          <span className="text-[11px] text-teal-600 dark:text-teal-400 font-medium">
            @{assumptions.collection_rate_pct}% collection
          </span>
        </Card>

        <Card className="p-3.5 bg-amber-50/40 dark:bg-amber-950/20 border-amber-200 dark:border-amber-800/40">
          <p className="text-xs font-semibold text-amber-700 dark:text-amber-400 uppercase tracking-wider">
            Projected Outstanding
          </p>
          <p className="text-lg font-bold text-amber-950 dark:text-amber-200 mt-1">
            ₹{summary ? parseFloat(summary.total_projected_outstanding).toLocaleString('en-IN', { minimumFractionDigits: 0 }) : '0'}
          </p>
          <span className="text-[11px] text-amber-600 dark:text-amber-400 font-medium">Expected AR Balance</span>
        </Card>
      </div>

      {/* Main Simulator Grid: Controls on Left, Chart on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Sliders Control Panel */}
        <div className="lg:col-span-4 space-y-4">
          <Card className="p-5 border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Sliders className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
                <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                  Simulation Parameters
                </h3>
              </div>
              <button
                onClick={handleResetToBaseline}
                className="text-xs text-slate-500 hover:text-indigo-600 dark:hover:text-indigo-400 flex items-center gap-1"
                title="Reset sliders to historical baseline"
              >
                <RotateCcw className="h-3 w-3" /> Reset
              </button>
            </div>

            {/* Presets */}
            <div className="mt-3">
              <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-1.5 block">
                Quick Scenarios:
              </label>
              <div className="grid grid-cols-3 gap-1.5">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleApplyPreset('aggressive')}
                  className="text-[11px] px-2 py-1 bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-950/30 dark:border-emerald-800 dark:text-emerald-300"
                >
                  🚀 Aggressive
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleApplyPreset('conservative')}
                  className="text-[11px] px-2 py-1 bg-slate-50 text-slate-700 border-slate-200 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300"
                >
                  🛡️ Conservative
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleApplyPreset('stress')}
                  className="text-[11px] px-2 py-1 bg-rose-50 text-rose-700 border-rose-200 dark:bg-rose-950/30 dark:border-rose-800 dark:text-rose-300"
                >
                  ⚠️ Stress Test
                </Button>
              </div>
            </div>

            {/* Parameter Sliders */}
            <div className="space-y-4 mt-5">
              {/* New Growth */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    New Subscription Growth
                  </span>
                  <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                    {assumptions.new_growth_pct > 0 ? `+${assumptions.new_growth_pct}%` : `${assumptions.new_growth_pct}%`}
                  </span>
                </div>
                <input
                  type="range"
                  min="-10"
                  max="40"
                  step="0.5"
                  value={assumptions.new_growth_pct}
                  onChange={(e) => updateAssumption('new_growth_pct', parseFloat(e.target.value))}
                  className="w-full accent-indigo-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400">Monthly new customer MRR addition</span>
              </div>

              {/* Churn */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    Monthly Churn Rate
                  </span>
                  <span className="font-mono font-bold text-rose-600 dark:text-rose-400">
                    {assumptions.churn_pct}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="25"
                  step="0.25"
                  value={assumptions.churn_pct}
                  onChange={(e) => updateAssumption('churn_pct', parseFloat(e.target.value))}
                  className="w-full accent-rose-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400">Cancelled / expired subscriptions per month</span>
              </div>

              {/* Expansion / Upgrades */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    Expansion / Upgrades
                  </span>
                  <span className="font-mono font-bold text-emerald-600 dark:text-emerald-400">
                    +{assumptions.expansion_pct}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="20"
                  step="0.5"
                  value={assumptions.expansion_pct}
                  onChange={(e) => updateAssumption('expansion_pct', parseFloat(e.target.value))}
                  className="w-full accent-emerald-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400">Existing account tier upgrades & expansions</span>
              </div>

              {/* Contraction / Downgrades */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    Contraction / Downgrades
                  </span>
                  <span className="font-mono font-bold text-amber-600 dark:text-amber-400">
                    -{assumptions.contraction_pct}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="15"
                  step="0.5"
                  value={assumptions.contraction_pct}
                  onChange={(e) => updateAssumption('contraction_pct', parseFloat(e.target.value))}
                  className="w-full accent-amber-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400">Plan downgrades & seat reductions</span>
              </div>

              {/* Collection Rate */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    Collection Efficiency Rate
                  </span>
                  <span className="font-mono font-bold text-teal-600 dark:text-teal-400">
                    {assumptions.collection_rate_pct}%
                  </span>
                </div>
                <input
                  type="range"
                  min="50"
                  max="100"
                  step="1"
                  value={assumptions.collection_rate_pct}
                  onChange={(e) => updateAssumption('collection_rate_pct', parseFloat(e.target.value))}
                  className="w-full accent-teal-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400">Expected percentage of billed invoices collected</span>
              </div>

              {/* Price Increase */}
              <div>
                <div className="flex justify-between items-center text-xs mb-1">
                  <span className="font-medium text-slate-700 dark:text-slate-300">
                    Catalog Price Adjustment
                  </span>
                  <span className="font-mono font-bold text-violet-600 dark:text-violet-400">
                    {assumptions.price_increase_pct > 0 ? `+${assumptions.price_increase_pct}%` : `${assumptions.price_increase_pct}%`}
                  </span>
                </div>
                <input
                  type="range"
                  min="-20"
                  max="30"
                  step="1"
                  value={assumptions.price_increase_pct}
                  onChange={(e) => updateAssumption('price_increase_pct', parseFloat(e.target.value))}
                  className="w-full accent-violet-600 cursor-pointer"
                />
                <span className="text-[10px] text-slate-400">General price rise or promotional discount</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Chart View */}
        <div className="lg:col-span-8 space-y-4">
          <Card className="p-5 border-slate-200 dark:border-slate-800 shadow-sm">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-bold text-slate-900 dark:text-white">
                    MRR Trajectory: Baseline vs Simulated Scenario
                  </h3>
                  <Badge variant="warning" className="text-[10px] font-mono">
                    PROJECTION
                  </Badge>
                </div>
                <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                  Visual comparison over the next {horizonMonths} months
                </p>
              </div>

              {simulating && (
                <span className="flex items-center gap-1.5 text-xs text-indigo-600 font-medium">
                  <span className="h-2 w-2 rounded-full bg-indigo-600 animate-ping" />
                  Simulating...
                </span>
              )}
            </div>

            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{ top: 10, right: 20, left: 20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                  <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                  <YAxis
                    tick={{ fontSize: 11 }}
                    tickFormatter={(val) => `₹${(val / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    content={({ active, payload, label }) => {
                      if (!active || !payload || !payload.length) return null;
                      const d = payload[0].payload;
                      return (
                        <div className="rounded-lg border border-slate-200 bg-white p-3 shadow-lg dark:border-slate-700 dark:bg-slate-900 text-xs space-y-1.5 max-w-xs">
                          <p className="font-bold text-slate-900 dark:text-white border-b pb-1">
                            Month {label}
                          </p>
                          <div className="flex justify-between gap-4">
                            <span className="text-slate-500">Baseline MRR:</span>
                            <span className="font-mono font-medium">
                              ₹{d.baseline_mrr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </span>
                          </div>
                          <div className="flex justify-between gap-4 text-indigo-600 font-bold">
                            <span>Simulated MRR:</span>
                            <span className="font-mono">
                              ₹{d.projected_mrr.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </span>
                          </div>
                          <div className="flex justify-between gap-4 text-teal-600">
                            <span>Projected Collections:</span>
                            <span className="font-mono">
                              ₹{d.projected_collected.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                            </span>
                          </div>
                          <div className="pt-1.5 border-t text-[11px] text-slate-600 dark:text-slate-400 italic">
                            {d.step_explanation}
                          </div>
                        </div>
                      );
                    }}
                  />
                  <Legend />
                  <Area
                    type="monotone"
                    dataKey="projected_collected"
                    name="Projected Collections"
                    fill="#14b8a6"
                    stroke="#0d9488"
                    fillOpacity={0.12}
                  />
                  <Line
                    type="monotone"
                    dataKey="baseline_mrr"
                    name="Historical Baseline"
                    stroke="#94a3b8"
                    strokeDasharray="4 4"
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="projected_mrr"
                    name="Simulated Scenario"
                    stroke="#4f46e5"
                    strokeWidth={3}
                    dot={{ r: 3, fill: '#4f46e5' }}
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>
      </div>

      {/* Step-by-Step Mathematical Explanation Ledger */}
      <Card className="p-5 border-slate-200 dark:border-slate-800 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Calculator className="h-4 w-4 text-indigo-600" />
            <h3 className="font-bold text-slate-900 dark:text-white">
              Mathematical Step Explanations (Explainable Simulator)
            </h3>
          </div>
          <Badge variant="outline" className="text-xs">
            {simulationData?.projection?.length || 0} Step Intervals
          </Badge>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-800 text-slate-500 uppercase tracking-wider font-semibold">
                <th className="py-2.5 px-3">Interval</th>
                <th className="py-2.5 px-3">Projected MRR</th>
                <th className="py-2.5 px-3">ARR Equivalent</th>
                <th className="py-2.5 px-3">Expected Billed</th>
                <th className="py-2.5 px-3">Expected Collected</th>
                <th className="py-2.5 px-3">Outstanding AR</th>
                <th className="py-2.5 px-3 w-1/3">Formula Step Formulation</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 font-mono text-slate-700 dark:text-slate-300">
              {(simulationData?.projection || []).map((step, idx) => (
                <tr key={step.month} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/30">
                  <td className="py-2 px-3 font-semibold text-slate-900 dark:text-white flex items-center gap-1.5">
                    <span className="text-[10px] text-slate-400">#{idx + 1}</span> {step.month}
                  </td>
                  <td className="py-2 px-3 font-bold text-indigo-600 dark:text-indigo-400">
                    ₹{parseFloat(step.mrr).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-3 text-slate-500">
                    ₹{parseFloat(step.arr).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-3">
                    ₹{parseFloat(step.projected_invoiced).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-3 text-emerald-600 dark:text-emerald-400 font-semibold">
                    ₹{parseFloat(step.projected_collected).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-3 text-amber-600">
                    ₹{parseFloat(step.projected_outstanding).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-2 px-3 text-[11px] font-sans text-slate-600 dark:text-slate-400">
                    {step.step_explanation}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Save Scenario Modal */}
      <Modal
        isOpen={isSaveModalOpen}
        onClose={() => setIsSaveModalOpen(false)}
        title="Save Simulation Scenario"
        description="Persist this set of assumptions and projection model for future review and team comparisons."
      >
        <div className="space-y-4 py-2">
          {saveSuccessMsg ? (
            <div className="rounded-lg bg-emerald-50 p-4 text-emerald-800 flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
              <span>{saveSuccessMsg}</span>
            </div>
          ) : (
            <>
              <Input
                label="Scenario Name"
                placeholder="e.g. Q1 Aggressive Expansion Model"
                value={scenarioName}
                onChange={(e) => setScenarioName(e.target.value)}
              />
              <div>
                <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300 mb-1">
                  Description / Context (Optional)
                </label>
                <textarea
                  rows={3}
                  value={scenarioDescription}
                  onChange={(e) => setScenarioDescription(e.target.value)}
                  placeholder="Notes regarding sales hiring, churn mitigation, price rises..."
                  className="w-full rounded-lg border border-slate-300 p-2.5 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                />
              </div>

              <div className="rounded-lg bg-slate-50 dark:bg-slate-800/40 p-3 text-xs space-y-1">
                <p className="font-semibold text-slate-700 dark:text-slate-300">Included Assumptions:</p>
                <p className="text-slate-500">
                  New Growth: +{assumptions.new_growth_pct}% | Churn: {assumptions.churn_pct}% | Expansion: +{assumptions.expansion_pct}% | Collection: {assumptions.collection_rate_pct}%
                </p>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <Button variant="outline" size="sm" onClick={() => setIsSaveModalOpen(false)}>
                  Cancel
                </Button>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={handleSaveScenario}
                  disabled={!scenarioName.trim()}
                  className="bg-amber-600 hover:bg-amber-700 text-white"
                >
                  <Save className="h-4 w-4 mr-1" />
                  Save Scenario
                </Button>
              </div>
            </>
          )}
        </div>
      </Modal>

      {/* Saved Scenarios List Modal */}
      <Modal
        isOpen={isLoadModalOpen}
        onClose={() => setIsLoadModalOpen(false)}
        title="Saved Forecast Scenarios"
        description="Select a previously stored scenario to load its assumptions into the simulator."
        size="lg"
      >
        <div className="space-y-3 py-2 max-h-96 overflow-y-auto">
          {savedScenarios.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">
              No saved scenarios found. Configure parameters and click "Save Scenario" above.
            </p>
          ) : (
            savedScenarios.map((sc) => (
              <div
                key={sc.id}
                onClick={() => handleLoadScenario(sc)}
                className="rounded-lg border border-slate-200 dark:border-slate-800 p-3 hover:border-indigo-500 dark:hover:border-indigo-500 cursor-pointer transition-all flex items-center justify-between"
              >
                <div>
                  <h4 className="font-bold text-sm text-slate-900 dark:text-white">{sc.name}</h4>
                  {sc.description && (
                    <p className="text-xs text-slate-500 mt-0.5">{sc.description}</p>
                  )}
                  <div className="flex items-center gap-3 text-[11px] text-slate-400 mt-2 font-mono">
                    <span>Horizon: {sc.horizon_months}M</span>
                    <span>Growth: +{sc.assumptions.new_growth_pct}%</span>
                    <span>Churn: {sc.assumptions.churn_pct}%</span>
                    <span>Collection: {sc.assumptions.collection_rate_pct}%</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-xs text-indigo-600 border-indigo-200"
                    onClick={() => handleLoadScenario(sc)}
                  >
                    Load
                  </Button>
                  <button
                    onClick={(e) => handleDeleteScenario(sc.id, e)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md"
                    title="Delete scenario"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </Modal>
    </div>
  );
};
