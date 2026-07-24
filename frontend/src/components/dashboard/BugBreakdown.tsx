import React from 'react';
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';
import Card from '../common/Card';
import { BugBreakdownDatum } from '../../types';

interface BugBreakdownProps {
  data: BugBreakdownDatum[];
}

const COLORS = ['#06b6d4', '#8b5cf6', '#22c55e', '#f59e0b', '#ef4444'];

function BugBreakdown({ data }: BugBreakdownProps) {
  return (
    <Card title="Bug type breakdown" subtitle="Where current defect volume is concentrating.">
      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={68} outerRadius={100} paddingAngle={3}>
              {data.map((entry, index) => (
                <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#0f172a',
                border: '1px solid rgba(148,163,184,0.18)',
                borderRadius: '1rem',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {data.map((item, index) => (
          <div key={item.name} className="flex items-center justify-between rounded-2xl border border-white/8 bg-white/5 px-4 py-3 text-sm">
            <div className="flex items-center gap-3">
              <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
              <span className="text-slate-300">{item.name}</span>
            </div>
            <span className="font-semibold text-slate-50">{item.value}%</span>
          </div>
        ))}
      </div>
    </Card>
  );
}

export default BugBreakdown;
