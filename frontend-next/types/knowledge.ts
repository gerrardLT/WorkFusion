/**
 * 知识库管理相关的TypeScript类型定义
 */

// 知识库分类枚举
export enum KnowledgeCategory {
  QUALIFICATIONS = "qualifications",  // 资质证照
  PERFORMANCE = "performance",        // 历史业绩
  SOLUTIONS = "solutions",            // 技术方案
  PERSONNEL = "personnel",            // 人员档案
}

// 知识库状态枚举
export enum KnowledgeStatus {
  ACTIVE = "active",                  // 有效
  EXPIRED = "expired",                // 已过期
  EXPIRING_SOON = "expiring_soon",    // 即将过期
  ARCHIVED = "archived",              // 已归档
}

// 知识库项目接口
export interface KnowledgeItem {
  id: string;
  scenario_id: string;
  document_id?: string;
  category: KnowledgeCategory;
  title: string;
  description?: string;
  tags: string[];
  status: KnowledgeStatus;
  issue_date?: string;  // YYYY-MM-DD
  expire_date?: string; // YYYY-MM-DD
  metadata: Record<string, any>;
  file_path?: string;
  file_size?: number;
  file_type?: string;
  view_count: number;
  reference_count: number;
  created_at: string;
  updated_at: string;
  created_by?: string;
  updated_by?: string;
}

// API请求/响应类型
export interface CreateKnowledgeRequest {
  scenario_id: string;
  category: KnowledgeCategory;
  title: string;
  description?: string;
  tags?: string[];
  document_id?: string;
  issue_date?: string;
  expire_date?: string;
  metadata?: Record<string, any>;
  file_path?: string;
  file_size?: number;
  file_type?: string;
  created_by?: string;
}

export interface UpdateKnowledgeRequest {
  title?: string;
  description?: string;
  tags?: string[];
  issue_date?: string;
  expire_date?: string;
  metadata?: Record<string, any>;
  status?: KnowledgeStatus;
  updated_by?: string;
}

export interface KnowledgeListResponse {
  total: number;
  items: KnowledgeItem[];
}

export interface KnowledgeStatsResponse {
  total: number;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  expiring_soon: number;
}

// 前端特定类型
export interface KnowledgeFilter {
  category?: KnowledgeCategory;
  status?: KnowledgeStatus;
  tags?: string[];
  search?: string;
  dateRange?: {
    start?: string;
    end?: string;
  };
}

export interface KnowledgeViewMode {
  mode: 'card' | 'list';
}

// 知识库分类中文名称映射
export const KNOWLEDGE_CATEGORY_LABELS: Record<KnowledgeCategory, string> = {
  [KnowledgeCategory.QUALIFICATIONS]: "资质证照",
  [KnowledgeCategory.PERFORMANCE]: "历史业绩",
  [KnowledgeCategory.SOLUTIONS]: "技术方案",
  [KnowledgeCategory.PERSONNEL]: "人员档案",
};

// 知识库状态中文名称映射
export const KNOWLEDGE_STATUS_LABELS: Record<KnowledgeStatus, string> = {
  [KnowledgeStatus.ACTIVE]: "有效",
  [KnowledgeStatus.EXPIRED]: "已过期",
  [KnowledgeStatus.EXPIRING_SOON]: "即将过期",
  [KnowledgeStatus.ARCHIVED]: "已归档",
};

// 知识库状态颜色映射
export const KNOWLEDGE_STATUS_COLORS: Record<KnowledgeStatus, { bg: string; text: string; border: string }> = {
  [KnowledgeStatus.ACTIVE]: {
    bg: "bg-green-100",
    text: "text-green-700",
    border: "border-green-300",
  },
  [KnowledgeStatus.EXPIRED]: {
    bg: "bg-red-100",
    text: "text-red-700",
    border: "border-red-300",
  },
  [KnowledgeStatus.EXPIRING_SOON]: {
    bg: "bg-yellow-100",
    text: "text-yellow-700",
    border: "border-yellow-300",
  },
  [KnowledgeStatus.ARCHIVED]: {
    bg: "bg-gray-100",
    text: "text-gray-700",
    border: "border-gray-300",
  },
};

// 知识库分类图标映射
export const KNOWLEDGE_CATEGORY_ICONS: Record<KnowledgeCategory, string> = {
  [KnowledgeCategory.QUALIFICATIONS]: "📜",
  [KnowledgeCategory.PERFORMANCE]: "🏆",
  [KnowledgeCategory.SOLUTIONS]: "💡",
  [KnowledgeCategory.PERSONNEL]: "👤",
};

