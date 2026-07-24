import React from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import Card from '../common/Card';
import { RootCauseDatum } from '../../types';

interface RootCauseBreakdownProps {
  data: RootCauseDatum[];
}

function RootCauseBreakdown({ data }: RootCauseBreakdownProps) {
  return (
    <Card title="Root cause analysis" subtitle="Most frequent causes behind active quality erosion.">
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 8, right: 8, left: 20, bottom: 8 }}>
            <CartesianGrid stroke="rgba(148,163,184,0.08)" horizontal={false} />
            <XAxis type="number" stroke="#64748b" tickLine={false} axisLine={false} />
            <YAxis type="category" dataKey="name" stroke="#94a3b8" tickLine={false} axisLine={false} width={140} />
            <Tooltip
              cursor={{ fill: 'rgba(148,163,184,0.08)' }}
              contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(148,163,184,0.18)', borderRadius: '1rem' }}
            />
            <Bar dataKey="value" radius={[0, 12, 12, 0]} fill="#8b5cf6" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export default RootCauseBreakdown;
