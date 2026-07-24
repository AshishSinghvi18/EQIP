import React from 'react';
import { useBugBreakdownQuery, useBugsQuery } from '../api/hooks';
import Badge from '../components/common/Badge';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import BugBreakdown from '../components/dashboard/BugBreakdown';
import { BugItem } from '../types';

function Bugs() {
  const bugsQuery = useBugsQuery();
  const bugBreakdownQuery = useBugBreakdownQuery();

  if (bugsQuery.isLoading || bugBreakdownQuery.isLoading) {
    return <LoadingSpinner label="Loading defect intelligence…" />;
  }

  const bugs: BugItem[] = bugsQuery.data?.data ?? [];

  return (
    <div className="space-y-6">
      <BugBreakdown data={bugBreakdownQuery.data?.data ?? []} />
      <Card title="Active defect ledger" subtitle="Severity, origin, and containment status across the release train.">
        <div className="grid gap-4 xl:grid-cols-2">
          {bugs.map((bug) => (
            <div key={bug.id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold text-slate-100">{bug.id}</p>
                  <p className="mt-1 text-sm text-slate-400">{bug.module}</p>
                </div>
                <div className="flex gap-2">
                  <Badge tone={bug.severity === 'Critical' || bug.severity === 'High' ? 'danger' : bug.severity === 'Medium' ? 'warning' : 'info'}>{bug.severity}</Badge>
                  <Badge>{bug.status}</Badge>
                </div>
              </div>
              <p className="mt-4 text-base font-medium text-slate-50">{bug.title}</p>
              <div className="mt-4 grid gap-3 sm:grid-cols-3 text-sm text-slate-400">
                <div>
                  <p className="text-xs text-slate-500">Origin</p>
                  <p className="mt-1 text-slate-300">{bug.origin}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Owner</p>
                  <p className="mt-1 text-slate-300">{bug.owner}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Created</p>
                  <p className="mt-1 text-slate-300">{bug.createdAt}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

export default Bugs;
