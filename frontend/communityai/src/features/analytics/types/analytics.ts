export interface AnalyticsKpiSummary {
  total_followers: number
  follower_growth: number
  total_impressions: number
  total_reach: number
  total_engagement: number
  engagement_rate: number
  total_likes: number
  total_comments: number
  total_shares: number
  total_clicks: number
  posts_published: number
}

export interface AnalyticsSummaryResponse {
  period_start: string
  period_end: string
  kpis: AnalyticsKpiSummary
  social_account_id?: number | null
  platform?: string | null
  accounts_count: number
}

export interface AnalyticsTimeSeriesPoint {
  date: string
  followers: number
  follower_growth: number
  impressions: number
  reach: number
  engagement: number
  engagement_rate: number
  likes: number
  comments: number
  shares: number
  clicks: number
  posts_published: number
}

export interface AnalyticsTimeSeriesResponse {
  period_start: string
  period_end: string
  points: AnalyticsTimeSeriesPoint[]
}

export interface TopPostMetric {
  post_id: number
  content: string
  media_url?: string | null
  platform: string
  account_name: string
  published_at?: string | null
  likes: number
  comments: number
  shares: number
  clicks: number
  impressions: number
  reach: number
  engagement: number
  engagement_rate: number
}

export interface TopPostsResponse {
  items: TopPostMetric[]
  total: number
}

export interface AnalyticsFiltersState {
  social_account_id?: number | 'ALL'
  platform?: string | 'ALL'
  days?: number
  start_date?: string
  end_date?: string
}

export interface AnalyticsSeedResponse {
  message: string
  snapshots_created: number
}
