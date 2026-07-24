import { useQuery } from '@tanstack/react-query';
import { ApiResult, requestWithFallback } from './client';
import {
  BugBreakdownDatum,
  BugItem,
  ChainStage,
  DashboardSummary,
  LeaderboardEntry,
  ModuleDetailModel,
  ModuleQuality,
  RootCauseDatum,
  StoryItem,
  TrendDatum,
} from '../types';

const dashboardSummaryFallback: DashboardSummary = {
  metrics: [
    {
      id: 'quality-index',
      title: 'Quality Index',
      value: '92.4',
      delta: '+4.8%',
      trend: 'up',
      description: 'Composite score across defects, coverage, and release confidence.',
      tone: 'success',
    },
    {
      id: 'sprint-quality',
      title: 'Sprint Quality',
      value: '88.1',
      delta: '+2.1 pts',
      trend: 'up',
      description: 'Weighted sprint readiness based on escaped defect risk and QA depth.',
      tone: 'info',
    },
    {
      id: 'escaped-defects',
      title: 'Escaped Defects %',
      value: '1.8%',
      delta: '-0.6 pts',
      trend: 'up',
      description: 'Production escapes over total defects found this release cycle.',
      tone: 'success',
    },
    {
      id: 'automation-confidence',
      title: 'Automation Confidence',
      value: '84%',
      delta: '+6 suites',
      trend: 'up',
      description: 'Critical path automation signal across high-risk services.',
      tone: 'warning',
    },
  ],
  highlights: [
    'Checkout defect leakage dropped for the third consecutive sprint after test fixture hardening.',
    'Payments squad achieved 96% review coverage and caught four critical bugs pre-release.',
    'Identity remains the highest-risk surface due to flaky auth regression automation in staging.',
  ],
};

const modulesFallback: ModuleQuality[] = [
  {
    id: 'payments',
    name: 'Payments',
    team: 'Monetization',
    qualityIndex: 94,
    coverage: 91,
    defectDensity: 0.8,
    velocity: 32,
    openBugs: 3,
    escapedDefects: 0,
    riskLevel: 'good',
    summary: 'Stable release train with strong pre-release interception and excellent automation depth.',
    topIssue: 'Fraud retry telemetry still needs contract monitoring.',
  },
  {
    id: 'identity',
    name: 'Identity',
    team: 'Core Platform',
    qualityIndex: 71,
    coverage: 68,
    defectDensity: 2.7,
    velocity: 18,
    openBugs: 9,
    escapedDefects: 2,
    riskLevel: 'bad',
    summary: 'Authentication flows have elevated regression risk due to flaky device-auth scenarios.',
    topIssue: 'Session renewal edge cases are under-tested in mobile web.',
  },
  {
    id: 'analytics',
    name: 'Analytics',
    team: 'Data Products',
    qualityIndex: 86,
    coverage: 79,
    defectDensity: 1.4,
    velocity: 25,
    openBugs: 5,
    escapedDefects: 1,
    riskLevel: 'warning',
    summary: 'Schema drift alerts improved resilience, but ingestion retries still skew downstream reports.',
    topIssue: 'Late-arriving event replay validation is manual.',
  },
  {
    id: 'notifications',
    name: 'Notifications',
    team: 'Growth',
    qualityIndex: 89,
    coverage: 82,
    defectDensity: 1.1,
    velocity: 27,
    openBugs: 4,
    escapedDefects: 0,
    riskLevel: 'good',
    summary: 'Delivery health is strong after template validation standardization.',
    topIssue: 'Push token revocation lacks dedicated chaos coverage.',
  },
  {
    id: 'search',
    name: 'Search',
    team: 'Discovery',
    qualityIndex: 78,
    coverage: 74,
    defectDensity: 1.9,
    velocity: 21,
    openBugs: 6,
    escapedDefects: 1,
    riskLevel: 'warning',
    summary: 'Ranking regressions are improving, but indexing freshness still causes noisy incident spikes.',
    topIssue: 'Index lag alert thresholds need recalibration.',
  },
  {
    id: 'mobile-api',
    name: 'Mobile API',
    team: 'App Platform',
    qualityIndex: 83,
    coverage: 76,
    defectDensity: 1.6,
    velocity: 23,
    openBugs: 5,
    escapedDefects: 1,
    riskLevel: 'warning',
    summary: 'API stability improved after contract checks were moved into CI gates.',
    topIssue: 'Versioned response fixture coverage is incomplete.',
  },
];

const bugBreakdownFallback: BugBreakdownDatum[] = [
  { name: 'Regression', value: 38 },
  { name: 'Config', value: 17 },
  { name: 'Data Integrity', value: 22 },
  { name: 'Performance', value: 13 },
  { name: 'UX Edge Case', value: 10 },
];

const rootCauseFallback: RootCauseDatum[] = [
  { name: 'Missing test coverage', value: 16 },
  { name: 'Requirement ambiguity', value: 12 },
  { name: 'Schema drift', value: 9 },
  { name: 'Observability gap', value: 7 },
  { name: 'Release process issue', value: 5 },
];

const trendFallback: TrendDatum[] = [
  { sprint: 'S-19', qualityIndex: 74, escapedDefects: 4.2, automationConfidence: 62 },
  { sprint: 'S-20', qualityIndex: 78, escapedDefects: 3.5, automationConfidence: 67 },
  { sprint: 'S-21', qualityIndex: 81, escapedDefects: 3.1, automationConfidence: 71 },
  { sprint: 'S-22', qualityIndex: 86, escapedDefects: 2.4, automationConfidence: 79 },
  { sprint: 'S-23', qualityIndex: 90, escapedDefects: 2.0, automationConfidence: 82 },
  { sprint: 'S-24', qualityIndex: 92, escapedDefects: 1.8, automationConfidence: 84 },
];

const chainFallback: ChainStage[] = [
  {
    stage: 'Defect Origin',
    connections: [
      { target: 'Requirements', value: 14, evidence: '14 defects stemmed from acceptance criteria gaps.' },
      { target: 'Implementation', value: 22, evidence: 'Implementation regressions clustered around auth and payments.' },
      { target: 'Data Contracts', value: 9, evidence: 'Schema drift surfaced across event pipelines.' },
    ],
  },
  {
    stage: 'Detection Channel',
    connections: [
      { target: 'Code Review', value: 19, evidence: 'Review checklists flagged high-risk API changes early.' },
      { target: 'CI Automation', value: 15, evidence: 'Expanded smoke packs caught checkout and permissions regressions.' },
      { target: 'Exploratory QA', value: 11, evidence: 'Exploratory passes surfaced mobile auth and notification edge cases.' },
    ],
  },
  {
    stage: 'Outcome',
    connections: [
      { target: 'Blocked Pre-release', value: 28, evidence: '28 issues were stopped before deployment.' },
      { target: 'Mitigated in Canary', value: 9, evidence: 'Canary observation contained incidents within 30 minutes.' },
      { target: 'Escaped', value: 4, evidence: 'Escapes came primarily from Identity and Analytics.' },
    ],
  },
];

const leaderboardFallback: LeaderboardEntry[] = [
  {
    id: 'maya',
    name: 'Maya Chen',
    role: 'Senior QA Engineer',
    squad: 'Payments',
    score: 98,
    evidence: 'Rank #1 — 4 critical bugs caught pre-release, 0 escaped defects, 96% review coverage.',
    criticalBugsCaught: 4,
    escapedDefects: 0,
    avatarColor: 'from-cyan-400 to-teal-500',
  },
  {
    id: 'owen',
    name: 'Owen Patel',
    role: 'Staff Engineer',
    squad: 'Notifications',
    score: 93,
    evidence: 'Rank #2 — Reduced flaky tests by 38% and closed every sev-1 alert before launch.',
    criticalBugsCaught: 3,
    escapedDefects: 0,
    avatarColor: 'from-violet-400 to-fuchsia-500',
  },
  {
    id: 'lina',
    name: 'Lina Gomez',
    role: 'Engineering Manager',
    squad: 'Analytics',
    score: 90,
    evidence: 'Rank #3 — Standardized release readiness reviews, cutting incident reopen rate by 24%.',
    criticalBugsCaught: 2,
    escapedDefects: 1,
    avatarColor: 'from-emerald-400 to-cyan-500',
  },
  {
    id: 'ethan',
    name: 'Ethan Brooks',
    role: 'Tech Lead',
    squad: 'Identity',
    score: 84,
    evidence: 'Rank #4 — Cleared 7 auth bugs but still carries 2 escaped defects from stale fixtures.',
    criticalBugsCaught: 2,
    escapedDefects: 2,
    avatarColor: 'from-amber-400 to-orange-500',
  },
];

const storiesFallback: StoryItem[] = [
  {
    id: 'EQIP-184',
    title: 'Stabilize checkout retry orchestration',
    owner: 'Maya Chen',
    module: 'Payments',
    status: 'On track',
    risk: 'Low',
    qaSignal: 'Smoke and canary coverage both green.',
    dueDate: '2026-07-30',
  },
  {
    id: 'EQIP-196',
    title: 'Harden device-auth regression pack',
    owner: 'Ethan Brooks',
    module: 'Identity',
    status: 'At risk',
    risk: 'High',
    qaSignal: 'Two flaky mobile-web scenarios remain unresolved.',
    dueDate: '2026-07-28',
  },
  {
    id: 'EQIP-203',
    title: 'Add replay validation for delayed events',
    owner: 'Lina Gomez',
    module: 'Analytics',
    status: 'At risk',
    risk: 'Medium',
    qaSignal: 'Manual data verification still needed before release.',
    dueDate: '2026-08-01',
  },
  {
    id: 'EQIP-207',
    title: 'Introduce push token revocation chaos tests',
    owner: 'Owen Patel',
    module: 'Notifications',
    status: 'On track',
    risk: 'Low',
    qaSignal: 'Chaos suite added to nightly validation.',
    dueDate: '2026-08-03',
  },
  {
    id: 'EQIP-214',
    title: 'Tune stale index freshness alerts',
    owner: 'Nina Ross',
    module: 'Search',
    status: 'Blocked',
    risk: 'High',
    qaSignal: 'Awaiting production baselines for false-positive filtering.',
    dueDate: '2026-08-04',
  },
];

const bugsFallback: BugItem[] = [
  {
    id: 'BUG-902',
    title: 'Session renewal fails after MFA retry',
    severity: 'Critical',
    module: 'Identity',
    status: 'Open',
    origin: 'Mobile web regression',
    owner: 'Ethan Brooks',
    createdAt: '2026-07-22',
  },
  {
    id: 'BUG-887',
    title: 'Replay events double-count revenue in long-running batches',
    severity: 'High',
    module: 'Analytics',
    status: 'Triaged',
    origin: 'Schema drift',
    owner: 'Lina Gomez',
    createdAt: '2026-07-20',
  },
  {
    id: 'BUG-876',
    title: 'Search results lag after catalog import',
    severity: 'Medium',
    module: 'Search',
    status: 'Mitigated',
    origin: 'Indexing threshold',
    owner: 'Nina Ross',
    createdAt: '2026-07-19',
  },
  {
    id: 'BUG-861',
    title: 'Push revocation webhook retries on expired tokens',
    severity: 'Low',
    module: 'Notifications',
    status: 'Resolved',
    origin: 'Webhook edge case',
    owner: 'Owen Patel',
    createdAt: '2026-07-16',
  },
  {
    id: 'BUG-854',
    title: 'Checkout fraud review timeout lacks analytics breadcrumb',
    severity: 'High',
    module: 'Payments',
    status: 'Triaged',
    origin: 'Observability gap',
    owner: 'Maya Chen',
    createdAt: '2026-07-15',
  },
];

const recommendationsByModule: Record<string, string[]> = {
  payments: [
    'Expand fraud review telemetry assertions into the release smoke pack.',
    'Protect partner gateway contract changes with synthetic canary monitoring.',
  ],
  identity: [
    'Quarantine flaky device-auth cases and rebuild them against stable seed data.',
    'Add MFA session-renewal contract tests to pre-merge gates.',
  ],
  analytics: [
    'Automate replay validation for late-arriving event streams.',
    'Promote schema drift alerts to release-blocking status when downstream KPIs move >2%.',
  ],
  notifications: [
    'Keep chaos token revocation checks in nightly plus pre-release canary.',
    'Introduce template diff approval for multi-locale releases.',
  ],
  search: [
    'Rebaseline freshness alerts using weekday traffic cohorts.',
    'Add index lag traces to incident runbooks for faster triage.',
  ],
  'mobile-api': [
    'Add versioned fixture validation to every app release candidate.',
    'Surface contract drift warnings directly in mobile release checklists.',
  ],
};

function moduleKeyToName(moduleId: string) {
  return modulesFallback.find((module) => module.id === moduleId)?.name ?? moduleId;
}

export function useDashboardSummaryQuery() {
  return useQuery<ApiResult<DashboardSummary>>({
    queryKey: ['dashboard-summary'],
    queryFn: () => requestWithFallback('/dashboard/summary', dashboardSummaryFallback),
  });
}

export function useModulesQuery() {
  return useQuery<ApiResult<ModuleQuality[]>>({
    queryKey: ['modules'],
    queryFn: () => requestWithFallback('/modules', modulesFallback),
  });
}

export function useBugBreakdownQuery() {
  return useQuery<ApiResult<BugBreakdownDatum[]>>({
    queryKey: ['bug-breakdown'],
    queryFn: () => requestWithFallback('/dashboard/bugs/breakdown', bugBreakdownFallback),
  });
}

export function useRootCauseBreakdownQuery() {
  return useQuery<ApiResult<RootCauseDatum[]>>({
    queryKey: ['root-cause-breakdown'],
    queryFn: () => requestWithFallback('/dashboard/root-causes', rootCauseFallback),
  });
}

export function useTrendQuery() {
  return useQuery<ApiResult<TrendDatum[]>>({
    queryKey: ['trend'],
    queryFn: () => requestWithFallback('/dashboard/trends', trendFallback),
  });
}

export function useChainQuery() {
  return useQuery<ApiResult<ChainStage[]>>({
    queryKey: ['chain'],
    queryFn: () => requestWithFallback('/dashboard/chain', chainFallback),
  });
}

export function useLeaderboardQuery() {
  return useQuery<ApiResult<LeaderboardEntry[]>>({
    queryKey: ['leaderboard'],
    queryFn: () => requestWithFallback('/leaderboard', leaderboardFallback),
  });
}

export function useStoriesQuery() {
  return useQuery<ApiResult<StoryItem[]>>({
    queryKey: ['stories'],
    queryFn: () => requestWithFallback('/stories', storiesFallback),
  });
}

export function useBugsQuery() {
  return useQuery<ApiResult<BugItem[]>>({
    queryKey: ['bugs'],
    queryFn: () => requestWithFallback('/bugs', bugsFallback),
  });
}

export function useModuleQuery(moduleId?: string) {
  return useQuery<ApiResult<ModuleDetailModel>>({
    queryKey: ['module', moduleId],
    enabled: Boolean(moduleId),
    queryFn: async () => {
      const fallback = buildModuleDetail(moduleId ?? 'payments');
      return requestWithFallback(`/modules/${moduleId}`, fallback);
    },
  });
}

function buildModuleDetail(moduleId: string): ModuleDetailModel {
  const module = modulesFallback.find((item) => item.id === moduleId) ?? modulesFallback[0];
  const moduleName = moduleKeyToName(module.id);

  return {
    module,
    stories: storiesFallback.filter((story) => story.module === moduleName),
    bugs: bugsFallback.filter((bug) => bug.module === moduleName),
    recommendations: recommendationsByModule[module.id] ?? [
      'No module-specific recommendation available.',
    ],
  };
}
