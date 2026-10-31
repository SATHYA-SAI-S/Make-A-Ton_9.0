import React, { useEffect, useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  CreditCard,
  Layers,
  Calendar,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  Download,
  Building2,
  Mail,
  Phone,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  StatCard,
  Badge,
  Button,
  useToast,
} from '@/shared/ui';
import { portalApi } from '../../api/portalApi';
import { DashboardSummary } from '../../types/portal';

export const CustomerDashboard: React.FC = () => {
  const { toast } = useToast();
  const [data, setData] = useState<DashboardSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    portalApi
      .getDashboard()
      .then((res) => setData(res))
      .catch((err) => toast.error('Error loading dashboard', err.message))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      {/* Top Welcome Card */}
      <div className="p-6 rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white shadow-lg border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="space-y-1.5">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-brand-500/20 text-brand-300 text-xs font-semibold border border-brand-500/30">
            <ShieldCheck className="w-3.5 h-3.5" /> Customer Self-Service Portal
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            Welcome back, {data?.customer.name || 'Valued Customer'}
          </h1>
          <div className="flex flex-wrap items-center gap-4 text-xs text-slate-400 pt-1">
            <span className="flex items-center gap-1">
              <Mail className="w-3.5 h-3.5" /> {data?.customer.email}
            </span>
            <span className="flex items-center gap-1">
              <Phone className="w-3.5 h-3.5" /> {data?.customer.phone || 'No phone set'}
            </span>
            <span className="flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5" /> GSTIN: {data?.customer.gstin || 'Unregistered'}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <NavLink to="/portal/subscriptions">
            <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-4 h-4" />}>
              Manage Subscriptions
            </Button>
          </NavLink>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Active Subscriptions"
          value={isLoading ? '...' : data?.active_subscriptions_count ?? 0}
          icon={<Layers className="w-5 h-5 text-brand-600" />}
          subtitle="Enterprise SLA services"
        />
        <StatCard
          title="Outstanding Balance"
          value={isLoading ? '...' : `₹${Number(data?.outstanding_balance || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}`}
          icon={<CreditCard className="w-5 h-5 text-amber-600" />}
          subtitle="Pending settlement"
          invertColors
        />
        <StatCard
          title="Unpaid Invoices"
          value={isLoading ? '...' : data?.unpaid_invoices_count ?? 0}
          icon={<AlertCircle className="w-5 h-5 text-rose-600" />}
          subtitle="Action required"
          invertColors
        />
        <StatCard
          title="Next Renewal Date"
          value={isLoading ? '...' : data?.next_renewal_date || 'None'}
          icon={<Calendar className="w-5 h-5 text-emerald-600" />}
          subtitle="Auto-renewal enabled"
        />
      </div>

      {/* Active Subscriptions and Invoices Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Subscriptions */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>My Subscriptions</CardTitle>
              <p className="text-xs text-slate-500">Contracted recurring plans & licenses</p>
            </div>
            <NavLink to="/portal/subscriptions">
              <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                View all
              </Button>
            </NavLink>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading ? (
              <div className="py-8 text-center text-xs text-slate-400">Loading subscriptions...</div>
            ) : !data?.recent_subscriptions.length ? (
              <div className="py-8 text-center text-xs text-slate-400">No active subscriptions</div>
            ) : (
              data.recent_subscriptions.map((sub) => (
                <div
                  key={sub.id}
                  className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850/50 flex items-center justify-between gap-3"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-slate-900 dark:text-slate-100 truncate">
                        {sub.plan_name}
                      </span>
                      <Badge variant={sub.status === 'ACTIVE' ? 'success' : 'warning'} size="sm" dot>
                        {sub.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {sub.number} • Billed {sub.billing_frequency.toLowerCase()} • Renews {sub.expiry_date}
                    </p>
                  </div>

                  <NavLink to="/portal/subscriptions">
                    <Button variant="outline" size="sm">
                      Details
                    </Button>
                  </NavLink>
                </div>
              ))
            )}
          </CardContent>
        </Card>

        {/* Recent Invoices */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>Recent Invoices</CardTitle>
              <p className="text-xs text-slate-500">Billing statements & payment status</p>
            </div>
            <NavLink to="/portal/invoices">
              <Button variant="ghost" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />}>
                View all
              </Button>
            </NavLink>
          </CardHeader>
          <CardContent className="space-y-3">
            {isLoading ? (
              <div className="py-8 text-center text-xs text-slate-400">Loading invoices...</div>
            ) : !data?.recent_invoices.length ? (
              <div className="py-8 text-center text-xs text-slate-400">No invoices generated yet</div>
            ) : (
              data.recent_invoices.map((inv) => (
                <div
                  key={inv.id}
                  className="p-4 rounded-xl border border-slate-100 dark:border-slate-800 bg-slate-50/50 dark:bg-slate-850/50 flex items-center justify-between gap-3"
                >
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-sm text-slate-900 dark:text-slate-100">
                        {inv.number}
                      </span>
                      <Badge
                        variant={inv.status === 'PAID' ? 'success' : 'danger'}
                        size="sm"
                        dot
                      >
                        {inv.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Due: {inv.due_date} • Balance: ₹{Number(inv.balance).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-900 dark:text-slate-100">
                      ₹{Number(inv.total).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </span>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => portalApi.downloadInvoicePdf(inv.id, inv.number)}
                      title="Download PDF"
                    >
                      <Download className="w-4 h-4 text-slate-500" />
                    </Button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
