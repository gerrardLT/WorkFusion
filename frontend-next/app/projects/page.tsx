'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, Grid, List, RefreshCw } from 'lucide-react';
import ProjectTableView from '@/components/projects/project-table-view';
import ProjectCardView from '@/components/projects/project-card-view';
import ProjectFilters from '@/components/projects/project-filters';
import type { ProjectRecommendation, ProjectFilters as Filters, ProjectSortOptions } from '@/types/project';
import { getRecommendations } from '@/lib/api-v2';

export default function ProjectsPage() {
  const router = useRouter();
  const [viewMode, setViewMode] = useState<'table' | 'card'>('table');
  const [loading, setLoading] = useState(true);
  const [recommendations, setRecommendations] = useState<ProjectRecommendation[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);

  // 筛选和排序状态
  const [filters, setFilters] = useState<Filters>({
    min_score: 70,
  });
  const [sortOptions, setSortOptions] = useState<ProjectSortOptions>({
    sort_by: 'match_score',
    order: 'desc',
  });

  // 加载推荐列表
  const loadRecommendations = async () => {
    setLoading(true);
    try {
      const response = await getRecommendations({
        ...filters,
        ...sortOptions,
        page,
        page_size: pageSize,
      });
      setRecommendations(response.recommendations);
      setTotal(response.total);
    } catch (error: any) {
      console.error('加载推荐失败:', error);
      alert(error.message || '加载推荐失败');
    } finally {
      setLoading(false);
    }
  };

  // 初始加载和筛选/排序/分页变化时重新加载
  useEffect(() => {
    loadRecommendations();
  }, [filters, sortOptions, page]);

  // 刷新推荐
  const handleRefresh = () => {
    loadRecommendations();
  };

  // 应用筛选
  const handleApplyFilters = (newFilters: Filters) => {
    setFilters(newFilters);
    setPage(1); // 重置到第一页
  };

  // 应用排序
  const handleApplySort = (newSort: ProjectSortOptions) => {
    setSortOptions(newSort);
    setPage(1); // 重置到第一页
  };

  // 切换收藏/忽略
  const handleToggleFavorite = async (projectId: string, isFavorite: boolean) => {
    // TODO: 实现收藏功能
    console.log('Toggle favorite:', projectId, isFavorite);
  };

  const handleToggleIgnore = async (projectId: string, isIgnored: boolean) => {
    // TODO: 实现忽略功能
    console.log('Toggle ignore:', projectId, isIgnored);
  };

  return (
    <div className="min-h-screen bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        {/* 标题栏 */}
        <div className="mb-8">
          <Button
            variant="ghost"
            onClick={() => router.push('/')}
            className="mb-4 text-gray-300 hover:text-white"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            返回首页
          </Button>
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">项目推荐</h1>
              <p className="text-gray-400">
                根据您的企业画像，为您精准推荐匹配的招标项目
              </p>
            </div>
            <div className="flex items-center gap-2">
              {/* 刷新按钮 */}
              <Button
                variant="outline"
                onClick={handleRefresh}
                disabled={loading}
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                刷新
              </Button>

              {/* 视图切换 */}
              <div className="flex border border-gray-600 rounded-lg overflow-hidden">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setViewMode('table')}
                  className={`rounded-none ${
                    viewMode === 'table'
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <List className="h-4 w-4 mr-2" />
                  表格
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setViewMode('card')}
                  className={`rounded-none border-l border-gray-600 ${
                    viewMode === 'card'
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'text-gray-300 hover:bg-gray-700'
                  }`}
                >
                  <Grid className="h-4 w-4 mr-2" />
                  卡片
                </Button>
              </div>
            </div>
          </div>
        </div>

        {/* 筛选器 */}
        <Card className="bg-gray-800 border-gray-700 p-6 mb-6">
          <ProjectFilters
            filters={filters}
            sortOptions={sortOptions}
            onApplyFilters={handleApplyFilters}
            onApplySort={handleApplySort}
          />
        </Card>

        {/* 统计信息 */}
        <div className="mb-6">
          <p className="text-gray-400 text-sm">
            找到 <span className="text-white font-semibold">{total}</span> 个匹配项目
          </p>
        </div>

        {/* 列表内容 */}
        {loading ? (
          <Card className="bg-gray-800 border-gray-700 p-12 text-center">
            <div className="flex flex-col items-center gap-4">
              <RefreshCw className="h-8 w-8 text-blue-500 animate-spin" />
              <p className="text-gray-400">加载中...</p>
            </div>
          </Card>
        ) : recommendations.length === 0 ? (
          <Card className="bg-gray-800 border-gray-700 p-12 text-center">
            <p className="text-gray-400 mb-4">暂无推荐项目</p>
            <p className="text-gray-500 text-sm mb-6">
              请先完善企业画像信息，或调整筛选条件
            </p>
            <Button
              onClick={() => router.push('/company')}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              完善企业画像
            </Button>
          </Card>
        ) : viewMode === 'table' ? (
          <ProjectTableView
            recommendations={recommendations}
            onToggleFavorite={handleToggleFavorite}
            onToggleIgnore={handleToggleIgnore}
          />
        ) : (
          <ProjectCardView
            recommendations={recommendations}
            onToggleFavorite={handleToggleFavorite}
            onToggleIgnore={handleToggleIgnore}
          />
        )}

        {/* 分页 */}
        {!loading && recommendations.length > 0 && (
          <div className="mt-6 flex items-center justify-center gap-2">
            <Button
              variant="outline"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              上一页
            </Button>
            <span className="text-gray-400 px-4">
              第 {page} 页 / 共 {Math.ceil(total / pageSize)} 页
            </span>
            <Button
              variant="outline"
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / pageSize)}
              className="border-gray-600 text-gray-300 hover:bg-gray-700"
            >
              下一页
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

