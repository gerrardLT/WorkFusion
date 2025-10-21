"use client";

import React, { useState, useEffect, useMemo } from 'react';
import {
  Checklist,
  Task,
  TaskCategory,
  TaskFilter,
  TaskSort,
  TaskStats,
  UpdateTaskRequest
} from '@/types/checklist';
import { TaskGroup } from './task-group';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import {
  Search,
  Filter,
  Download,
  RefreshCw,
  CheckCircle2,
  Clock,
  AlertCircle,
  ListTodo
} from 'lucide-react';
import * as api from '@/lib/api-v2';

interface ChecklistPanelProps {
  documentId: string;
  scenarioId?: string;
  onTaskUpdate?: (taskId: string, updates: UpdateTaskRequest) => void;
}

export function ChecklistPanel({
  documentId,
  scenarioId = 'tender',
  onTaskUpdate
}: ChecklistPanelProps) {
  const [checklist, setChecklist] = useState<Checklist | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<TaskFilter>({});
  const [generating, setGenerating] = useState(false);

  // 加载清单
  const loadChecklist = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await api.getChecklistByDocument(documentId);

      if (response.success && response.data) {
        setChecklist(response.data);
      } else {
        setError('未找到任务清单');
      }
    } catch (err: any) {
      console.error('加载清单失败:', err);
      setError(err.message || '加载清单失败');
    } finally {
      setLoading(false);
    }
  };

  // 生成清单
  const generateChecklist = async () => {
    try {
      setGenerating(true);
      setError(null);

      const response = await api.generateChecklistForDocument(documentId, scenarioId);

      if (response.success && response.checklist_id) {
        // 生成成功，重新加载
        await loadChecklist();
      } else {
        setError(response.message || '生成清单失败');
      }
    } catch (err: any) {
      console.error('生成清单失败:', err);
      setError(err.message || '生成清单失败');
    } finally {
      setGenerating(false);
    }
  };

  // 更新任务
  const handleTaskUpdate = async (taskId: string, updates: Partial<Task>) => {
    try {
      const updateRequest: UpdateTaskRequest = {
        title: updates.title,
        description: updates.description,
        priority: updates.priority,
        status: updates.status,
        deadline: updates.deadline,
        assignee: updates.assignee,
        notes: updates.notes,
        estimated_hours: updates.estimated_hours,
        actual_hours: updates.actual_hours,
      };

      const response = await api.updateTask(taskId, updateRequest);

      if (response.success) {
        // 更新本地状态
        if (checklist) {
          const updatedTasks = checklist.tasks.map(task =>
            task.id === taskId ? { ...task, ...updates } : task
          );
          setChecklist({
            ...checklist,
            tasks: updatedTasks,
            completed_tasks: updatedTasks.filter(t => t.status === 'completed').length
          });
        }

        // 调用外部回调
        if (onTaskUpdate) {
          onTaskUpdate(taskId, updateRequest);
        }
      } else {
        console.error('更新任务失败:', response.message);
      }
    } catch (err: any) {
      console.error('更新任务失败:', err);
    }
  };

  // 初始加载
  useEffect(() => {
    loadChecklist();
  }, [documentId]);

  // 过滤和搜索任务
  const filteredTasks = useMemo(() => {
    if (!checklist) return [];

    let tasks = [...checklist.tasks];

    // 搜索过滤
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      tasks = tasks.filter(task =>
        task.title.toLowerCase().includes(query) ||
        task.description?.toLowerCase().includes(query) ||
        task.category.toLowerCase().includes(query)
      );
    }

    // 状态过滤
    if (filter.status && filter.status.length > 0) {
      tasks = tasks.filter(task => filter.status!.includes(task.status));
    }

    // 优先级过滤
    if (filter.priority && filter.priority.length > 0) {
      tasks = tasks.filter(task => filter.priority!.includes(task.priority));
    }

    // 分类过滤
    if (filter.category && filter.category.length > 0) {
      tasks = tasks.filter(task => filter.category!.includes(task.category));
    }

    return tasks;
  }, [checklist, searchQuery, filter]);

  // 按分类分组
  const tasksByCategory = useMemo(() => {
    const groups: Record<TaskCategory, Task[]> = {
      '资质文件准备': [],
      '技术方案编写': [],
      '商务文件准备': [],
      '时间节点管理': [],
      '合规性检查': [],
      '其他': []
    };

    filteredTasks.forEach(task => {
      if (groups[task.category]) {
        groups[task.category].push(task);
      } else {
        groups['其他'].push(task);
      }
    });

    // 按order_index排序
    Object.keys(groups).forEach(category => {
      groups[category as TaskCategory].sort((a, b) => a.order_index - b.order_index);
    });

    return groups;
  }, [filteredTasks]);

  // 计算统计信息
  const stats: TaskStats | null = useMemo(() => {
    if (!checklist) return null;

    const tasks = checklist.tasks;
    const completed = tasks.filter(t => t.status === 'completed').length;
    const inProgress = tasks.filter(t => t.status === 'in_progress').length;
    const pending = tasks.filter(t => t.status === 'pending').length;
    const cancelled = tasks.filter(t => t.status === 'cancelled').length;

    const byPriority = {
      high: tasks.filter(t => t.priority === 'high').length,
      medium: tasks.filter(t => t.priority === 'medium').length,
      low: tasks.filter(t => t.priority === 'low').length,
    };

    const byCategory: Record<TaskCategory, number> = {
      '资质文件准备': 0,
      '技术方案编写': 0,
      '商务文件准备': 0,
      '时间节点管理': 0,
      '合规性检查': 0,
      '其他': 0
    };

    tasks.forEach(task => {
      if (byCategory[task.category] !== undefined) {
        byCategory[task.category]++;
      } else {
        byCategory['其他']++;
      }
    });

    return {
      total: tasks.length,
      completed,
      in_progress: inProgress,
      pending,
      cancelled,
      by_priority: byPriority,
      by_category: byCategory,
      completion_rate: tasks.length > 0 ? Math.round((completed / tasks.length) * 100) : 0
    };
  }, [checklist]);

  // 加载中状态
  if (loading) {
    return (
      <Card className="p-8">
        <div className="flex flex-col items-center justify-center gap-4">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
          <p className="text-gray-600">加载任务清单中...</p>
        </div>
      </Card>
    );
  }

  // 错误状态
  if (error && !checklist) {
    return (
      <Card className="p-8">
        <div className="flex flex-col items-center justify-center gap-4">
          <AlertCircle className="h-12 w-12 text-gray-400" />
          <p className="text-gray-600">{error}</p>
          <Button onClick={generateChecklist} disabled={generating}>
            {generating ? (
              <>
                <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <ListTodo className="mr-2 h-4 w-4" />
                生成任务清单
              </>
            )}
          </Button>
        </div>
      </Card>
    );
  }

  if (!checklist) {
    return null;
  }

  return (
    <div className="space-y-4">
      {/* 头部 */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <ListTodo className="h-6 w-6 text-blue-500" />
              {checklist.title}
            </h2>
            {checklist.description && (
              <p className="text-gray-600 mt-1">{checklist.description}</p>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={loadChecklist}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              刷新
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => {/* TODO: 导出功能 */}}
            >
              <Download className="h-4 w-4 mr-2" />
              导出
            </Button>
          </div>
        </div>

        {/* 统计卡片 */}
        {stats && (
          <div className="grid grid-cols-4 gap-4">
            <div className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg">
              <ListTodo className="h-8 w-8 text-blue-500" />
              <div>
                <p className="text-sm text-gray-600">总任务</p>
                <p className="text-2xl font-bold text-gray-900">{stats.total}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
              <CheckCircle2 className="h-8 w-8 text-green-500" />
              <div>
                <p className="text-sm text-gray-600">已完成</p>
                <p className="text-2xl font-bold text-gray-900">{stats.completed}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
              <Clock className="h-8 w-8 text-yellow-500" />
              <div>
                <p className="text-sm text-gray-600">进行中</p>
                <p className="text-2xl font-bold text-gray-900">{stats.in_progress}</p>
              </div>
            </div>

            <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
              <div className="relative h-8 w-8">
                <svg className="transform -rotate-90" viewBox="0 0 36 36">
                  <circle
                    cx="18"
                    cy="18"
                    r="16"
                    fill="none"
                    stroke="#e5e7eb"
                    strokeWidth="3"
                  />
                  <circle
                    cx="18"
                    cy="18"
                    r="16"
                    fill="none"
                    stroke="#3b82f6"
                    strokeWidth="3"
                    strokeDasharray={`${stats.completion_rate}, 100`}
                  />
                </svg>
              </div>
              <div>
                <p className="text-sm text-gray-600">完成率</p>
                <p className="text-2xl font-bold text-gray-900">{stats.completion_rate}%</p>
              </div>
            </div>
          </div>
        )}
      </Card>

      {/* 搜索和过滤 */}
      <Card className="p-4">
        <div className="flex items-center gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <Input
                type="text"
                placeholder="搜索任务..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          <Button variant="outline" size="sm">
            <Filter className="h-4 w-4 mr-2" />
            筛选
          </Button>
        </div>
      </Card>

      {/* 任务列表（按分类分组） */}
      <div>
        {(Object.keys(tasksByCategory) as TaskCategory[]).map(category => (
          <TaskGroup
            key={category}
            category={category}
            tasks={tasksByCategory[category]}
            onTaskUpdate={handleTaskUpdate}
            defaultExpanded={true}
          />
        ))}
      </div>

      {/* 空状态 */}
      {filteredTasks.length === 0 && (
        <Card className="p-8">
          <div className="flex flex-col items-center justify-center gap-4">
            <ListTodo className="h-12 w-12 text-gray-400" />
            <p className="text-gray-600">
              {searchQuery ? '没有找到匹配的任务' : '暂无任务'}
            </p>
          </div>
        </Card>
      )}
    </div>
  );
}

