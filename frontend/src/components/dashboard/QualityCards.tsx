import React from 'react';
import { ArrowDownRight, ArrowRight, ArrowUpRight } from 'lucide-react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { DashboardSummary, TrendDirection } from '../../types';

interface QualityCardsProps {
  summary: DashboardSummary;
}

const trendIcon: Record<TrendDirection, React.ReactNode> = {
  up: <ArrowUpRight className="h-4 w-4" />,
  down: <ArrowDownRight className="h-4 w-4" />,
  flat: <ArrowRight className="h-4 w-4" />,
};

const toneMap = {
  success: 'success' as const,
  warning: 'warning' as const,
  danger: 'danger' as const,
  info: 'info' as const,
};

function QualityCards({ summary }: QualityCardsProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2 2xl:grid-cols-4">
      {summary.metrics.map((metric) => (
        <Card key={metric.id} className="metric-glow">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm text-slate-400">{metric.title}</p>
              <p className="mt-3 text-4xl font-semibold tracking-tight text-slate-50">{metric.value}</p>
            </div>
            <Badge tone={toneMap[metric.tone]} className="gap-1.5">
              {trendIcon[metric.trend]}
              {metric.delta}
            </Badge>
          </div>
          <p className="mt-4 text-sm leading-6 text-slate-400">{metric.description}</p>
        </Card>
      ))}
    </div>
  );
}

export default QualityCards;
