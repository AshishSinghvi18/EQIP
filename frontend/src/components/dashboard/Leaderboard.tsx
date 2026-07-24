import React from 'react';
import Card from '../common/Card';
import Badge from '../common/Badge';
import { LeaderboardEntry } from '../../types';

interface LeaderboardProps {
  entries: LeaderboardEntry[];
}

function Leaderboard({ entries }: LeaderboardProps) {
  return (
    <Card title="Quality leaderboard" subtitle="Fact-based recognition for who is reducing customer-visible risk.">
      <div className="space-y-4">
        {entries.map((entry, index) => (
          <div key={entry.id} className="flex flex-col gap-4 rounded-3xl border border-white/10 bg-white/5 p-4 md:flex-row md:items-center md:justify-between">
            <div className="flex items-start gap-4">
              <div className={`flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br ${entry.avatarColor} text-base font-bold text-slate-950`}>
                {entry.name
                  .split(' ')
                  .map((part) => part[0])
                  .join('')
                  .slice(0, 2)}
              </div>
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <p className="text-sm font-semibold text-slate-100">#{index + 1} {entry.name}</p>
                  <Badge tone={entry.escapedDefects === 0 ? 'success' : 'warning'}>{entry.score} score</Badge>
                </div>
                <p className="mt-1 text-sm text-slate-400">{entry.role} • {entry.squad}</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{entry.evidence}</p>
              </div>
            </div>
            <div className="grid min-w-[200px] grid-cols-2 gap-3 text-sm">
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-3">
                <p className="text-xs text-slate-500">Critical bugs caught</p>
                <p className="mt-1 text-xl font-semibold text-slate-50">{entry.criticalBugsCaught}</p>
              </div>
              <div className="rounded-2xl border border-white/8 bg-slate-950/35 p-3">
                <p className="text-xs text-slate-500">Escaped defects</p>
                <p className="mt-1 text-xl font-semibold text-slate-50">{entry.escapedDefects}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default Leaderboard;
