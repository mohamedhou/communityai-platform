export type PostStatus = 'DRAFT' | 'SCHEDULED' | 'PUBLISHING' | 'PUBLISHED' | 'FAILED' | 'CANCELLED';

export interface Post {
  id: number;
  user_id: number;
  social_account_id: number;
  content: string;
  media_url?: string;
  scheduled_at?: string;
  published_at?: string;
  status: PostStatus;
  external_post_id?: string;
  error_message?: string;
  created_at: string;
  updated_at: string;
}
export interface CreatePostPayload {
  social_account_id: number
  content: string
  media_url?: string | null
}

export interface UpdatePostPayload {
  content?: string
  media_url?: string | null
  social_account_id?: number
}

export interface SchedulePostPayload {
  scheduled_at: string
}
