'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Heart, EyeOff, ExternalLink, TrendingUp, MapPin, Calendar, DollarSign, Building2, FileText } from 'lucide-react';
import type { ProjectRecommendation } from '@/types/project';
import { generateEvaluationReport } from '@/lib/api-v2';
import { useCompany } from '@/contexts/company-context';

interface ProjectCardViewProps {
  recommendations: ProjectRecommendation[];
  onToggleFavorite: (projectId: string, isFavorite: boolean) => void;
  onToggleIgnore: (projectId: string, isIgnored: boolean) => void;
}

export default function ProjectCardView({
  recommendations,
  onToggleFavorite,
  onToggleIgnore,
}: ProjectCardViewProps) {
  const router = useRouter();
  const { state } = useCompany();
  const [generatingReport, setGeneratingReport] = useState<string | null>(null);

  // 生成评估报告
  const handleGenerateReport = async (projectId: string, e: React.MouseEvent) => {
    e.stopPropagation();

    // 检查是否有企业画像
    if (!state.currentCompany?.id) {
      if (confirm('需要先创建企业画像才能生成评估报告，是否前往创建？')) {
        router.push('/company');
      }
      return;
    }

    setGeneratingReport(projectId);

    try {
      const response = await generateEvaluationReport({
        project_id: projectId,
        company_id: state.currentCompany.id,
        include_pdf: true,
      });

      if (response.success && response.report_id) {
        alert('评估报告生成成功！');
        router.push(`/evaluations/${response.report_id}`);
      } else {
        alert(response.message || '报告生成失败');
      }
    } catch (error: any) {
      console.error('生成报告失败:', error);
      alert(error.message || '生成报告失败');
    } finally {
      setGeneratingReport(null);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'bg-green-600';
    if (score >= 80) return 'bg-blue-600';
    if (score >= 70) return 'bg-yellow-600';
    return 'bg-gray-600';
  };

  const formatBudget = (budget?: number) => {
    if (!budget) return '预算未公开';
    if (budget >= 10000) return `${(budget / 10000).toFixed(2)}亿元`;
    return `${budget}万元`;
  };

  const formatDeadline = (deadline?: string) => {
    if (!deadline) return '未设置截止时间';
    const date = new Date(deadline);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return '已截止';
    if (diffDays === 0) return '今天截止';
    if (diffDays <= 3) return `${diffDays}天后截止`;
    return `${date.toLocaleDateString('zh-CN')} 截止`;
  };

  const getDeadlineUrgency = (deadline?: string) => {
    if (!deadline) return 'normal';
    const date = new Date(deadline);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return 'expired';
    if (diffDays <= 3) return 'urgent';
    return 'normal';
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {recommendations.map((rec) => {
        const urgency = getDeadlineUrgency(rec.project.deadline);

        return (
          <Card
            key={rec.project.id}
            className="bg-gray-800 border-gray-700 hover:border-blue-600 transition-all cursor-pointer overflow-hidden group"
            onClick={() => router.push(`/projects/${rec.project.id}`)}
          >
            {/* 匹配度横条 */}
            <div className={`h-2 ${getScoreColor(rec.match_score)}`} />

            <div className="p-6">
              {/* 头部 */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  <div className={`${getScoreColor(rec.match_score)} rounded-lg p-2`}>
                    <TrendingUp className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-white">{rec.match_score}</div>
                    <div className="text-xs text-gray-500">匹配度</div>
                  </div>
                </div>

                {/* 操作按钮 */}
                <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onToggleFavorite(rec.project.id, false)}
                    className="text-gray-400 hover:text-red-400"
                  >
                    <Heart className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onToggleIgnore(rec.project.id, false)}
                    className="text-gray-400 hover:text-gray-300"
                  >
                    <EyeOff className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* 项目标题 */}
              <h3 className="text-white font-semibold text-lg mb-3 line-clamp-2 group-hover:text-blue-400 transition-colors">
                {rec.project.title}
              </h3>

              {/* 发布方 */}
              {rec.project.publisher && (
                <div className="flex items-center gap-2 mb-3 text-gray-400 text-sm">
                  <Building2 className="h-4 w-4" />
                  <span className="line-clamp-1">{rec.project.publisher}</span>
                </div>
              )}

              {/* 项目信息 */}
              <div className="space-y-2 mb-4">
                {/* 预算 */}
                <div className="flex items-center gap-2 text-gray-300 text-sm">
                  <DollarSign className="h-4 w-4 text-gray-500" />
                  <span>{formatBudget(rec.project.budget)}</span>
                </div>

                {/* 地域 */}
                {rec.project.area && (
                  <div className="flex items-center gap-2 text-gray-300 text-sm">
                    <MapPin className="h-4 w-4 text-gray-500" />
                    <span>{rec.project.area}</span>
                  </div>
                )}

                {/* 截止时间 */}
                <div className="flex items-center gap-2 text-sm">
                  <Calendar className={`h-4 w-4 ${
                    urgency === 'urgent' ? 'text-red-500' : 'text-gray-500'
                  }`} />
                  <span className={urgency === 'urgent' ? 'text-red-400 font-medium' : 'text-gray-300'}>
                    {formatDeadline(rec.project.deadline)}
                  </span>
                  {urgency === 'urgent' && (
                    <Badge variant="outline" className="bg-red-900/20 text-red-400 border-red-800 text-xs">
                      紧急
                    </Badge>
                  )}
                </div>
              </div>

              {/* 匹配原因 */}
              <div className="flex flex-wrap gap-1 mb-4">
                {rec.match_details.qualification_match && (
                  <Badge variant="outline" className="bg-green-900/20 text-green-400 border-green-800 text-xs">
                    资质匹配
                  </Badge>
                )}
                {rec.match_details.area_match && (
                  <Badge variant="outline" className="bg-blue-900/20 text-blue-400 border-blue-800 text-xs">
                    地域匹配
                  </Badge>
                )}
                {rec.match_details.budget_match && (
                  <Badge variant="outline" className="bg-purple-900/20 text-purple-400 border-purple-800 text-xs">
                    预算匹配
                  </Badge>
                )}
                {rec.match_details.capability_match && (
                  <Badge variant="outline" className="bg-orange-900/20 text-orange-400 border-orange-800 text-xs">
                    能力匹配
                  </Badge>
                )}
              </div>

              {/* 底部操作 */}
              <div className="flex items-center gap-2 pt-4 border-t border-gray-700">
                <Button
                  variant="outline"
                  size="sm"
                  className="flex-1 border-gray-600 text-gray-300 hover:bg-green-600 hover:text-white hover:border-green-600"
                  onClick={(e) => handleGenerateReport(rec.project.id, e)}
                  disabled={generatingReport === rec.project.id}
                >
                  <FileText className={`h-4 w-4 mr-2 ${generatingReport === rec.project.id ? 'animate-pulse' : ''}`} />
                  {generatingReport === rec.project.id ? '生成中...' : '快速评估'}
                </Button>
                {rec.project.source_url && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation();
                      window.open(rec.project.source_url, '_blank');
                    }}
                    className="border-gray-600 text-gray-300 hover:bg-gray-700"
                  >
                    <ExternalLink className="h-4 w-4" />
                  </Button>
                )}
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}

