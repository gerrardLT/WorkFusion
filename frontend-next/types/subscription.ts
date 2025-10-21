// frontend-next/types/subscription.ts

export enum SubscriptionStatus {
  ACTIVE = 'active',
  PAUSED = 'paused',
  EXPIRED = 'expired',
}

export interface Subscription {
  id: string;
  company_id: string;
  scenario_id: string;
  name: string;
  description: string | null;
  status: SubscriptionStatus;
  keywords: string[];
  regions: string[];
  budget_min: number | null;
  budget_max: number | null;
  match_score_threshold: number;
  notify_system: boolean;
  notify_email: boolean;
  notify_webhook: boolean;
  max_notifications_per_day: number;
  total_matches: number;
  total_notifications: number;
  last_match_at: string | null;
  created_at: string;
  updated_at: string;
  expires_at: string | null;
}

export interface CreateSubscriptionRequest {
  company_id: string;
  scenario_id?: string;
  name: string;
  description?: string;
  keywords?: string[];
  regions?: string[];
  budget_min?: number;
  budget_max?: number;
  match_score_threshold?: number;
  notify_system?: boolean;
  notify_email?: boolean;
  notify_webhook?: boolean;
  max_notifications_per_day?: number;
  expires_at?: string;
  metadata?: Record<string, any>;
}

export interface UpdateSubscriptionRequest {
  name?: string;
  description?: string;
  keywords?: string[];
  regions?: string[];
  budget_min?: number;
  budget_max?: number;
  match_score_threshold?: number;
  status?: SubscriptionStatus;
  notify_system?: boolean;
  notify_email?: boolean;
  notify_webhook?: boolean;
  max_notifications_per_day?: number;
  expires_at?: string;
  metadata?: Record<string, any>;
}

export interface SubscriptionListResponse {
  subscriptions: Subscription[];
  total: number;
  page: number;
  page_size: number;
}

