import { apiGet } from './api'
import type { HealthStatus } from '../types/health'

export function getHealthStatus(): Promise<HealthStatus> {
  return apiGet<HealthStatus>('/health')
}
