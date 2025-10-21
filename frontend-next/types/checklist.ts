/**
 * 任务清单相关类型定义
 */

// 任务优先级
export type TaskPriority = 'high' | 'medium' | 'low';

// 任务状态
export type TaskStatus = 'pending' | 'in_progress' | 'completed' | 'cancelled';

// 任务分类
export type TaskCategory =
  | '资质文件准备'
  | '技术方案编写'
  | '商务文件准备'
  | '时间节点管理'
  | '合规性检查'
  | '其他';

// 任务项
export interface Task {
  id: string;
  title: string;
  description?: string;
  category: TaskCategory;
  priority: TaskPriority;
  status: TaskStatus;
  deadline?: string; // ISO格式日期
  estimated_hours?: number;
  actual_hours?: number;
  assignee?: string;
  source_page?: number;
  source_content?: string;
  confidence_score?: number;
  notes?: string;
  order_index: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

// 任务清单
export interface Checklist {
  id: string;
  document_id: string;
  scenario_id: string;
  title: string;
  description?: string;
  total_tasks: number;
  completed_tasks: number;
  generation_method: 'auto' | 'manual' | 'hybrid';
  created_at: string;
  updated_at: string;
  tasks: Task[];
}

// 生成清单请求
export interface GenerateChecklistRequest {
  document_id: string;
  scenario_id?: string;
  generation_config?: {
    categories?: TaskCategory[];
    [key: string]: any;
  };
}

// 生成清单响应
export interface GenerateChecklistResponse {
  success: boolean;
  checklist_id?: string;
  message: string;
}

// 清单详情响应
export interface ChecklistResponse {
  success: boolean;
  data?: Checklist;
  message: string;
}

// 更新任务请求
export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  priority?: TaskPriority;
  status?: TaskStatus;
  deadline?: string;
  assignee?: string;
  notes?: string;
  estimated_hours?: number;
  actual_hours?: number;
}

// 更新任务响应
export interface UpdateTaskResponse {
  success: boolean;
  message: string;
}

// 删除清单响应
export interface DeleteChecklistResponse {
  success: boolean;
  message: string;
}

// 任务统计
export interface TaskStats {
  total: number;
  completed: number;
  in_progress: number;
  pending: number;
  cancelled: number;
  by_priority: {
    high: number;
    medium: number;
    low: number;
  };
  by_category: Record<TaskCategory, number>;
  completion_rate: number; // 0-100
}

// 任务过滤器
export interface TaskFilter {
  status?: TaskStatus[];
  priority?: TaskPriority[];
  category?: TaskCategory[];
  assignee?: string;
  search?: string;
}

// 任务排序
export type TaskSortBy = 'priority' | 'deadline' | 'created_at' | 'order_index';
export type TaskSortOrder = 'asc' | 'desc';

export interface TaskSort {
  by: TaskSortBy;
  order: TaskSortOrder;
}

