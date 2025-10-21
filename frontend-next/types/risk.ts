/**
 * 风险识别相关的TypeScript类型定义
 */

// 风险等级枚举
export enum RiskLevel {
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low",
}

// 风险类型枚举
export enum RiskType {
  DISQUALIFICATION = "disqualification",
  UNLIMITED_LIABILITY = "unlimited_liability",
  HARSH_TERMS = "harsh_terms",
  TIGHT_DEADLINE = "tight_deadline",
  HIGH_PENALTY = "high_penalty",
  UNCLEAR_REQUIREMENTS = "unclear_requirements",
  OTHER = "other",
}

// 风险项接口
export interface Risk {
  id: string;
  document_id: string;
  scenario_id: string;
  title: string;
  description: string;
  risk_type: RiskType;
  risk_level: RiskLevel;
  page_number?: number;
  section?: string;
  clause_number?: string;
  original_text?: string;
  impact_description?: string;
  mitigation_suggestion?: string;
  confidence_score?: number;
  created_at: string;
  updated_at: string;
}

// 风险报告接口
export interface RiskReport {
  id: string;
  document_id: string;
  scenario_id: string;
  title: string;
  summary?: string;
  total_risks: number;
  high_risks: number;
  medium_risks: number;
  low_risks: number;
  overall_risk_level?: RiskLevel;
  created_at: string;
  updated_at: string;
  risks: Risk[];
}

// API请求/响应类型
export interface DetectRiskRequest {
  document_id: string;
  scenario_id?: string;
}

export interface DetectRiskResponse {
  success: boolean;
  message: string;
  report_id?: string;
}

// 前端特定类型
export interface RiskStats {
  total: number;
  high: number;
  medium: number;
  low: number;
  byType: Record<RiskType, number>;
}

export interface RiskFilter {
  levels?: RiskLevel[];
  types?: RiskType[];
  search?: string;
  pageNumber?: number;
}

// 风险高亮位置信息（用于PDF标注）
export interface RiskHighlightPosition {
  pageNumber: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

// 带位置信息的风险（用于PDF高亮）
export interface RiskWithPosition extends Risk {
  position?: RiskHighlightPosition;
}

// 风险等级颜色映射
export const RISK_LEVEL_COLORS: Record<RiskLevel, { bg: string; border: string; text: string }> = {
  [RiskLevel.HIGH]: {
    bg: "rgba(239, 68, 68, 0.2)",
    border: "rgb(239, 68, 68)",
    text: "text-red-600",
  },
  [RiskLevel.MEDIUM]: {
    bg: "rgba(251, 191, 36, 0.2)",
    border: "rgb(251, 191, 36)",
    text: "text-yellow-600",
  },
  [RiskLevel.LOW]: {
    bg: "rgba(34, 197, 94, 0.2)",
    border: "rgb(34, 197, 94)",
    text: "text-green-600",
  },
};

// 风险类型中文名称映射
export const RISK_TYPE_LABELS: Record<RiskType, string> = {
  [RiskType.DISQUALIFICATION]: "废标风险",
  [RiskType.UNLIMITED_LIABILITY]: "无限责任",
  [RiskType.HARSH_TERMS]: "苛刻条款",
  [RiskType.TIGHT_DEADLINE]: "时间紧迫",
  [RiskType.HIGH_PENALTY]: "高额罚款",
  [RiskType.UNCLEAR_REQUIREMENTS]: "要求不明确",
  [RiskType.OTHER]: "其他风险",
};

// 风险等级中文名称映射
export const RISK_LEVEL_LABELS: Record<RiskLevel, string> = {
  [RiskLevel.HIGH]: "高风险",
  [RiskLevel.MEDIUM]: "中风险",
  [RiskLevel.LOW]: "低风险",
};

