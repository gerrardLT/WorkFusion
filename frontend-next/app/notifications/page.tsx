'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Bell, Check, Archive, Trash2, ExternalLink } from 'lucide-react';
import { useCompany } from '@/contexts/company-context';
import {
  listNotifications,
  markNotificationAsRead,
  markNotificationAsArchived,
  markAllNotificationsAsRead,
  deleteNotification
} from '@/lib/api-v2';
import type { Notification } from '@/types/notification';

export default function NotificationsPage() {
  const router = useRouter();
  const { state } = useCompany();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);

  useEffect(() => {
    if (state.currentCompany?.id) {
      loadNotifications();
    }
  }, [state.currentCompany]);

  const loadNotifications = async () => {
    if (!state.currentCompany?.id) return;

    setLoading(true);
    try {
      const response = await listNotifications({
        company_id: state.currentCompany.id,
        page: 1,
        page_size: 50,
      });
      setNotifications(response.notifications);
      setUnreadCount(response.unread_count);
    } catch (error) {
      console.error('加载通知列表失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (id: string) => {
    try {
      await markNotificationAsRead(id);
      loadNotifications();
    } catch (error) {
      console.error('标记通知为已读失败:', error);
    }
  };

  const handleMarkAllAsRead = async () => {
    if (!state.currentCompany?.id) return;
    try {
      await markAllNotificationsAsRead(state.currentCompany.id);
      loadNotifications();
    } catch (error) {
      console.error('标记所有通知为已读失败:', error);
    }
  };

  const handleArchive = async (id: string) => {
    try {
      await markNotificationAsArchived(id);
      loadNotifications();
    } catch (error) {
      console.error('归档通知失败:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除此通知吗？')) return;
    try {
      await deleteNotification(id);
      loadNotifications();
    } catch (error) {
      console.error('删除通知失败:', error);
    }
  };

  const getTypeBadge = (type: string) => {
    switch (type) {
      case 'project_match':
        return <Badge className="bg-blue-100 text-blue-700">项目匹配</Badge>;
      case 'system_alert':
        return <Badge className="bg-red-100 text-red-700">系统警告</Badge>;
      case 'deadline_reminder':
        return <Badge className="bg-yellow-100 text-yellow-700">截止提醒</Badge>;
      default:
        return <Badge>{type}</Badge>;
    }
  };

  if (!state.currentCompany) {
    return (
      <div className="container mx-auto p-6">
        <Card className="p-8 text-center">
          <h2 className="text-xl font-semibold mb-4 text-gray-100">请先创建企业画像</h2>
          <p className="text-gray-400 mb-6">通知功能需要关联企业画像</p>
          <Button onClick={() => router.push('/company')}>
            创建企业画像
          </Button>
        </Card>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      {/* Header */}
      <div className="mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-100">通知中心</h1>
          <p className="text-gray-400 mt-2">
            {unreadCount > 0 && `${unreadCount} 条未读`}
          </p>
        </div>
        {unreadCount > 0 && (
          <Button
            onClick={handleMarkAllAsRead}
            variant="outline"
            className="border-gray-600 text-gray-300"
          >
            <Check className="h-4 w-4 mr-2" />
            全部已读
          </Button>
        )}
      </div>

      {/* Notifications List */}
      {loading ? (
        <div className="text-center py-12 text-gray-400">加载中...</div>
      ) : notifications.length === 0 ? (
        <Card className="p-8 text-center bg-gray-800 border-gray-700">
          <Bell className="h-12 w-12 mx-auto mb-4 text-gray-600" />
          <h3 className="text-lg font-semibold mb-2 text-gray-100">暂无通知</h3>
          <p className="text-gray-400">订阅规则匹配后，通知会显示在这里</p>
        </Card>
      ) : (
        <div className="space-y-3">
          {notifications.map((notification) => (
            <Card
              key={notification.id}
              className={`p-4 bg-gray-800 border-gray-700 transition-all ${
                notification.status === 'unread' ? 'border-l-4 border-l-blue-500' : ''
              }`}
            >
              <div className="flex gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    {getTypeBadge(notification.type)}
                    {notification.status === 'unread' && (
                      <Badge variant="secondary" className="bg-blue-900 text-blue-300">未读</Badge>
                    )}
                  </div>

                  <h3 className="font-semibold text-gray-100 mb-2">{notification.title}</h3>
                  <p className="text-sm text-gray-400 whitespace-pre-line">
                    {notification.content}
                  </p>

                  <div className="flex items-center gap-4 mt-3 text-xs text-gray-500">
                    <span>{new Date(notification.created_at).toLocaleString('zh-CN')}</span>
                    {notification.link_url && (
                      <button
                        onClick={() => router.push(notification.link_url!)}
                        className="flex items-center gap-1 text-blue-400 hover:text-blue-300"
                      >
                        查看详情 <ExternalLink className="h-3 w-3" />
                      </button>
                    )}
                  </div>
                </div>

                <div className="flex flex-col gap-2">
                  {notification.status === 'unread' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleMarkAsRead(notification.id)}
                      className="text-blue-400 hover:text-blue-300"
                      title="标记已读"
                    >
                      <Check className="h-4 w-4" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleArchive(notification.id)}
                    className="text-gray-400 hover:text-gray-200"
                    title="归档"
                  >
                    <Archive className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleDelete(notification.id)}
                    className="text-red-400 hover:text-red-300"
                    title="删除"
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

