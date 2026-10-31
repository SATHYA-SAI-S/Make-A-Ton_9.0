import React from 'react';
import { Download, RefreshCw, AlertTriangle, Inbox } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/shared/ui/Card';
import { Button } from '@/shared/ui/Button';

export interface ChartCardProps {
  title: string;
  description?: string;
  isLoading?: boolean;
  isError?: boolean;
  isEmpty?: boolean;
  onRefresh?: () => void;
  onExport?: () => void;
  headerAction?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const ChartCard: React.FC<ChartCardProps> = ({
  title,
  description,
  isLoading = false,
  isError = false,
  isEmpty = false,
  onRefresh,
  onExport,
  headerAction,
  children,
  className = '',
}) => {
  return (
    <Card className={`overflow-hidden ${className}`}>
      <CardHeader className="flex flex-row items-center justify-between pb-4">
        <div>
          <CardTitle>{title}</CardTitle>
          {description && <CardDescription>{description}</CardDescription>}
        </div>

        <div className="flex items-center gap-2">
          {headerAction}
          {onRefresh && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onRefresh}
              disabled={isLoading}
              title="Refresh dataset"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            </Button>
          )}
          {onExport && (
            <Button
              variant="outline"
              size="sm"
              onClick={onExport}
              disabled={isLoading || isEmpty || isError}
              leftIcon={<Download className="w-3.5 h-3.5" />}
            >
              Export
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent className="min-h-[320px] flex items-center justify-center relative">
        {isLoading ? (
          <div className="w-full space-y-4 animate-pulse">
            <div className="h-4 bg-slate-200 dark:bg-slate-800 rounded w-1/4"></div>
            <div className="h-56 bg-slate-100 dark:bg-slate-800/60 rounded-xl"></div>
          </div>
        ) : isError ? (
          <div className="text-center py-12 space-y-3">
            <div className="w-10 h-10 rounded-full bg-rose-50 dark:bg-rose-950/60 text-rose-500 mx-auto flex items-center justify-center">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-200">
              Failed to load analytics data
            </p>
            {onRefresh && (
              <Button size="sm" variant="outline" onClick={onRefresh}>
                Retry
              </Button>
            )}
          </div>
        ) : isEmpty ? (
          <div className="text-center py-12 space-y-2">
            <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 text-slate-400 mx-auto flex items-center justify-center">
              <Inbox className="w-5 h-5" />
            </div>
            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">
              No matching records for current filter criteria
            </p>
          </div>
        ) : (
          <div className="w-full h-full min-h-[300px]">{children}</div>
        )}
      </CardContent>
    </Card>
  );
};
