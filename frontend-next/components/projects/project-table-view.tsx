'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Heart, EyeOff, ExternalLink, TrendingUp, MapPin, Calendar, DollarSign, FileText } from 'lucide-react';
import type { ProjectRecommendation } from '@/types/project';
import { generateEvaluationReport, setPreference, checkPreference } from '@/lib/api-v2';
import { useCompany } from '@/contexts/company-context';
import { useEffect } from 'react';

interface ProjectTableViewProps {
  recommendations: ProjectRecommendation[];
  onToggleFavorite?: (projectId: string, isFavorite: boolean) => void;
  onToggleIgnore?: (projectId: string, isIgnored: boolean) => void;
}

export default function ProjectTableView({
  recommendations,
  onToggleFavorite,
  onToggleIgnore,
}: ProjectTableViewProps) {
  const router = useRouter();
  const { state } = useCompany();
  const [generatingReport, setGeneratingReport] = useState<string | null>(null);
  const [favoriteStates, setFavoriteStates] = useState<Record<string, boolean>>({});
  const [ignoreStates, setIgnoreStates] = useState<Record<string, boolean>>({});

  // 加载所有项目的偏好状态
  useEffect(() => {
    const loadPreferences = async () => {
      if (!state.currentCompany?.id) return;

      const states: Record<string, boolean> = {};
      const ignores: Record<string, boolean> = {};

      for (const rec of recommendations) {
        try {
          const pref = await checkPreference(state.currentCompany.id, rec.project.id);
          states[rec.project.id] = pref.is_favorite;
          ignores[rec.project.id] = pref.is_ignored;
        } catch (error) {
          console.error('检查偏好失败:', error);
        }
      }

      setFavoriteStates(states);
      setIgnoreStates(ignores);
    };

    loadPreferences();
  }, [recommendations, state.currentCompany]);

  // 切换收藏状态
  const handleToggleFavorite = async (projectId: string) => {
    if (!state.currentCompany?.id) {
      alert('请先创建企业画像');
      return;
    }

    const isFavorite = favoriteStates[projectId] || false;
    const newState = !isFavorite;

    try {
      if (newState) {
        await setPreference({
          company_id: state.currentCompany.id,
          project_id: projectId,
          preference_type: 'favorite',
          is_active: true,
        });
      } else {
        await setPreference({
          company_id: state.currentCompany.id,
          project_id: projectId,
          preference_type: 'favorite',
          is_active: false,
        });
      }

      setFavoriteStates(prev => ({ ...prev, [projectId]: newState }));
      if (onToggleFavorite) onToggleFavorite(projectId, newState);
    } catch (error: any) {
      console.error('切换收藏失败:', error);
      alert(error.message || '操作失败');
    }
  };

  // 切换忽略状态
  const handleToggleIgnore = async (projectId: string) => {
    if (!state.currentCompany?.id) {
      alert('请先创建企业画像');
      return;
    }

    const isIgnored = ignoreStates[projectId] || false;
    const newState = !isIgnored;

    try {
      if (newState) {
        await setPreference({
          company_id: state.currentCompany.id,
          project_id: projectId,
          preference_type: 'ignore',
          is_active: true,
        });
      } else {
        await setPreference({
          company_id: state.currentCompany.id,
          project_id: projectId,
          preference_type: 'ignore',
          is_active: false,
        });
      }

      setIgnoreStates(prev => ({ ...prev, [projectId]: newState }));
      if (onToggleIgnore) onToggleIgnore(projectId, newState);
    } catch (error: any) {
      console.error('切换忽略失败:', error);
      alert(error.message || '操作失败');
    }
  };

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
    if (score >= 90) return 'text-green-400';
    if (score >= 80) return 'text-blue-400';
    if (score >= 70) return 'text-yellow-400';
    return 'text-gray-400';
  };

  const getScoreBadgeVariant = (score: number) => {
    if (score >= 90) return 'default';
    if (score >= 80) return 'secondary';
    return 'outline';
  };

  const formatBudget = (budget?: number) => {
    if (!budget) return '未公开';
    if (budget >= 10000) return `${(budget / 10000).toFixed(2)}亿`;
    return `${budget}万`;
  };

  const formatDeadline = (deadline?: string) => {
    if (!deadline) return '未设置';
    const date = new Date(deadline);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays < 0) return '已截止';
    if (diffDays === 0) return '今天';
    if (diffDays <= 3) return `${diffDays}天`;
    return date.toLocaleDateString('zh-CN');
  };

  return (
    <Card className="bg-gray-800 border-gray-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700/50 border-b border-gray-600">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                匹配度
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                项目名称
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                预算
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                地域
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                截止时间
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-300 uppercase tracking-wider">
                匹配原因
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-300 uppercase tracking-wider">
                操作
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-700">
            {recommendations.map((rec) => (
              <tr
                key={rec.project.id}
                className="hover:bg-gray-700/50 transition-colors cursor-pointer"
                onClick={() => router.push(`/projects/${rec.project.id}`)}
              >
                {/* 匹配度 */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-2">
                    <TrendingUp className={`h-4 w-4 ${getScoreColor(rec.match_score)}`} />
                    <span className={`text-lg font-bold ${getScoreColor(rec.match_score)}`}>
                      {rec.match_score}
                    </span>
                    <span className="text-xs text-gray-500">分</span>
                  </div>
                </td>

                {/* 项目名称 */}
                <td className="px-6 py-4">
                  <div className="flex flex-col gap-1 max-w-md">
                    <div className="text-white font-medium line-clamp-2">
                      {rec.project.title}
                    </div>
                    {rec.project.publisher && (
                      <div className="text-xs text-gray-400">
                        发布方：{rec.project.publisher}
                      </div>
                    )}
                  </div>
                </td>

                {/* 预算 */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-1 text-gray-300">
                    <DollarSign className="h-4 w-4" />
                    <span>{formatBudget(rec.project.budget)}</span>
                  </div>
                </td>

                {/* 地域 */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-1 text-gray-300">
                    <MapPin className="h-4 w-4" />
                    <span>{rec.project.area || '未知'}</span>
                  </div>
                </td>

                {/* 截止时间 */}
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center gap-1 text-gray-300">
                    <Calendar className="h-4 w-4" />
                    <span>{formatDeadline(rec.project.deadline)}</span>
                  </div>
                </td>

                {/* 匹配原因 */}
                <td className="px-6 py-4">
                  <div className="flex flex-wrap gap-1 max-w-xs">
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
                </td>

                {/* 操作 */}
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => handleGenerateReport(rec.project.id, e)}
                      disabled={generatingReport === rec.project.id}
                      className="text-gray-400 hover:text-green-400"
                      title="快速评估"
                    >
                      <FileText className={`h-4 w-4 ${generatingReport === rec.project.id ? 'animate-pulse' : ''}`} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleFavorite(rec.project.id)}
                      className={favoriteStates[rec.project.id] ? 'text-red-400' : 'text-gray-400 hover:text-red-400'}
                      title={favoriteStates[rec.project.id] ? '取消收藏' : '收藏'}
                    >
                      <Heart className={`h-4 w-4 ${favoriteStates[rec.project.id] ? 'fill-current' : ''}`} />
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleToggleIgnore(rec.project.id)}
                      className={ignoreStates[rec.project.id] ? 'text-yellow-400' : 'text-gray-400 hover:text-gray-300'}
                      title={ignoreStates[rec.project.id] ? '取消忽略' : '忽略'}
                    >
                      <EyeOff className={`h-4 w-4 ${ignoreStates[rec.project.id] ? 'fill-current' : ''}`} />
                    </Button>
                    {rec.project.source_url && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => window.open(rec.project.source_url, '_blank')}
                        className="text-gray-400 hover:text-blue-400"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

