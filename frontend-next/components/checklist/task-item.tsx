"use client";

import React, { useState } from 'react';
import { Task, TaskPriority, TaskStatus } from '@/types/checklist';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  CheckCircle2,
  Circle,
  Clock,
  User,
  FileText,
  ChevronDown,
  ChevronUp,
  Edit2,
  Trash2
} from 'lucide-react';

interface TaskItemProps {
  task: Task;
  onUpdate: (taskId: string, updates: Partial<Task>) => void;
  onDelete?: (taskId: string) => void;
}

export function TaskItem({ task, onUpdate, onDelete }: TaskItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  // 优先级颜色映射
  const getPriorityColor = (priority: TaskPriority): string => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low':
        return 'bg-blue-100 text-blue-700 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  // 优先级标签
  const getPriorityLabel = (priority: TaskPriority): string => {
    switch (priority) {
      case 'high':
        return '高';
      case 'medium':
        return '中';
      case 'low':
        return '低';
      default:
        return '未知';
    }
  };

  // 状态图标
  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <Clock className="h-5 w-5 text-blue-500" />;
      case 'cancelled':
        return <Circle className="h-5 w-5 text-gray-400 line-through" />;
      default:
        return <Circle className="h-5 w-5 text-gray-400" />;
    }
  };

  // 状态标签
  const getStatusLabel = (status: TaskStatus): string => {
    switch (status) {
      case 'pending':
        return '待处理';
      case 'in_progress':
        return '进行中';
      case 'completed':
        return '已完成';
      case 'cancelled':
        return '已取消';
      default:
        return '未知';
    }
  };

  // 切换任务状态
  const toggleStatus = () => {
    let newStatus: TaskStatus;
    if (task.status === 'pending') {
      newStatus = 'in_progress';
    } else if (task.status === 'in_progress') {
      newStatus = 'completed';
    } else if (task.status === 'completed') {
      newStatus = 'pending';
    } else {
      newStatus = 'pending';
    }
    onUpdate(task.id, { status: newStatus });
  };

  // 格式化日期
  const formatDate = (dateString?: string): string => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit'
    });
  };

  // 判断是否逾期
  const isOverdue = (): boolean => {
    if (!task.deadline || task.status === 'completed') return false;
    return new Date(task.deadline) < new Date();
  };

  return (
    <Card className={`p-4 mb-3 transition-all hover:shadow-md ${
      task.status === 'completed' ? 'bg-gray-50 opacity-75' : 'bg-white'
    } ${isOverdue() ? 'border-l-4 border-l-red-500' : ''}`}>
      {/* 任务头部 */}
      <div className="flex items-start gap-3">
        {/* 状态图标（可点击切换） */}
        <button
          onClick={toggleStatus}
          className="mt-1 hover:scale-110 transition-transform"
          aria-label="切换任务状态"
        >
          {getStatusIcon(task.status)}
        </button>

        {/* 任务主体 */}
        <div className="flex-1 min-w-0">
          {/* 标题行 */}
          <div className="flex items-center gap-2 mb-2">
            <h3 className={`text-base font-medium ${
              task.status === 'completed' ? 'line-through text-gray-500' : 'text-gray-900'
            }`}>
              {task.title}
            </h3>

            {/* 优先级标签 */}
            <Badge className={`${getPriorityColor(task.priority)} text-xs`}>
              {getPriorityLabel(task.priority)}
            </Badge>

            {/* 状态标签 */}
            <Badge variant="outline" className="text-xs">
              {getStatusLabel(task.status)}
            </Badge>

            {/* 逾期标签 */}
            {isOverdue() && (
              <Badge className="bg-red-100 text-red-700 text-xs">
                已逾期
              </Badge>
            )}
          </div>

          {/* 元信息 */}
          <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600 mb-2">
            {/* 分类 */}
            <div className="flex items-center gap-1">
              <FileText className="h-4 w-4" />
              <span>{task.category}</span>
            </div>

            {/* 截止时间 */}
            {task.deadline && (
              <div className={`flex items-center gap-1 ${isOverdue() ? 'text-red-600 font-medium' : ''}`}>
                <Clock className="h-4 w-4" />
                <span>{formatDate(task.deadline)}</span>
              </div>
            )}

            {/* 负责人 */}
            {task.assignee && (
              <div className="flex items-center gap-1">
                <User className="h-4 w-4" />
                <span>{task.assignee}</span>
              </div>
            )}

            {/* 预计工时 */}
            {task.estimated_hours && (
              <div className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                <span>{task.estimated_hours}小时</span>
              </div>
            )}

            {/* 来源页码 */}
            {task.source_page && (
              <div className="text-xs text-gray-500">
                第{task.source_page}页
              </div>
            )}

            {/* 置信度 */}
            {task.confidence_score && (
              <div className="text-xs text-gray-500">
                置信度: {task.confidence_score}%
              </div>
            )}
          </div>

          {/* 描述（简短显示） */}
          {task.description && !isExpanded && (
            <p className="text-sm text-gray-600 line-clamp-2">
              {task.description}
            </p>
          )}

          {/* 展开内容 */}
          {isExpanded && (
            <div className="mt-3 space-y-3 border-t pt-3">
              {/* 完整描述 */}
              {task.description && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">任务描述</h4>
                  <p className="text-sm text-gray-600">{task.description}</p>
                </div>
              )}

              {/* 原文内容 */}
              {task.source_content && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">原文摘录</h4>
                  <p className="text-sm text-gray-600 bg-gray-50 p-2 rounded border border-gray-200">
                    {task.source_content}
                  </p>
                </div>
              )}

              {/* 备注 */}
              {task.notes && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">备注</h4>
                  <p className="text-sm text-gray-600">{task.notes}</p>
                </div>
              )}

              {/* 实际工时 */}
              {task.actual_hours && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">实际工时</h4>
                  <p className="text-sm text-gray-600">{task.actual_hours}小时</p>
                </div>
              )}

              {/* 完成时间 */}
              {task.completed_at && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-1">完成时间</h4>
                  <p className="text-sm text-gray-600">{formatDate(task.completed_at)}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* 操作按钮 */}
        <div className="flex items-center gap-1">
          {/* 展开/收起 */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(!isExpanded)}
            className="h-8 w-8 p-0"
          >
            {isExpanded ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </Button>

          {/* 编辑 */}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsEditing(true)}
            className="h-8 w-8 p-0"
          >
            <Edit2 className="h-4 w-4" />
          </Button>

          {/* 删除 */}
          {onDelete && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onDelete(task.id)}
              className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}

