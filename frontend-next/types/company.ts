// 企业类型定义

export interface Qualification {
  name: string;
  level: string;
  number?: string;
  expire_date?: string;
}

export interface Capabilities {
  fields: string[];
  advantages: string[];
  certifications: string[];
  patents?: number;
  projects_completed?: number;
}

export interface Achievement {
  name: string;
  amount: number;
  year: number;
  client: string;
}

export interface Achievements {
  total_projects: number;
  total_amount: number;
  average_amount: number;
  success_rate: number;
  major_projects: Achievement[];
  clients: string[];
}

export interface BudgetRange {
  min: number;
  max: number;
}

export interface Company {
  id?: string;
  name: string;
  description?: string;
  scale: 'small' | 'medium' | 'large';
  founded_year?: number;
  employee_count?: number;
  registered_capital?: number;

  // 联系信息
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;
  address?: string;
  website?: string;

  // 资质与能力
  qualifications: Qualification[];
  capabilities: Capabilities;
  achievements: Achievements;

  // 目标市场
  target_areas: string[];
  target_industries: string[];
  budget_range: BudgetRange;

  // 偏好
  preferences?: Record<string, any>;

  // 元数据
  metadata?: Record<string, any>;
  is_active?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface CreateCompanyRequest {
  name: string;
  description?: string;
  scale?: string;
  employee_count?: number;
  registered_capital?: number;
  contact_person?: string;
  contact_phone?: string;
  contact_email?: string;
  address?: string;
  website?: string;
  qualifications?: Qualification[];
  capabilities?: Capabilities;
  achievements?: Achievements;
  target_areas?: string[];
  target_industries?: string[];
  budget_range?: BudgetRange;
  preferences?: Record<string, any>;
  scenario_id?: string;
}

export interface UpdateCompanyRequest extends Partial<CreateCompanyRequest> {
  is_active?: boolean;
}

