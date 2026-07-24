import React from 'react';
import Card from '../common/Card';
import { ChainStage } from '../../types';

interface ChainViewProps {
  stages: ChainStage[];
}

function ChainView({ stages }: ChainViewProps) {
  return (
    <Card title="Defect origin chain" subtitle="A flow view of where risk starts, how it is detected, and where it lands.">
      <div className="grid gap-4 xl:grid-cols-3">
        {stages.map((stage) => (
          <div key={stage.stage} className="rounded-2xl border border-white/10 bg-slate-950/25 p-4">
            <p className="text-sm font-semibold text-slate-100">{stage.stage}</p>
            <div className="mt-4 space-y-3">
              {stage.connections.map((connection) => (
                <div key={`${stage.stage}-${connection.target}`} className="rounded-2xl border border-white/8 bg-white/5 p-3">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-sm font-medium text-slate-200">{connection.target}</span>
                    <span className="text-sm font-semibold text-cyan-300">{connection.value}</span>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-800/80">
                    <div className="flow-line h-full rounded-full" style={{ width: `${Math.min(connection.value * 3.2, 100)}%` }} />
                  </div>
                  <p className="mt-3 text-xs leading-5 text-slate-400">{connection.evidence}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default ChainView;
