export type PostStatus = 'DRAFT' | 'SCHEDULED' | 'PUBLISHING' | 'PUBLISHED' | 'FAILED' | 'CANCELLED';

export type PostApprovalStatus = 'NOT_REQUIRED' | 'PENDING' | 'APPROVED' | 'REJECTED';

export interface Post {
  id: number;
  user_id: number;
  social_account_id: number;
  content: string;
  media_url?: string;
  media_asset_id?: number | null;
  scheduled_at?: string;
  published_at?: string;
  status: PostStatus;
  approval_status: PostApprovalStatus;
  reviewed_by?: number | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  submitted_for_review_at?: string | null;
  external_post_id?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}
export interface CreatePostPayload {
  social_account_id: number
  content: string
  media_url?: string | null
  media_asset_id?: number | null
}

export interface UpdatePostPayload {
  content?: string
  media_url?: string | null
  media_asset_id?: number | null
  social_account_id?: number
}

export interface SchedulePostPayload {
  scheduled_at: string
}
