import React from 'react';
import { Bell, Search, Sparkles } from 'lucide-react';
import { useLocation } from 'react-router-dom';
import Badge from '../common/Badge';

const titles: Record<string, { title: string; subtitle: string }> = {
  '/': {
    title: 'Executive quality command center',
    subtitle: 'See release health, defect flow, and team performance in one place.',
  },
  '/team': {
    title: 'Team quality leaderboard',
    subtitle: 'Spot who is catching the most risk before it reaches customers.',
  },
  '/stories': {
    title: 'Story readiness',
    subtitle: 'Track delivery risk, QA signal, and due dates across squads.',
  },
  '/bugs': {
    title: 'Bug intelligence',
    subtitle: 'Prioritize defects by severity, origin, and containment status.',
  },
};

function Header() {
  const location = useLocation();
  const key = location.pathname.startsWith('/modules/') ? '/modules' : location.pathname;
  const content =
    key === '/modules'
      ? {
          title: 'Module drill-down',
          subtitle: 'Deep dive into quality signals, open defects, and mitigation opportunities.',
        }
      : titles[key] ?? titles['/'];

  return (
    <header className="glass-card mb-6 p-5 md:p-6">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
        <div>
          <p className="eyebrow">Premium analytics workspace</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-50">{content.title}</h1>
          <p className="mt-2 max-w-2xl text-sm text-slate-400">{content.subtitle}</p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="flex items-center gap-3 rounded-2xl border border-white/10 bg-slate-950/30 px-4 py-3 text-sm text-slate-400 sm:min-w-[280px]">
            <Search className="h-4 w-4 text-slate-500" />
            <input
              className="w-full bg-transparent text-sm text-slate-100 outline-none placeholder:text-slate-500"
              placeholder="Search modules, stories, or bugs"
            />
          </label>

          <div className="flex items-center gap-3">
            <button className="relative rounded-2xl border border-white/10 bg-white/5 p-3 text-slate-300 transition hover:border-cyan-400/40 hover:text-cyan-200">
              <Bell className="h-4 w-4" />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-cyan-400" />
            </button>
            <div className="rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-right">
              <div className="flex items-center justify-end gap-2">
                <Sparkles className="h-4 w-4 text-cyan-300" />
                <Badge>Platform owner</Badge>
              </div>
              <p className="mt-2 text-sm font-semibold text-slate-100">Avery Morgan</p>
              <p className="text-xs text-slate-500">Director of Engineering Quality</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

export default Header;
