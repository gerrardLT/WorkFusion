'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Plus, Bell, BellOff, Edit, Trash2, Eye } from 'lucide-react';
import { useScenario } from '@/contexts/scenario-context';
import { useCompany } from '@/contexts/company-context';
import { listSubscriptions, deleteSubscription } from '@/lib/api-v2';
import type { Subscription } from '@/types/subscription';

export default function SubscriptionsPage() {
  const router = useRouter();
  const { currentScenario } = useScenario();
  const { state } = useCompany();
  const [subscriptions, setSubscriptions] = useState<Subscription[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    if (state.currentCompany?.id) {
      loadSubscriptions();
    }
  }, [state.currentCompany]);

  const loadSubscriptions = async () => {
    if (!state.currentCompany?.id) return;

    setLoading(true);
    try {
      const response = await listSubscriptions({
        company_id: state.currentCompany.id,
        scenario_id: currentScenario?.id,
        page: 1,
        page_size: 20,
      });
      setSubscriptions(response.subscriptions);
      setTotal(response.total);
    } catch (error) {
      console.error('加载订阅列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除此订阅吗？')) return;

    try {
      await deleteSubscription(id);
      loadSubscriptions();
    } catch (error) {
      console.error('删除订阅失败:', error);
      alert('删除失败');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-700">激活</Badge>;
      case 'paused':
        return <Badge className="bg-yellow-100 text-yellow-700">暂停</Badge>;
      case 'expired':
        return <Badge className="bg-gray-100 text-gray-700">已过期</Badge>;
      default:
        return <Badge>{status}</Badge>;
    }
  };

  if (!state.currentCompany) {
    return (
      <div className="container mx-auto p-6">
        <Card className="p-8 text-center">
          <h2 className="text-xl font-semibold mb-4 text-gray-100">请先创建企业画像</h2>
          <p className="text-gray-400 mb-6">订阅功能需要关联企业画像</p>
          <Button onClick={() => router.push('/company')}>
            创建企业画像
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">订阅管理</h1>
          <p className="text-gray-400 mt-2">管理项目订阅规则，自动接收匹配通知</p>
        </div>
        <Button
          onClick={() => router.push('/subscriptions/create')}
          className="bg-blue-600 hover:bg-blue-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          新建订阅
        </Button>
      </div>

      {/* Subscriptions List */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">加载中...</div>
      ) : subscriptions.length === 0 ? (
        <Card className="p-8 text-center bg-gray-800 border-gray-700">
          <Bell className="h-12 w-12 mx-auto mb-4 text-gray-600" />
          <h3 className="text-lg font-semibold mb-2 text-gray-100">暂无订阅规则</h3>
          <p className="text-gray-400 mb-4">创建订阅规则后，系统会自动推送匹配的项目</p>
          <Button onClick={() => router.push('/subscriptions/create')}>
            <Plus className="h-4 w-4 mr-2" />
            创建第一个订阅
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4">
          {subscriptions.map((subscription) => (
            <Card key={subscription.id} className="p-6 bg-gray-800 border-gray-700">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-gray-100">{subscription.name}</h3>
                    {getStatusBadge(subscription.status)}
                  </div>

                  {subscription.description && (
                    <p className="text-gray-400 mb-4">{subscription.description}</p>
                  )}

                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                    {subscription.keywords && subscription.keywords.length > 0 && (
                      <div>
                        <span className="text-sm text-gray-500">关键词:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {subscription.keywords.slice(0, 3).map((kw, i) => (
                            <Badge key={i} variant="secondary" className="text-xs bg-gray-700 text-gray-300">
                              {kw}
                            </Badge>
                          ))}
                          {subscription.keywords.length > 3 && (
                            <Badge variant="secondary" className="text-xs bg-gray-700 text-gray-300">
                              +{subscription.keywords.length - 3}
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}

                    {subscription.regions && subscription.regions.length > 0 && (
                      <div>
                        <span className="text-sm text-gray-500">地域:</span>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {subscription.regions.slice(0, 2).map((region, i) => (
                            <Badge key={i} variant="secondary" className="text-xs bg-gray-700 text-gray-300">
                              {region}
                            </Badge>
                          ))}
                          {subscription.regions.length > 2 && (
                            <Badge variant="secondary" className="text-xs bg-gray-700 text-gray-300">
                              +{subscription.regions.length - 2}
                            </Badge>
                          )}
                        </div>
                      </div>
                    )}

                    {(subscription.budget_min !== null || subscription.budget_max !== null) && (
                      <div>
                        <span className="text-sm text-gray-500">预算范围:</span>
                        <p className="text-sm text-gray-300 mt-1">
                          {subscription.budget_min ?? '不限'} - {subscription.budget_max ?? '不限'} 万元
                        </p>
                      </div>
                    )}

                    <div>
                      <span className="text-sm text-gray-500">匹配度阈值:</span>
                      <p className="text-sm text-gray-300 mt-1">{subscription.match_score_threshold}分</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
                    <span>总匹配: {subscription.total_matches}</span>
                    <span>总通知: {subscription.total_notifications}</span>
                    {subscription.notify_system && <BellOff className="h-4 w-4 text-blue-400" title="系统通知已开启" />}
                  </div>
                </div>

                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/subscriptions/${subscription.id}`)}
                    className="text-gray-400 hover:text-gray-200"
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => router.push(`/subscriptions/${subscription.id}/edit`)}
                    className="text-blue-400 hover:text-blue-300"
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(subscription.id)}
                    className="text-red-400 hover:text-red-300"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

