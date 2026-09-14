import { API_BASE_URL } from '../../../lib/env'
import type {
  AnalyticsFiltersState,
  AnalyticsSeedResponse,
  AnalyticsSummaryResponse,
  AnalyticsTimeSeriesResponse,
  TopPostsResponse,
} from '../types/analytics'

const API_BASE = `${API_BASE_URL}/api/v1/analytics`

function buildParams(filters?: AnalyticsFiltersState, extraParams?: Record<string, string | number>): URLSearchParams {
  const params = new URLSearchParams()
  if (filters?.social_account_id && filters.social_account_id !== 'ALL') {
    params.append('social_account_id', filters.social_account_id.toString())
  }
  if (filters?.platform && filters.platform !== 'ALL') {
    params.append('platform', filters.platform)
  }
  if (filters?.days) {
    params.append('days', filters.days.toString())
  }
  if (filters?.start_date) {
    params.append('start_date', filters.start_date)
  }
  if (filters?.end_date) {
    params.append('end_date', filters.end_date)
  }
  if (extraParams) {
    for (const [key, val] of Object.entries(extraParams)) {
      params.append(key, val.toString())
    }
  }
  return params
}

export async function getAnalyticsSummary(
  token: string,
  filters?: AnalyticsFiltersState,
): Promise<AnalyticsSummaryResponse> {
  const params = buildParams(filters)
  const res = await fetch(`${API_BASE}/summary?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch analytics summary' }))
    throw new Error(err.detail || 'Failed to fetch analytics summary')
  }
  return res.json()
}

export async function getAnalyticsTimeSeries(
  token: string,
  filters?: AnalyticsFiltersState,
): Promise<AnalyticsTimeSeriesResponse> {
  const params = buildParams(filters)
  const res = await fetch(`${API_BASE}/timeseries?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch time series' }))
    throw new Error(err.detail || 'Failed to fetch time series')
  }
  return res.json()
}

export async function getTopPosts(
  token: string,
  filters?: AnalyticsFiltersState,
  limit = 10,
): Promise<TopPostsResponse> {
  const params = buildParams(filters, { limit })
  const res = await fetch(`${API_BASE}/top-posts?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to fetch top posts' }))
    throw new Error(err.detail || 'Failed to fetch top posts')
  }
  return res.json()
}

export async function seedMockAnalytics(
  token: string,
  days = 30,
): Promise<AnalyticsSeedResponse> {
  const res = await fetch(`${API_BASE}/seed-mock?days=${days}`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Failed to seed mock analytics' }))
    throw new Error(err.detail || 'Failed to seed mock analytics')
  }
  return res.json()
}
