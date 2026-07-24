import React from 'react';
import clsx from 'clsx';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { ModuleQuality } from '../../types';

interface ModuleHeatmapProps {
  modules: ModuleQuality[];
  selectedModuleId?: string;
  onSelect?: (module: ModuleQuality) => void;
}

const levelStyles = {
  good: 'from-emerald-500/30 to-cyan-400/20 border-emerald-400/20',
  warning: 'from-amber-500/30 to-orange-400/15 border-amber-300/20',
  bad: 'from-rose-500/30 to-red-400/15 border-rose-400/20',
};

function ModuleHeatmap({ modules, selectedModuleId, onSelect }: ModuleHeatmapProps) {
  return (
    <Card
      title="Module quality heatmap"
      subtitle="Color intensity reflects current quality health across the platform."
      action={<Badge>{modules.length} modules monitored</Badge>}
    >
      <div className="mb-5 flex flex-wrap gap-3 text-xs text-slate-400">
        <span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-emerald-400" /> Good</span>
        <span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-amber-400" /> Watchlist</span>
        <span className="inline-flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full bg-rose-400" /> High risk</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {modules.map((module) => (
          <button
            key={module.id}
            type="button"
            onClick={() => onSelect?.(module)}
            className={clsx(
              'heatmap-cell rounded-2xl border bg-gradient-to-br p-4 text-left',
              levelStyles[module.riskLevel],
              selectedModuleId === module.id && 'ring-2 ring-cyan-300/70',
            )}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-slate-50">{module.name}</p>
                <p className="mt-1 text-xs text-slate-300/80">{module.team}</p>
              </div>
              <Badge tone={module.riskLevel === 'good' ? 'success' : module.riskLevel === 'warning' ? 'warning' : 'danger'}>
                {module.qualityIndex}
              </Badge>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3 text-sm text-slate-200">
              <div>
                <p className="text-xs text-slate-400">Coverage</p>
                <p className="mt-1 font-semibold">{module.coverage}%</p>
              </div>
              <div>
                <p className="text-xs text-slate-400">Open bugs</p>
                <p className="mt-1 font-semibold">{module.openBugs}</p>
              </div>
            </div>
            <p className="mt-4 text-xs leading-5 text-slate-300/80">{module.topIssue}</p>
          </button>
        ))}
      </div>
    </Card>
  );
}

export default ModuleHeatmap;
