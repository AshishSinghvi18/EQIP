import React from 'react';
import { useLeaderboardQuery, useModulesQuery } from '../api/hooks';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import Leaderboard from '../components/dashboard/Leaderboard';
import { LeaderboardEntry, ModuleQuality } from '../types';

function TeamView() {
  const leaderboardQuery = useLeaderboardQuery();
  const modulesQuery = useModulesQuery();

  if (leaderboardQuery.isLoading || modulesQuery.isLoading) {
    return <LoadingSpinner label="Loading team insights…" />;
  }

  const entries: LeaderboardEntry[] = leaderboardQuery.data?.data ?? [];
  const modules: ModuleQuality[] = modulesQuery.data?.data ?? [];

  return (
    <div className="space-y-6">
      <Card title="Squad health distribution" subtitle="How teams are performing across the monitored module landscape.">
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {modules.map((module) => (
            <div key={module.id} className="rounded-3xl border border-white/10 bg-white/5 p-5">
              <p className="text-sm text-slate-400">{module.team}</p>
              <p className="mt-2 text-2xl font-semibold text-slate-50">{module.name}</p>
              <div className="mt-4 flex items-end justify-between gap-4">
                <div>
                  <p className="text-xs text-slate-500">Quality index</p>
                  <p className="mt-1 text-3xl font-semibold text-slate-50">{module.qualityIndex}</p>
                </div>
                <div className="text-right text-sm text-slate-300">
                  <p>{module.coverage}% coverage</p>
                  <p>{module.openBugs} active bugs</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </Card>
      <Leaderboard entries={entries} />
    </div>
  );
}

export default TeamView;
