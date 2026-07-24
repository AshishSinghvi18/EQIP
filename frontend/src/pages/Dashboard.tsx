import React, { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ShieldCheck } from 'lucide-react';
import {
  useBugBreakdownQuery,
  useBugsQuery,
  useChainQuery,
  useDashboardSummaryQuery,
  useLeaderboardQuery,
  useModulesQuery,
  useRootCauseBreakdownQuery,
  useStoriesQuery,
  useTrendQuery,
} from '../api/hooks';
import Badge from '../components/common/Badge';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import BugBreakdown from '../components/dashboard/BugBreakdown';
import ChainView from '../components/dashboard/ChainView';
import DrillDown from '../components/dashboard/DrillDown';
import Leaderboard from '../components/dashboard/Leaderboard';
import ModuleHeatmap from '../components/dashboard/ModuleHeatmap';
import QualityCards from '../components/dashboard/QualityCards';
import RootCauseBreakdown from '../components/dashboard/RootCauseBreakdown';
import TrendChart from '../components/dashboard/TrendChart';
import { BugItem, DashboardSummary, ModuleQuality, StoryItem } from '../types';

function Dashboard() {
  const summaryQuery = useDashboardSummaryQuery();
  const modulesQuery = useModulesQuery();
  const bugBreakdownQuery = useBugBreakdownQuery();
  const rootCauseQuery = useRootCauseBreakdownQuery();
  const trendQuery = useTrendQuery();
  const chainQuery = useChainQuery();
  const leaderboardQuery = useLeaderboardQuery();
  const storiesQuery = useStoriesQuery();
  const bugsQuery = useBugsQuery();
  const [selectedModuleId, setSelectedModuleId] = useState<string>();

  const modules: ModuleQuality[] = useMemo(() => modulesQuery.data?.data ?? [], [modulesQuery.data]);
  const stories: StoryItem[] = useMemo(() => storiesQuery.data?.data ?? [], [storiesQuery.data]);
  const bugs: BugItem[] = useMemo(() => bugsQuery.data?.data ?? [], [bugsQuery.data]);
  const selectedModule: ModuleQuality | undefined = useMemo(
    () => modules.find((module) => module.id === selectedModuleId) ?? modules[0],
    [modules, selectedModuleId],
  );

  useEffect(() => {
    if (!selectedModuleId && modules[0]) {
      setSelectedModuleId(modules[0].id);
    }
  }, [modules, selectedModuleId]);

  if (
    summaryQuery.isLoading ||
    modulesQuery.isLoading ||
    bugBreakdownQuery.isLoading ||
    rootCauseQuery.isLoading ||
    trendQuery.isLoading ||
    chainQuery.isLoading ||
    leaderboardQuery.isLoading ||
    storiesQuery.isLoading ||
    bugsQuery.isLoading
  ) {
    return <LoadingSpinner />;
  }

  const summary: DashboardSummary | undefined = summaryQuery.data?.data;
  const selectedDetail = selectedModule
    ? {
        module: selectedModule,
        stories: stories.filter((story) => story.module === selectedModule.name),
        bugs: bugs.filter((bug) => bug.module === selectedModule.name),
        recommendations: [selectedModule.topIssue, selectedModule.summary],
      }
    : undefined;

  if (!summary || !selectedModule || !selectedDetail) {
    return <LoadingSpinner label="Preparing EQIP dashboard…" />;
  }

  return (
    <div className="space-y-6">
      <Card className="bg-hero-gradient">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
          <div className="max-w-3xl">
            <div className="flex flex-wrap items-center gap-3">
              <Badge tone="success">{summaryQuery.data?.source === 'api' ? 'Live API data' : 'Mock data fallback'}</Badge>
              <Badge>Next release gate in 18h</Badge>
            </div>
            <h2 className="mt-4 text-4xl font-semibold tracking-tight text-slate-50 md:text-5xl">
              Engineering Quality <span className="text-gradient">Intelligence Platform</span>
            </h2>
            <p className="mt-4 max-w-2xl text-base leading-7 text-slate-300">
              Premium release intelligence for engineering leaders: track quality posture, defect propagation, and the teams preventing customer-visible incidents.
            </p>
          </div>

          <div className="grid gap-3 sm:grid-cols-3 xl:min-w-[440px]">
            {summary.highlights.map((highlight) => (
              <div key={highlight} className="rounded-3xl border border-white/10 bg-slate-950/35 p-4 text-sm leading-6 text-slate-300">
                <ShieldCheck className="mb-3 h-5 w-5 text-cyan-300" />
                {highlight}
              </div>
            ))}
          </div>
        </div>
      </Card>

      <QualityCards summary={summary} />

      <div className="grid gap-6 2xl:grid-cols-[1.3fr_0.9fr]">
        <ModuleHeatmap
          modules={modules}
          selectedModuleId={selectedModule.id}
          onSelect={(module) => setSelectedModuleId(module.id)}
        />
        <Card title="Selected module focus" subtitle="Fast path into the area with the strongest or weakest signal.">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="eyebrow">{selectedModule.team}</p>
                <p className="mt-2 text-3xl font-semibold text-slate-50">{selectedModule.name}</p>
              </div>
              <Badge tone={selectedModule.riskLevel === 'good' ? 'success' : selectedModule.riskLevel === 'warning' ? 'warning' : 'danger'}>
                Quality {selectedModule.qualityIndex}
              </Badge>
            </div>
            <p className="mt-4 text-sm leading-6 text-slate-300">{selectedModule.summary}</p>
            <div className="mt-5 grid grid-cols-3 gap-3 text-sm">
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-3">
                <p className="text-xs text-slate-500">Coverage</p>
                <p className="mt-1 text-xl font-semibold text-slate-50">{selectedModule.coverage}%</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-3">
                <p className="text-xs text-slate-500">Open bugs</p>
                <p className="mt-1 text-xl font-semibold text-slate-50">{selectedModule.openBugs}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-3">
                <p className="text-xs text-slate-500">Velocity</p>
                <p className="mt-1 text-xl font-semibold text-slate-50">{selectedModule.velocity}</p>
              </div>
            </div>
            <Link
              to={`/modules/${selectedModule.id}`}
              className="mt-5 inline-flex items-center gap-2 rounded-2xl border border-cyan-400/30 bg-cyan-400/10 px-4 py-3 text-sm font-medium text-cyan-200 transition hover:border-cyan-300/50 hover:bg-cyan-400/15"
            >
              Open module drill-down
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </Card>
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <TrendChart data={trendQuery.data?.data ?? []} />
        <BugBreakdown data={bugBreakdownQuery.data?.data ?? []} />
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <RootCauseBreakdown data={rootCauseQuery.data?.data ?? []} />
        <ChainView stages={chainQuery.data?.data ?? []} />
      </div>

      <Leaderboard entries={leaderboardQuery.data?.data ?? []} />
      <DrillDown detail={selectedDetail} />
    </div>
  );
}

export default Dashboard;
