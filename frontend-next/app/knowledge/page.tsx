'use client';

import * as React from 'react';
import { useState, useEffect, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Plus, Grid, List as ListIcon, Calendar, Tag, FileText, Loader2, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';
import { listKnowledgeItems, getKnowledgeStats } from '@/lib/api-v2';
import {
  KnowledgeItem,
  KnowledgeCategory,
  KnowledgeStatus,
  KNOWLEDGE_CATEGORY_LABELS,
  KNOWLEDGE_STATUS_LABELS,
  KNOWLEDGE_STATUS_COLORS,
  KNOWLEDGE_CATEGORY_ICONS,
  KnowledgeStatsResponse
} from '@/types/knowledge';

export default function KnowledgePage() {
  const router = useRouter();
  const { toast } = useToast();

  const [items, setItems] = useState<KnowledgeItem[]>([]);
  const [stats, setStats] = useState<KnowledgeStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<KnowledgeCategory>(KnowledgeCategory.QUALIFICATIONS);
  const [viewMode, setViewMode] = useState<'card' | 'list'>('card');

  // 加载数据
  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [itemsResponse, statsResponse] = await Promise.all([
        listKnowledgeItems({
          scenario_id: 'tender',
          category: selectedCategory,
          search: searchQuery || undefined,
          limit: 100
        }),
        getKnowledgeStats('tender')
      ]);

      setItems(itemsResponse.items);
      setStats(statsResponse);
    } catch (error) {
      console.error('加载知识库失败:', error);
      toast({
        title: "加载失败",
        description: error instanceof Error ? error.message : "未知错误",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [selectedCategory, searchQuery, toast]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // 渲染状态标签
  const renderStatusBadge = (status: KnowledgeStatus) => {
    const colors = KNOWLEDGE_STATUS_COLORS[status];
    return (
      <Badge className={`${colors.bg} ${colors.text} border ${colors.border}`}>
        {KNOWLEDGE_STATUS_LABELS[status]}
      </Badge>
    );
  };

  // 渲染卡片视图
  const renderCardView = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {items.map((item) => (
        <Card key={item.id} className="p-4 hover:shadow-lg transition-shadow bg-gray-800 border-gray-700">
          <div className="flex items-start justify-between mb-3">
            <div className="flex items-center space-x-2">
              <span className="text-2xl">{KNOWLEDGE_CATEGORY_ICONS[item.category]}</span>
              <div>
                <h3 className="font-semibold text-gray-100">{item.title}</h3>
                <p className="text-xs text-gray-400">
                  {new Date(item.created_at).toLocaleDateString('zh-CN')}
                </p>
              </div>
            </div>
            {renderStatusBadge(item.status)}
          </div>

          {item.description && (
            <p className="text-sm text-gray-300 mb-3 line-clamp-2">{item.description}</p>
          )}

          {item.tags && item.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mb-3">
              {item.tags.slice(0, 3).map((tag, index) => (
                <Badge key={index} variant="outline" className="text-xs bg-gray-700 text-gray-200 border-gray-600">
                  {tag}
                </Badge>
              ))}
              {item.tags.length > 3 && (
                <Badge variant="outline" className="text-xs bg-gray-700 text-gray-200 border-gray-600">
                  +{item.tags.length - 3}
                </Badge>
              )}
            </div>
          )}

          {item.expire_date && (
            <div className="flex items-center text-xs text-gray-400 mb-3">
              <Calendar className="h-3 w-3 mr-1" />
              到期日期: {item.expire_date}
            </div>
          )}

          <div className="flex items-center justify-between text-xs text-gray-500">
            <span>查看 {item.view_count} 次</span>
            <Button variant="ghost" size="sm" className="text-blue-400 hover:text-blue-300">
              查看详情
            </Button>
          </div>
        </Card>
      ))}
    </div>
  );

  // 渲染列表视图
  const renderListView = () => (
    <div className="space-y-2">
      {items.map((item) => (
        <Card key={item.id} className="p-4 hover:bg-gray-750 transition-colors bg-gray-800 border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4 flex-1">
              <span className="text-2xl">{KNOWLEDGE_CATEGORY_ICONS[item.category]}</span>
              <div className="flex-1">
                <h3 className="font-semibold text-gray-100">{item.title}</h3>
                <p className="text-sm text-gray-400">{item.description}</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {item.expire_date && (
                <span className="text-sm text-gray-400">{item.expire_date}</span>
              )}
              {renderStatusBadge(item.status)}
              <Button variant="ghost" size="sm" className="text-blue-400 hover:text-blue-300">
                查看
              </Button>
            </div>
          </div>
        </Card>
      ))}
    </div>
  );

  return (
    <div className="h-screen flex flex-col bg-gray-900">
      {/* 顶部导航栏 */}
      <div className="bg-gray-800 border-b border-gray-700 p-4">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-100">知识库管理</h1>
            <p className="text-sm text-gray-400 mt-1">管理企业资质、业绩、方案和人员档案</p>
          </div>
          <Button className="bg-blue-600 hover:bg-blue-700">
            <Plus className="h-4 w-4 mr-2" />
            新增知识
          </Button>
        </div>

        {/* 统计信息 */}
        {stats && (
          <div className="grid grid-cols-4 gap-4">
            {Object.entries(KNOWLEDGE_CATEGORY_LABELS).map(([key, label]) => (
              <Card key={key} className="p-3 bg-gray-700 border-gray-600">
                <div className="text-sm text-gray-400">{label}</div>
                <div className="text-2xl font-bold text-gray-100 mt-1">
                  {stats.by_category[key] || 0}
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      {/* 主内容区域 */}
      <div className="flex-1 overflow-auto p-6">
        {/* 分类Tab和工具栏 */}
        <div className="mb-6">
          <Tabs value={selectedCategory} onValueChange={(value) => setSelectedCategory(value as KnowledgeCategory)}>
            <div className="flex items-center justify-between mb-4">
              <TabsList className="bg-gray-800">
                {Object.entries(KNOWLEDGE_CATEGORY_LABELS).map(([key, label]) => (
                  <TabsTrigger key={key} value={key} className="data-[state=active]:bg-gray-700">
                    {KNOWLEDGE_CATEGORY_ICONS[key as KnowledgeCategory]} {label}
                  </TabsTrigger>
                ))}
              </TabsList>

              <div className="flex items-center space-x-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="搜索知识库..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 w-64 bg-gray-800 border-gray-700 text-gray-200"
                  />
                </div>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setViewMode('card')}
                  className={viewMode === 'card' ? 'bg-gray-700' : 'bg-gray-800'}
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => setViewMode('list')}
                  className={viewMode === 'list' ? 'bg-gray-700' : 'bg-gray-800'}
                >
                  <ListIcon className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {Object.values(KnowledgeCategory).map((category) => (
              <TabsContent key={category} value={category}>
                {loading ? (
                  <div className="flex items-center justify-center h-64">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
                    <span className="ml-2 text-gray-400">加载中...</span>
                  </div>
                ) : items.length === 0 ? (
                  <Card className="p-12 text-center bg-gray-800 border-gray-700">
                    <FileText className="h-12 w-12 text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-400">暂无{KNOWLEDGE_CATEGORY_LABELS[category]}数据</p>
                    <Button className="mt-4 bg-blue-600 hover:bg-blue-700">
                      <Plus className="h-4 w-4 mr-2" />
                      添加第一个
                    </Button>
                  </Card>
                ) : (
                  viewMode === 'card' ? renderCardView() : renderListView()
                )}
              </TabsContent>
            ))}
          </Tabs>
        </div>
      </div>
    </div>
  );
}

