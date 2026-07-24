import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { ModuleDetailModel } from '../../types';

interface DrillDownProps {
  detail: ModuleDetailModel;
}

function DrillDown({ detail }: DrillDownProps) {
  const { module, stories, bugs, recommendations } = detail;

  return (
    <Card title={`${module.name} drill-down`} subtitle={module.summary}>
      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <div className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              <p className="text-xs text-slate-500">Quality index</p>
              <p className="mt-2 text-3xl font-semibold text-slate-50">{module.qualityIndex}</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              <p className="text-xs text-slate-500">Coverage</p>
              <p className="mt-2 text-3xl font-semibold text-slate-50">{module.coverage}%</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
              <p className="text-xs text-slate-500">Escaped defects</p>
              <p className="mt-2 text-3xl font-semibold text-slate-50">{module.escapedDefects}</p>
            </div>
          </div>

          <div className="rounded-2xl border border-white/8 bg-slate-950/30 p-4">
            <p className="text-sm font-semibold text-slate-100">Open stories</p>
            <div className="mt-3 space-y-3">
              {stories.map((story) => (
                <div key={story.id} className="rounded-2xl border border-white/8 bg-white/5 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <p className="text-sm font-medium text-slate-100">{story.id} — {story.title}</p>
                    <Badge tone={story.risk === 'High' ? 'danger' : story.risk === 'Medium' ? 'warning' : 'success'}>{story.status}</Badge>
                  </div>
                  <p className="mt-2 text-xs leading-5 text-slate-400">{story.qaSignal}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div className="rounded-2xl border border-white/8 bg-slate-950/30 p-4">
            <p className="text-sm font-semibold text-slate-100">Active bugs</p>
            <div className="mt-3 space-y-3">
              {bugs.map((bug) => (
                <div key={bug.id} className="rounded-2xl border border-white/8 bg-white/5 p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-sm font-medium text-slate-100">{bug.id}</p>
                    <Badge tone={bug.severity === 'Critical' || bug.severity === 'High' ? 'danger' : bug.severity === 'Medium' ? 'warning' : 'info'}>
                      {bug.severity}
                    </Badge>
                  </div>
                  <p className="mt-2 text-sm text-slate-300">{bug.title}</p>
                  <p className="mt-2 text-xs text-slate-500">{bug.origin}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/8 bg-white/5 p-4">
            <p className="text-sm font-semibold text-slate-100">Recommended next actions</p>
            <ul className="mt-3 space-y-3 text-sm leading-6 text-slate-300">
              {recommendations.map((item) => (
                <li key={item} className="flex gap-3">
                  <span className="mt-2 h-2 w-2 rounded-full bg-cyan-300" />
                  <span>{item}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
}

export default DrillDown;
