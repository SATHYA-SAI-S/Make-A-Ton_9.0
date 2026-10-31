import React, { useState } from 'react';
import {
  DollarSign,
  TrendingUp,
  AlertCircle,
  Users,
  Search,
  Sparkles,
  Layers,
  ArrowRight,
  ShieldCheck,
} from 'lucide-react';
import {
  Button,
  Input,
  Select,
  Modal,
  Table,
  Tabs,
  Badge,
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  StatCard,
  useToast,
} from '@/shared/ui';
import { ChartCard, FilterBar, useChartFilters } from '@/modules/p3/charts';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';

export const UiDemo: React.FC = () => {
  const { toast } = useToast();
  const [activeTab, setActiveTab] = useState('components');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isTableLoading, setIsTableLoading] = useState(false);
  const [chartState, setChartState] = useState<'normal' | 'loading' | 'error' | 'empty'>('normal');

  const { filters, updateFilters, resetFilters } = useChartFilters();

  const demoChartData = [
    { month: 'May', mrr: 120000, collected: 114000 },
    { month: 'Jun', mrr: 135000, collected: 128000 },
    { month: 'Jul', mrr: 148000, collected: 141000 },
    { month: 'Aug', mrr: 162000, collected: 155000 },
    { month: 'Sep', mrr: 174000, collected: 168000 },
    { month: 'Oct', mrr: 184500, collected: 179200 },
  ];

  const tableData = [
    { id: '1', name: 'Acme Software', plan: 'Enterprise Monthly', mrr: '₹15,600.00', status: 'ACTIVE' },
    { id: '2', name: 'TechCorp Logistics', plan: 'Growth Yearly', mrr: '₹5,000.00', status: 'ACTIVE' },
    { id: '3', name: 'BrightRetail Inc', plan: 'Starter Monthly', mrr: '₹2,500.00', status: 'PAUSED' },
    { id: '4', name: 'Global Logistics', plan: 'Enterprise Yearly', mrr: '₹24,000.00', status: 'CLOSED' },
  ];

  const tableColumns = [
    { key: 'name', header: 'Customer' },
    { key: 'plan', header: 'Subscription Plan' },
    { key: 'mrr', header: 'Normalized MRR', align: 'right' as const },
    {
      key: 'status',
      header: 'Status',
      align: 'center' as const,
      render: (item: any) => (
        <Badge
          variant={
            item.status === 'ACTIVE'
              ? 'success'
              : item.status === 'PAUSED'
              ? 'warning'
              : 'neutral'
          }
          dot
        >
          {item.status}
        </Badge>
      ),
    },
  ];

  return (
    <div className="space-y-8 pb-12">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-brand-600 via-indigo-600 to-purple-600 text-white shadow-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md text-xs font-semibold uppercase tracking-wider mb-2">
            <Sparkles className="w-3.5 h-3.5" /> Person 3 Design System
          </div>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
            SubscriptIQ UI Kit & Component Showcase
          </h1>
          <p className="mt-1 text-sm text-brand-100 max-w-xl">
            Clean, accessible, theme-aware React components provided by Person 3 as the foundational design system for all SubscriptIQ modules.
          </p>
        </div>

        <Button
          variant="secondary"
          onClick={() => setIsModalOpen(true)}
          leftIcon={<Layers className="w-4 h-4" />}
        >
          Open Modal Demo
        </Button>
      </div>

      {/* Primary Navigation Tabs */}
      <Tabs
        tabs={[
          { id: 'components', label: 'Core Design System' },
          { id: 'charts', label: 'Analytics & Chart Wrappers' },
          { id: 'feedback', label: 'Modals & Interactive Toast' },
        ]}
        activeTab={activeTab}
        onChange={setActiveTab}
        variant="pills"
      />

      {/* SECTION 1: Core Design System */}
      {activeTab === 'components' && (
        <div className="space-y-8">
          {/* Executive KPI StatCards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <StatCard
              title="Monthly Recurring Revenue"
              value="₹184,500.00"
              changePct={13.8}
              icon={<DollarSign className="w-5 h-5 text-brand-600" />}
              subtitle="All active subscriptions"
            />
            <StatCard
              title="Annual Recurring Revenue"
              value="₹2,214,000.00"
              changePct={13.8}
              icon={<TrendingUp className="w-5 h-5 text-emerald-600" />}
              subtitle="Run-rate (MRR × 12)"
            />
            <StatCard
              title="Active Customers"
              value="118"
              changePct={7.2}
              icon={<Users className="w-5 h-5 text-indigo-600" />}
              subtitle="Accounts with active plans"
            />
            <StatCard
              title="Customer Churn Rate"
              value="2.1%"
              changePct={-0.7}
              invertColors
              icon={<AlertCircle className="w-5 h-5 text-rose-600" />}
              subtitle="Down 0.7% from Sep"
            />
          </div>

          {/* Buttons Showcase */}
          <Card>
            <CardHeader>
              <CardTitle>Button System (`Button`)</CardTitle>
              <CardDescription>
                Accessible buttons with 5 variants, 3 sizes, loading spinners, and icon slots.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="primary">Primary Action</Button>
                <Button variant="secondary">Secondary</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="danger">Danger</Button>
                <Button variant="ghost">Ghost Button</Button>
                <Button variant="primary" isLoading>Loading State</Button>
                <Button variant="primary" rightIcon={<ArrowRight className="w-4 h-4" />}>
                  With Icon
                </Button>
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-2 border-t border-slate-100 dark:border-slate-800">
                <Button size="sm">Small (sm)</Button>
                <Button size="md">Medium (md)</Button>
                <Button size="lg">Large (lg)</Button>
              </div>
            </CardContent>
          </Card>

          {/* Form Inputs & Selects */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Form Inputs (`Input`)</CardTitle>
                <CardDescription>Text fields with label, helper, error, and icon bindings.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input
                  label="Customer Search"
                  placeholder="Search by company name or GSTIN..."
                  leftIcon={<Search className="w-4 h-4" />}
                />
                <Input
                  label="Tax ID / GSTIN"
                  placeholder="29ABCDE1234F1Z5"
                  helperText="Format: 15-character alphanumeric GSTIN code."
                />
                <Input
                  label="Discount Code"
                  placeholder="FALL10"
                  error="This discount rule has expired."
                />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Form Controls (`Select` & `Badge`)</CardTitle>
                <CardDescription>Dropdown selects and semantic status badges.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Select
                  label="Billing Frequency"
                  options={[
                    { value: 'MONTHLY', label: 'Monthly Billed' },
                    { value: 'YEARLY', label: 'Yearly Billed (Discounted)' },
                    { value: 'WEEKLY', label: 'Weekly Billed' },
                  ]}
                />

                <div className="space-y-2 pt-2">
                  <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 dark:text-slate-300">
                    Badge Status Pills
                  </label>
                  <div className="flex flex-wrap gap-2">
                    <Badge variant="success" dot>Active</Badge>
                    <Badge variant="warning" dot>Paused</Badge>
                    <Badge variant="danger" dot>Overdue</Badge>
                    <Badge variant="info" dot>Draft</Badge>
                    <Badge variant="neutral">Closed</Badge>
                    <Badge variant="brand">Signature</Badge>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Data Table with Pagination */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Data Table with Server Pagination (`Table`)</CardTitle>
                <CardDescription>Sortable columns, custom renderers, and responsive pagination.</CardDescription>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsTableLoading(!isTableLoading)}
              >
                {isTableLoading ? 'Show Table Data' : 'Test Loading Skeleton'}
              </Button>
            </CardHeader>
            <CardContent>
              <Table
                columns={tableColumns}
                data={tableData}
                isLoading={isTableLoading}
                total={28}
                page={1}
                pageSize={4}
                onPageChange={(p) => toast.info(`Navigated to page ${p}`)}
              />
            </CardContent>
          </Card>
        </div>
      )}

      {/* SECTION 2: Analytics & Chart Wrappers */}
      {activeTab === 'charts' && (
        <div className="space-y-6">
          <FilterBar
            filters={filters}
            onChange={updateFilters}
            onReset={resetFilters}
          />

          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-500">Test Chart States:</span>
            <div className="flex gap-1.5">
              {(['normal', 'loading', 'error', 'empty'] as const).map((s) => (
                <button
                  key={s}
                  onClick={() => setChartState(s)}
                  className={`px-2.5 py-1 rounded text-xs capitalize font-medium ${
                    chartState === s
                      ? 'bg-brand-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <ChartCard
            title="Revenue Performance (Invoiced vs Collected)"
            description="Normalized recurring revenue billed vs cash received over the last 6 months"
            isLoading={chartState === 'loading'}
            isError={chartState === 'error'}
            isEmpty={chartState === 'empty'}
            onRefresh={() => toast.success('Dataset Refreshed', 'Chart data updated with latest billing ledger.')}
            onExport={() => toast.info('Export Started', 'Generating revenue_performance_2026.csv')}
          >
            <ResponsiveContainer width="100%" height={320}>
              <AreaChart data={demoChartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorMrr" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorCollected" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="month" stroke="#94a3b8" />
                <YAxis stroke="#94a3b8" tickFormatter={(v) => `₹${(v / 1000).toFixed(0)}k`} />
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.6} />
                <Tooltip
                  formatter={(val: any) => [`₹${Number(val).toLocaleString()}`, '']}
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '12px', border: 'none', color: '#fff' }}
                />
                <Area type="monotone" dataKey="mrr" name="Invoiced MRR" stroke="#6366f1" strokeWidth={2.5} fillOpacity={1} fill="url(#colorMrr)" />
                <Area type="monotone" dataKey="collected" name="Cash Collected" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorCollected)" />
              </AreaChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      )}

      {/* SECTION 3: Feedback & Dialogs */}
      {activeTab === 'feedback' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Toast Notifications (`useToast`)</CardTitle>
              <CardDescription>Trigger floating, accessible notifications.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                variant="primary"
                onClick={() => toast.success('Operation Successful', 'Subscription #SUB-2026-0001 has been activated.')}
                className="w-full"
              >
                Trigger Success Toast
              </Button>
              <Button
                variant="danger"
                onClick={() => toast.error('Payment Failed', 'Card transaction rejected by gateway (insufficient funds).')}
                className="w-full"
              >
                Trigger Error Toast
              </Button>
              <Button
                variant="secondary"
                onClick={() => toast.info('Scheduled Job Running', 'Celery nightly revenue snapshot has begun.')}
                className="w-full"
              >
                Trigger Info Toast
              </Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Modal Dialogs (`Modal`)</CardTitle>
              <CardDescription>Focus-trapped, backdrop-dismissible dialogs.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Click below to open the sample subscription upgrade confirmation modal.
              </p>
              <Button variant="primary" onClick={() => setIsModalOpen(true)}>
                Open Subscription Modal
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Interactive Modal Component */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Confirm Plan Upgrade Request"
        description="Review effective date and pricing snapshot before submission."
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Cancel
            </Button>
            <Button
              variant="primary"
              onClick={() => {
                setIsModalOpen(false);
                toast.success('Upgrade Submitted', 'Your request has been forwarded to staff review.');
              }}
            >
              Submit Upgrade
            </Button>
          </>
        }
      >
        <div className="space-y-3 text-sm">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 space-y-1.5">
            <div className="flex justify-between">
              <span className="text-slate-500">Current Plan:</span>
              <span className="font-semibold">Enterprise Monthly (₹15,600/mo)</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Requested Plan:</span>
              <span className="font-semibold text-brand-600">Enterprise Yearly (₹150,000/yr)</span>
            </div>
            <div className="flex justify-between text-xs text-emerald-600">
              <span>Annual Savings:</span>
              <span>₹37,200.00 / year (20% discount)</span>
            </div>
          </div>
          <p className="text-xs text-slate-500">
            Once staff approves, your billing period will automatically transition on the next renewal date.
          </p>
        </div>
      </Modal>
    </div>
  );
};
