import React, { useEffect, useState } from 'react';
import {
  Layers,
  Calendar,
  AlertCircle,
  ArrowUpRight,
  PauseCircle,
  XCircle,
  RefreshCw,
  PlusCircle,
  CheckCircle2,
  Clock,
  Sparkles,
} from 'lucide-react';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Badge,
  Button,
  Modal,
  Select,
  Input,
  Tabs,
  useToast,
} from '@/shared/ui';
import { portalApi } from '../../api/portalApi';
import { Subscription, CustomerRequest } from '../../types/portal';

export const MySubscriptions: React.FC = () => {
  const { toast } = useToast();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [requests, setRequests] = useState<CustomerRequest[]>([]);
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [isLoading, setIsLoading] = useState(true);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [activeSub, setActiveSub] = useState<Subscription | null>(null);
  const [requestType, setRequestType] = useState<string>('UPGRADE');
  const [targetPlanId, setTargetPlanId] = useState<string>('plan-ent-yearly');
  const [requestNote, setRequestNote] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchSubscriptions = () => {
    setIsLoading(true);
    Promise.all([
      portalApi.getSubscriptions(selectedStatus),
      portalApi.getMyRequests(),
    ])
      .then(([subs, reqs]) => {
        setSubscriptions(subs);
        setRequests(reqs.items || []);
      })
      .catch((err) => toast.error('Failed to load subscriptions', err.message))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => {
    fetchSubscriptions();
  }, [selectedStatus]);

  const openActionModal = (sub: Subscription, type: string) => {
    setActiveSub(sub);
    setRequestType(type);
    setRequestNote('');
    setIsModalOpen(true);
  };

  const handleRequestSubmit = async () => {
    if (!activeSub) return;
    setIsSubmitting(true);
    try {
      await portalApi.submitRequest({
        subscription_id: activeSub.id,
        type: requestType,
        target_plan_id: requestType === 'UPGRADE' || requestType === 'DOWNGRADE' ? targetPlanId : undefined,
        note: requestNote || undefined,
      });
      toast.success('Request Submitted', `Your ${requestType} request has been submitted for staff review.`);
      setIsModalOpen(false);
      fetchSubscriptions();
    } catch (err: any) {
      toast.error('Submission Failed', err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  const statusTabs = [
    { id: 'ALL', label: 'All Subscriptions' },
    { id: 'ACTIVE', label: 'Active', badge: subscriptions.filter((s) => s.status === 'ACTIVE').length },
    { id: 'PAUSED', label: 'Paused', badge: subscriptions.filter((s) => s.status === 'PAUSED').length },
    { id: 'CLOSED', label: 'Closed', badge: subscriptions.filter((s) => s.status === 'CLOSED').length },
  ];

  const planOptions = [
    { value: 'plan-ent-yearly', label: 'Enterprise Cloud Suite (Yearly - 20% discount)' },
    { value: 'plan-ent-monthly', label: 'Enterprise Cloud Suite (Monthly)' },
    { value: 'plan-growth-yearly', label: 'Growth Tier (Yearly)' },
    { value: 'plan-support-monthly', label: '24/7 Dedicated SLA Support' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
            My Subscriptions
          </h1>
          <p className="text-xs text-slate-500">
            Active plans, contracted seat quantities, and lifecycle modification requests.
          </p>
        </div>

        <Tabs
          tabs={statusTabs}
          activeTab={selectedStatus}
          onChange={setSelectedStatus}
          variant="pills"
        />
      </div>

      {/* Subscriptions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {isLoading ? (
          <div className="col-span-2 py-12 text-center text-sm text-slate-400">Loading subscriptions...</div>
        ) : !subscriptions.length ? (
          <div className="col-span-2 py-12 text-center text-sm text-slate-400">
            No subscriptions found matching filter "{selectedStatus}".
          </div>
        ) : (
          subscriptions.map((sub) => (
            <Card key={sub.id} className="relative overflow-hidden flex flex-col justify-between">
              <div>
                <CardHeader className="flex flex-row items-start justify-between pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">
                        {sub.plan_name}
                      </h3>
                      <Badge
                        variant={
                          sub.status === 'ACTIVE'
                            ? 'success'
                            : sub.status === 'PAUSED'
                            ? 'warning'
                            : 'neutral'
                        }
                        size="sm"
                        dot
                      >
                        {sub.status}
                      </Badge>
                    </div>
                    <p className="text-xs text-slate-400 mt-0.5">Reference: {sub.number}</p>
                  </div>

                  <span className="text-xs font-semibold px-2.5 py-1 rounded-lg bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    {sub.billing_frequency}
                  </span>
                </CardHeader>

                <CardContent className="space-y-4 pt-2">
                  {/* Line Items */}
                  <div className="space-y-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                      Contracted Lines
                    </span>
                    {sub.lines.map((line) => (
                      <div
                        key={line.id}
                        className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs"
                      >
                        <div>
                          <p className="font-semibold text-slate-800 dark:text-slate-200">{line.product_name}</p>
                          <p className="text-slate-400">
                            {line.quantity} seats @ ₹{Number(line.unit_price).toLocaleString('en-IN')}/seat
                          </p>
                        </div>
                        <span className="font-bold text-slate-900 dark:text-slate-100">
                          ₹{Number(line.amount).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* Dates & Terms */}
                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
                    <div>
                      <span className="text-slate-400 block text-[11px]">Start Date</span>
                      <span className="font-medium text-slate-800 dark:text-slate-200">{sub.start_date}</span>
                    </div>
                    <div>
                      <span className="text-slate-400 block text-[11px]">Expiry / Renewal</span>
                      <span className="font-medium text-slate-800 dark:text-slate-200">{sub.expiry_date || 'Ongoing'}</span>
                    </div>
                  </div>
                </CardContent>
              </div>

              {/* Action Buttons */}
              <div className="p-4 border-t border-slate-100 dark:border-slate-800/60 bg-slate-50/50 dark:bg-slate-900/50 flex flex-wrap items-center gap-2">
                <Button
                  size="sm"
                  variant="primary"
                  leftIcon={<ArrowUpRight className="w-3.5 h-3.5" />}
                  onClick={() => openActionModal(sub, 'UPGRADE')}
                >
                  Upgrade
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => openActionModal(sub, 'DOWNGRADE')}
                >
                  Downgrade
                </Button>
                {sub.status === 'ACTIVE' ? (
                  <Button
                    size="sm"
                    variant="ghost"
                    leftIcon={<PauseCircle className="w-3.5 h-3.5" />}
                    onClick={() => openActionModal(sub, 'PAUSE')}
                  >
                    Pause
                  </Button>
                ) : (
                  <Button
                    size="sm"
                    variant="ghost"
                    leftIcon={<RefreshCw className="w-3.5 h-3.5" />}
                    onClick={() => openActionModal(sub, 'RENEWAL')}
                  >
                    Resume
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="danger"
                  className="ml-auto"
                  leftIcon={<XCircle className="w-3.5 h-3.5" />}
                  onClick={() => openActionModal(sub, 'CANCEL')}
                >
                  Cancel
                </Button>
              </div>
            </Card>
          ))
        )}
      </div>

      {/* Customer Request History Table */}
      <Card>
        <CardHeader>
          <CardTitle>My Modification Requests</CardTitle>
          <p className="text-xs text-slate-500">History of submitted plan changes and staff decisions</p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-600 dark:text-slate-300">
              <thead className="bg-slate-50 dark:bg-slate-800 text-slate-400 uppercase font-semibold">
                <tr>
                  <th className="px-4 py-3">Request ID</th>
                  <th className="px-4 py-3">Type</th>
                  <th className="px-4 py-3">Target Plan</th>
                  <th className="px-4 py-3">Created</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3">Staff Note</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {!requests.length ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-slate-400">
                      No change requests submitted yet.
                    </td>
                  </tr>
                ) : (
                  requests.map((r) => (
                    <tr key={r.id}>
                      <td className="px-4 py-3 font-mono font-medium text-slate-900 dark:text-slate-100">
                        #{r.id.substring(0, 8)}
                      </td>
                      <td className="px-4 py-3 font-semibold">{r.type}</td>
                      <td className="px-4 py-3">{r.target_plan_id || '—'}</td>
                      <td className="px-4 py-3">{r.created_at.split('T')[0]}</td>
                      <td className="px-4 py-3">
                        <Badge
                          variant={
                            r.status === 'APPLIED' || r.status === 'APPROVED'
                              ? 'success'
                              : r.status === 'PENDING'
                              ? 'warning'
                              : 'danger'
                          }
                          size="sm"
                          dot
                        >
                          {r.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-500">{r.decision_note || r.note || '—'}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Subscription Request Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Request ${requestType} for ${activeSub?.number}`}
        description="Your request will be submitted to our operations team for review."
        footer={
          <>
            <Button variant="ghost" onClick={() => setIsModalOpen(false)}>
              Dismiss
            </Button>
            <Button
              variant={requestType === 'CANCEL' ? 'danger' : 'primary'}
              onClick={handleRequestSubmit}
              isLoading={isSubmitting}
            >
              Submit Request
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="p-3 rounded-xl bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 text-xs space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Current Plan:</span>
              <span className="font-semibold">{activeSub?.plan_name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Action:</span>
              <span className="font-semibold text-brand-600">{requestType}</span>
            </div>
          </div>

          {(requestType === 'UPGRADE' || requestType === 'DOWNGRADE') && (
            <Select
              label="Select Target Plan"
              options={planOptions}
              value={targetPlanId}
              onChange={(e) => setTargetPlanId(e.target.value)}
            />
          )}

          <Input
            label="Rationale / Special Instructions (Optional)"
            placeholder="Add any specific requirements for our billing team..."
            value={requestNote}
            onChange={(e) => setRequestNote(e.target.value)}
          />

          <p className="text-[11px] text-slate-400">
            Note: Standard terms apply. Rate adjustments take effect on the agreed effective date.
          </p>
        </div>
      </Modal>
    </div>
  );
};
