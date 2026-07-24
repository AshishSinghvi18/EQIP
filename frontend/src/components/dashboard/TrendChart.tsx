import React from 'react';
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import Card from '../common/Card';
import { TrendDatum } from '../../types';

interface TrendChartProps {
  data: TrendDatum[];
}

function TrendChart({ data }: TrendChartProps) {
  return (
    <Card title="Quality trend" subtitle="Release quality index versus escaped defects over time.">
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 8, right: 8, left: -18, bottom: 8 }}>
            <CartesianGrid stroke="rgba(148,163,184,0.08)" vertical={false} />
            <XAxis dataKey="sprint" stroke="#64748b" tickLine={false} axisLine={false} />
            <YAxis yAxisId="left" stroke="#06b6d4" tickLine={false} axisLine={false} />
            <YAxis yAxisId="right" orientation="right" stroke="#8b5cf6" tickLine={false} axisLine={false} />
            <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(148,163,184,0.18)', borderRadius: '1rem' }} />
            <Line yAxisId="left" type="monotone" dataKey="qualityIndex" stroke="#06b6d4" strokeWidth={3} dot={{ r: 4, fill: '#06b6d4' }} />
            <Line yAxisId="right" type="monotone" dataKey="escapedDefects" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 4, fill: '#8b5cf6' }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}

export default TrendChart;
