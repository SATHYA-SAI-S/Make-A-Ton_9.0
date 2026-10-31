import React, { useEffect, useState } from 'react';
import { Clock, CheckCircle2, AlertCircle, ArrowUpRight, RefreshCw } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge, useToast } from '@/shared/ui';
import { portalApi } from '../../api/portalApi';
import { Subscription } from '../../types/portal';

export const SubscriptionTimeline: React.FC = () => {
  const { toast } = useToast();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    portalApi
      .getSubscriptions('ALL')
      .then((res) => setSubscriptions(res))
      .catch((err) => toast.error('Failed to load timeline', err.message))
      .finally(() => setIsLoading(false));
  }, []);

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-100">
          Subscription Activity Timeline
        </h1>
        <p className="text-xs text-slate-500">
          Chronological audit trail of subscription activations, modifications, renewals, and invoice occurrences.
        </p>
      </div>

      <div className="space-y-6">
        {isLoading ? (
          <div className="py-12 text-center text-xs text-slate-400">Loading timeline events...</div>
        ) : (
          subscriptions.map((sub) => (
            <Card key={sub.id}>
              <CardHeader className="flex flex-row items-center justify-between pb-3">
                <div>
                  <CardTitle>{sub.plan_name}</CardTitle>
                  <p className="text-xs text-slate-400 font-mono mt-0.5">{sub.number}</p>
                </div>
                <Badge variant={sub.status === 'ACTIVE' ? 'success' : 'warning'} size="sm" dot>
                  {sub.status}
                </Badge>
              </CardHeader>
              <CardContent className="pt-2">
                <ol className="relative border-l border-slate-200 dark:border-slate-800 ml-3 space-y-4">
                  {sub.timeline?.map((evt, idx) => (
                    <li key={idx} className="ml-6">
                      <span className="absolute -left-2.5 flex items-center justify-center w-5 h-5 rounded-full bg-brand-50 dark:bg-brand-950 border border-brand-500 text-brand-600 dark:text-brand-300">
                        <CheckCircle2 className="w-3 h-3" />
                      </span>
                      <div className="flex items-baseline justify-between gap-4">
                        <h4 className="text-xs font-semibold text-slate-800 dark:text-slate-200">{evt.event}</h4>
                        <time className="text-[10px] text-slate-400 shrink-0">{evt.date}</time>
                      </div>
                    </li>
                  ))}
                  <li className="ml-6">
                    <span className="absolute -left-2.5 flex items-center justify-center w-5 h-5 rounded-full bg-emerald-50 dark:bg-emerald-950 border border-emerald-500 text-emerald-600">
                      <Clock className="w-3 h-3" />
                    </span>
                    <div className="flex items-baseline justify-between gap-4">
                      <h4 className="text-xs font-semibold text-emerald-600 dark:text-emerald-400">
                        Active Billed Cycle Running
                      </h4>
                      <time className="text-[10px] text-slate-400 shrink-0">Current</time>
                    </div>
                  </li>
                </ol>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  );
};
