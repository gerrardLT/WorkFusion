// 项目推荐类型定义

export interface Qualification {
  name: string;
  level: string;
}

export interface ProjectMetadata {
  tags?: string[];
  keywords?: string[];
  scale?: string;
  duration?: number;
  payment_terms?: string;
  [key: string]: any;
}

export interface Project {
  id: string;
  title: string;
  description?: string;
  source_platform?: string;
  source_url?: string;
  project_code?: string;

  // 发布信息
  publisher?: string;
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;

  // 项目详情
  budget?: number;
  area?: string;
  industry?: string;
  project_type?: string;

  // 资质要求
  required_qualifications?: Qualification[];

  // 时间节点
  publish_date?: string;
  deadline?: string;
  bid_opening_date?: string;

  // 项目元数据
  metadata?: ProjectMetadata;

  // 状态
  status?: 'new' | 'active' | 'expired' | 'closed';
  is_recommended?: boolean;

  // 时间戳
  created_at?: string;
  updated_at?: string;
}

export interface ProjectRecommendation {
  project: Project;
  match_score: number;
  match_reason: string;
  match_details: {
    qualification_match: boolean;
    area_match: boolean;
    budget_match: boolean;
    capability_match: boolean;
    [key: string]: any;
  };
}

export interface RecommendationListResponse {
  recommendations: ProjectRecommendation[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface ProjectFilters {
  min_score?: number;
  min_budget?: number;
  max_budget?: number;
  areas?: string[];
  industries?: string[];
  status?: string;
  deadline_from?: string;
  deadline_to?: string;
}

export interface ProjectSortOptions {
  sort_by?: 'match_score' | 'budget' | 'deadline' | 'publish_date';
  order?: 'asc' | 'desc';
}

