// 评估报告类型定义

export interface QualificationMatch {
  requirement: string;
  company_has: boolean;
  company_qualification?: string;
  match_score: number;
  notes?: string;
}

export interface TimelineItem {
  event: string;
  date: string;
  status: 'upcoming' | 'current' | 'passed';
  days_left?: number;
}

export interface HistoricalProject {
  title: string;
  year: number;
  amount: number;
  result: 'won' | 'lost';
  similarity_score: number;
}

export interface RiskItem {
  level: 'high' | 'medium' | 'low';
  category: string;
  description: string;
  mitigation?: string;
}

export interface EvaluationReport {
  id: string;
  project_id: string;
  company_id: string;

  // 1. 项目概况摘要
  project_summary: {
    title: string;
    publisher: string;
    budget?: number;
    area?: string;
    industry?: string;
    deadline?: string;
    description?: string;
  };

  // 2. 核心资质要求对比
  qualification_analysis: {
    total_requirements: number;
    matched_requirements: number;
    match_rate: number;
    details: QualificationMatch[];
  };

  // 3. 关键时间节点表
  timeline: TimelineItem[];

  // 4. 历史类似项目中标情况分析
  historical_analysis: {
    total_similar_projects: number;
    won_projects: number;
    lost_projects: number;
    win_rate: number;
    average_amount: number;
    projects: HistoricalProject[];
  };

  // 5. 风险点提示
  risks: {
    total_risks: number;
    high_risks: number;
    medium_risks: number;
    low_risks: number;
    items: RiskItem[];
  };

  // 6. 综合评估结论和建议
  conclusion: {
    overall_score: number;
    recommendation: 'highly_recommended' | 'recommended' | 'consider' | 'not_recommended';
    strengths: string[];
    weaknesses: string[];
    suggestions: string[];
    final_verdict: string;
  };

  // 元数据
  status: 'draft' | 'final' | 'archived';
  generated_at: string;
  generated_by?: string;
  pdf_url?: string;
  metadata?: Record<string, any>;
}

export interface GenerateReportRequest {
  project_id: string;
  company_id: string;
  include_pdf?: boolean;
}

export interface GenerateReportResponse {
  success: boolean;
  message: string;
  report_id?: string;
  report?: EvaluationReport;
}

export interface ReportListResponse {
  reports: EvaluationReport[];
  total: number;
  page: number;
  page_size: number;
}

