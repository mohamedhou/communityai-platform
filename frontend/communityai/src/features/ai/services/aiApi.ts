import { API_BASE_URL } from '../../../lib/env'
import type {
  AIAdaptPlatformPayload,
  AIChangeTonePayload,
  AIExpandPayload,
  AIGeneratePayload,
  AIIdeasPayload,
  AIImprovePayload,
  AIResponse,
  AIRewritePayload,
  AIShortenPayload,
} from '../types/ai'

const API_BASE = `${API_BASE_URL}/api/v1/ai`

async function postAI<T>(endpoint: string, token: string, payload: T): Promise<AIResponse> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'AI generation failed' }))
    const message =
      typeof errorData.detail === 'string'
        ? errorData.detail
        : Array.isArray(errorData.detail)
          ? errorData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ')
          : 'AI generation failed'
    throw new Error(message)
  }

  return res.json()
}

export async function generatePost(token: string, payload: AIGeneratePayload): Promise<AIResponse> {
  return postAI('/generate', token, payload)
}

export async function rewriteContent(token: string, payload: AIRewritePayload): Promise<AIResponse> {
  return postAI('/rewrite', token, payload)
}

export async function improveContent(token: string, payload: AIImprovePayload): Promise<AIResponse> {
  return postAI('/improve', token, payload)
}

export async function shortenContent(token: string, payload: AIShortenPayload): Promise<AIResponse> {
  return postAI('/shorten', token, payload)
}

export async function expandContent(token: string, payload: AIExpandPayload): Promise<AIResponse> {
  return postAI('/expand', token, payload)
}

export async function changeTone(token: string, payload: AIChangeTonePayload): Promise<AIResponse> {
  return postAI('/change-tone', token, payload)
}

export async function adaptPlatform(token: string, payload: AIAdaptPlatformPayload): Promise<AIResponse> {
  return postAI('/adapt-platform', token, payload)
}

export async function generateIdeas(token: string, payload: AIIdeasPayload): Promise<AIResponse> {
  return postAI('/ideas', token, payload)
}
