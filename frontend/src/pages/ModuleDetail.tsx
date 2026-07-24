import React from 'react';
import { useParams } from 'react-router-dom';
import { useModuleQuery, useModulesQuery, useTrendQuery } from '../api/hooks';
import Badge from '../components/common/Badge';
import Card from '../components/common/Card';
import LoadingSpinner from '../components/common/LoadingSpinner';
import DrillDown from '../components/dashboard/DrillDown';
import ModuleHeatmap from '../components/dashboard/ModuleHeatmap';
import TrendChart from '../components/dashboard/TrendChart';
import { ModuleQuality } from '../types';

function ModuleDetail() {
  const { moduleId = 'payments' } = useParams();
  const moduleQuery = useModuleQuery(moduleId);
  const modulesQuery = useModulesQuery();
  const trendQuery = useTrendQuery();

  if (moduleQuery.isLoading || modulesQuery.isLoading || trendQuery.isLoading) {
    return <LoadingSpinner label="Loading module drill-down…" />;
  }

  const detail = moduleQuery.data?.data;
  const modules: ModuleQuality[] = modulesQuery.data?.data ?? [];

  if (!detail) {
    return <LoadingSpinner label="Module insights unavailable…" />;
  }

  return (
    <div className="space-y-6">
      <Card>
        <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="eyebrow">{detail.module.team}</p>
            <h2 className="mt-2 text-4xl font-semibold text-slate-50">{detail.module.name}</h2>
            <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-300">{detail.module.summary}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Badge tone={detail.module.riskLevel === 'good' ? 'success' : detail.module.riskLevel === 'warning' ? 'warning' : 'danger'}>
              {detail.module.riskLevel.toUpperCase()} RISK
            </Badge>
            <Badge>Escaped defects {detail.module.escapedDefects}</Badge>
            <Badge>Defect density {detail.module.defectDensity}/KLOC</Badge>
          </div>
        </div>
      </Card>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <DrillDown detail={detail} />
        <ModuleHeatmap modules={modules} selectedModuleId={detail.module.id} />
      </div>

      <TrendChart data={trendQuery.data?.data ?? []} />
    </div>
  );
}

export default ModuleDetail;
