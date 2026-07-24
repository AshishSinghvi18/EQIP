import React from 'react';
import { NavLink } from 'react-router-dom';
import { Activity, AlertTriangle, ChevronRight, LayoutDashboard, Medal, PanelsTopLeft, ScrollText } from 'lucide-react';
import clsx from 'clsx';

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/modules/payments', label: 'Module View', icon: PanelsTopLeft },
  { to: '/team', label: 'Team View', icon: Medal },
  { to: '/stories', label: 'Stories', icon: ScrollText },
  { to: '/bugs', label: 'Bugs', icon: AlertTriangle },
];

function Sidebar() {
  return (
    <aside className="glass-card flex w-full flex-col p-5 xl:sticky xl:top-6 xl:h-[calc(100vh-3rem)] xl:max-w-[280px]">
      <div className="flex items-center gap-3 border-b border-white/10 pb-5">
        <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-500 shadow-cyan">
          <Activity className="h-6 w-6 text-slate-950" />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-200">EQIP</p>
          <p className="text-xs text-slate-400">Engineering Quality Intelligence</p>
        </div>
      </div>

      <nav className="mt-6 flex flex-1 flex-col gap-2 md:flex-row md:flex-wrap xl:flex-col">
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              clsx(
                'group flex items-center justify-between rounded-2xl px-4 py-3 text-sm font-medium transition',
                isActive
                  ? 'bg-cyan-400/12 text-cyan-200 ring-1 ring-cyan-400/30'
                  : 'text-slate-400 hover:bg-white/5 hover:text-slate-100',
              )
            }
          >
            <span className="flex items-center gap-3">
              <Icon className="h-4 w-4" />
              {label}
            </span>
            <ChevronRight className="h-4 w-4 opacity-50 transition group-hover:translate-x-0.5" />
          </NavLink>
        ))}
      </nav>

      <div className="mt-4 rounded-2xl border border-cyan-400/10 bg-cyan-400/5 p-4">
        <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-200/80">Release posture</p>
        <p className="mt-2 text-sm text-slate-300">24 release checks passing • 2 modules need escalation.</p>
      </div>
    </aside>
  );
}

export default Sidebar;
