"use client";

import React, { useState } from 'react';
import { Task, TaskCategory } from '@/types/checklist';
import { TaskItem } from './task-item';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ChevronDown, ChevronRight } from 'lucide-react';

interface TaskGroupProps {
  category: TaskCategory;
  tasks: Task[];
  onTaskUpdate: (taskId: string, updates: Partial<Task>) => void;
  onTaskDelete?: (taskId: string) => void;
  defaultExpanded?: boolean;
}

export function TaskGroup({
  category,
  tasks,
  onTaskUpdate,
  onTaskDelete,
  defaultExpanded = true
}: TaskGroupProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  // 计算统计信息
  const stats = {
    total: tasks.length,
    completed: tasks.filter(t => t.status === 'completed').length,
    inProgress: tasks.filter(t => t.status === 'in_progress').length,
    pending: tasks.filter(t => t.status === 'pending').length,
  };

  const completionRate = stats.total > 0
    ? Math.round((stats.completed / stats.total) * 100)
    : 0;

  // 分类图标映射
  const getCategoryIcon = (category: TaskCategory): string => {
    switch (category) {
      case '资质文件准备':
        return '📄';
      case '技术方案编写':
        return '⚙️';
      case '商务文件准备':
        return '💼';
      case '时间节点管理':
        return '⏰';
      case '合规性检查':
        return '✅';
      default:
        return '📋';
    }
  };

  // 进度条颜色
  const getProgressColor = (): string => {
    if (completionRate === 100) return 'bg-green-500';
    if (completionRate >= 50) return 'bg-blue-500';
    if (completionRate > 0) return 'bg-yellow-500';
    return 'bg-gray-300';
  };

  if (tasks.length === 0) {
    return null;
  }

  return (
    <div className="mb-6">
      {/* 分组头部 */}
      <Card className="p-4 mb-3 bg-gray-50 border-2">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between hover:opacity-80 transition-opacity"
        >
          <div className="flex items-center gap-3">
            {/* 展开/收起图标 */}
            {isExpanded ? (
              <ChevronDown className="h-5 w-5 text-gray-600" />
            ) : (
              <ChevronRight className="h-5 w-5 text-gray-600" />
            )}

            {/* 分类图标和名称 */}
            <div className="flex items-center gap-2">
              <span className="text-2xl">{getCategoryIcon(category)}</span>
              <h3 className="text-lg font-semibold text-gray-900">{category}</h3>
            </div>

            {/* 统计徽章 */}
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="bg-white">
                {stats.completed}/{stats.total}
              </Badge>

              {stats.inProgress > 0 && (
                <Badge className="bg-blue-100 text-blue-700">
                  进行中 {stats.inProgress}
                </Badge>
              )}

              {stats.pending > 0 && (
                <Badge className="bg-gray-100 text-gray-700">
                  待处理 {stats.pending}
                </Badge>
              )}
            </div>
          </div>

          {/* 完成率 */}
          <div className="flex items-center gap-3">
            <span className="text-sm font-medium text-gray-600">
              {completionRate}%
            </span>

            {/* 进度条 */}
            <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full ${getProgressColor()} transition-all duration-300`}
                style={{ width: `${completionRate}%` }}
              />
            </div>
          </div>
        </button>
      </Card>

      {/* 任务列表 */}
      {isExpanded && (
        <div className="ml-4 space-y-0">
          {tasks.map((task) => (
            <TaskItem
              key={task.id}
              task={task}
              onUpdate={onTaskUpdate}
              onDelete={onTaskDelete}
            />
          ))}
        </div>
      )}
    </div>
  );
}

