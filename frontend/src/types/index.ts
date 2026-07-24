export type TrendDirection = 'up' | 'down' | 'flat';
export type HealthTone = 'success' | 'warning' | 'danger' | 'info';

export interface QualityMetric {
  id: string;
  title: string;
  value: string;
  delta: string;
  trend: TrendDirection;
  description: string;
  tone: HealthTone;
}

export interface ModuleQuality {
  id: string;
  name: string;
  team: string;
  qualityIndex: number;
  coverage: number;
  defectDensity: number;
  velocity: number;
  openBugs: number;
  escapedDefects: number;
  riskLevel: 'good' | 'warning' | 'bad';
  summary: string;
  topIssue: string;
}

export interface BugBreakdownDatum {
  name: string;
  value: number;
}

export interface RootCauseDatum {
  name: string;
  value: number;
}

export interface TrendDatum {
  sprint: string;
  qualityIndex: number;
  escapedDefects: number;
  automationConfidence: number;
}

export interface ChainStage {
  stage: string;
  connections: Array<{
    target: string;
    value: number;
    evidence: string;
  }>;
}

export interface LeaderboardEntry {
  id: string;
  name: string;
  role: string;
  squad: string;
  score: number;
  evidence: string;
  criticalBugsCaught: number;
  escapedDefects: number;
  avatarColor: string;
}

export interface StoryItem {
  id: string;
  title: string;
  owner: string;
  module: string;
  status: 'On track' | 'At risk' | 'Blocked';
  risk: 'Low' | 'Medium' | 'High';
  qaSignal: string;
  dueDate: string;
}

export interface BugItem {
  id: string;
  title: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  module: string;
  status: 'Open' | 'Triaged' | 'Mitigated' | 'Resolved';
  origin: string;
  owner: string;
  createdAt: string;
}

export interface DashboardSummary {
  metrics: QualityMetric[];
  highlights: string[];
}

export interface ModuleDetailModel {
  module: ModuleQuality;
  stories: StoryItem[];
  bugs: BugItem[];
  recommendations: string[];
}
