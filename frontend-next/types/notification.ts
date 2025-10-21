// frontend-next/types/notification.ts

export enum NotificationType {
  PROJECT_MATCH = 'project_match',
  SYSTEM_ALERT = 'system_alert',
  DEADLINE_REMINDER = 'deadline_reminder',
  STATUS_UPDATE = 'status_update',
}

export enum NotificationStatus {
  UNREAD = 'unread',
  READ = 'read',
  ARCHIVED = 'archived',
}

export interface Notification {
  id: string;
  company_id: string;
  subscription_id: string | null;
  project_id: string | null;
  type: NotificationType;
  title: string;
  content: string;
  link_url: string | null;
  status: NotificationStatus;
  is_sent_email: boolean;
  is_sent_webhook: boolean;
  metadata: Record<string, any> | null;
  created_at: string;
  read_at: string | null;
  archived_at: string | null;
}

export interface NotificationListResponse {
  notifications: Notification[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}

