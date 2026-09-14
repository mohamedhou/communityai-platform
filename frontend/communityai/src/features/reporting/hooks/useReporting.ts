import { useMutation, useQuery } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import { downloadReport, getReportPreview } from '../services/reportingApi'
import type { ReportFilters } from '../types/reporting'

export function useReportPreview(filters: ReportFilters) {
  const { accessToken } = useAuth()
  return useQuery({
    queryKey: ['report-preview', filters],
    queryFn: () => getReportPreview(accessToken!, filters),
    enabled: false,
  })
}

export function useReportExport() {
  const { accessToken } = useAuth()
  return useMutation({
    mutationFn: ({ filters, format }: { filters: ReportFilters; format: 'csv' | 'pdf' }) => downloadReport(accessToken!, filters, format),
  })
}