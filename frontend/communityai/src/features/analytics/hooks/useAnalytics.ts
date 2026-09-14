import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import { getSocialAccounts } from '../../social-accounts/services/socialApi'
import {
  getAnalyticsSummary,
  getAnalyticsTimeSeries,
  getTopPosts,
  seedMockAnalytics,
} from '../services/analyticsApi'
import type { AnalyticsFiltersState } from '../types/analytics'

export function useAnalytics() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()

  const [filters, setFilters] = useState<AnalyticsFiltersState>({
    social_account_id: 'ALL',
    platform: 'ALL',
    days: 30,
  })

  // Query: Social accounts for filter dropdown
  const { data: accounts = [] } = useQuery({
    queryKey: ['social-accounts'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getSocialAccounts(accessToken)
    },
    enabled: !!accessToken,
  })

  // Query: Summary (KPIs)
  const {
    data: summaryData,
    isLoading: isLoadingSummary,
    isError: isSummaryError,
    error: summaryError,
    refetch: refetchSummary,
  } = useQuery({
    queryKey: ['analytics-summary', filters],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getAnalyticsSummary(accessToken, filters)
    },
    enabled: !!accessToken,
  })

  // Query: Time-Series
  const {
    data: timeSeriesData,
    isLoading: isLoadingTimeSeries,
    isError: isTimeSeriesError,
    error: timeSeriesError,
    refetch: refetchTimeSeries,
  } = useQuery({
    queryKey: ['analytics-timeseries', filters],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getAnalyticsTimeSeries(accessToken, filters)
    },
    enabled: !!accessToken,
  })

  // Query: Top Posts
  const {
    data: topPostsData,
    isLoading: isLoadingTopPosts,
    isError: isTopPostsError,
    error: topPostsError,
    refetch: refetchTopPosts,
  } = useQuery({
    queryKey: ['analytics-top-posts', filters],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getTopPosts(accessToken, filters, 10)
    },
    enabled: !!accessToken,
  })

  // Mutation: Seed mock
  const seedMockMutation = useMutation({
    mutationFn: async (days?: number) => {
      if (!accessToken) throw new Error('Not authenticated')
      return seedMockAnalytics(accessToken, days ?? 30)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analytics-summary'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-timeseries'] })
      queryClient.invalidateQueries({ queryKey: ['analytics-top-posts'] })
    },
  })

  const refetchAll = useCallback(() => {
    refetchSummary()
    refetchTimeSeries()
    refetchTopPosts()
  }, [refetchSummary, refetchTimeSeries, refetchTopPosts])

  const isLoading = isLoadingSummary || isLoadingTimeSeries || isLoadingTopPosts
  const isError = isSummaryError || isTimeSeriesError || isTopPostsError
  const error = summaryError || timeSeriesError || topPostsError

  return {
    filters,
    setFilters,
    accounts,
    summary: summaryData,
    timeSeries: timeSeriesData?.points || [],
    topPosts: topPostsData?.items || [],
    isLoading,
    isError,
    error,
    refetchAll,
    seedMock: (days?: number) => seedMockMutation.mutateAsync(days),
    isSeeding: seedMockMutation.isPending,
  }
}
