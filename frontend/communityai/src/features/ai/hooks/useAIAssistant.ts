import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import * as aiApi from '../services/aiApi'
import type {
  AIAction,
  AIHistoryItem,
  AIPlatform,
  AIResponse,
  AITone,
} from '../types/ai'

const HISTORY_STORAGE_KEY = 'communityai_ai_history_v1'

export function useAIAssistant() {
  const { accessToken } = useAuth()
  const navigate = useNavigate()

  // Form State
  const [action, setAction] = useState<AIAction>('GENERATE')
  const [prompt, setPrompt] = useState('')
  const [content, setContent] = useState('')
  const [platform, setPlatform] = useState<AIPlatform | ''>('LINKEDIN')
  const [tone, setTone] = useState<AITone>('PROFESSIONAL')
  const [audience, setAudience] = useState('')
  const [objective, setObjective] = useState('')
  const [editorialContext, setEditorialContext] = useState('')
  const [showEditorialContext, setShowEditorialContext] = useState(false)

  // Result & UI State
  const [result, setResult] = useState<AIResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // History State
  const [history, setHistory] = useState<AIHistoryItem[]>(() => {
    try {
      const saved = localStorage.getItem(HISTORY_STORAGE_KEY)
      return saved ? JSON.parse(saved) : []
    } catch {
      return []
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(history.slice(0, 20)))
    } catch {
      // Storage unavailable or full
    }
  }, [history])

  // Mutation
  const aiMutation = useMutation({
    mutationFn: async () => {
      if (!accessToken) throw new Error('Not authenticated')
      setError(null)

      const plat = platform ? (platform as AIPlatform) : undefined
      const editCtx = editorialContext.trim() || undefined

      switch (action) {
        case 'GENERATE': {
          if (!prompt.trim()) throw new Error('Please enter a topic or instructions.')
          return aiApi.generatePost(accessToken, {
            prompt: prompt.trim(),
            platform: plat,
            tone,
            audience: audience.trim() || undefined,
            objective: objective.trim() || undefined,
            editorial_context: editCtx,
          })
        }
        case 'REWRITE': {
          if (!content.trim()) throw new Error('Please enter text to rewrite.')
          return aiApi.rewriteContent(accessToken, {
            content: content.trim(),
            tone,
            platform: plat,
            editorial_context: editCtx,
          })
        }
        case 'IMPROVE': {
          if (!content.trim()) throw new Error('Please enter text to improve.')
          return aiApi.improveContent(accessToken, {
            content: content.trim(),
            platform: plat,
            editorial_context: editCtx,
          })
        }
        case 'SHORTEN': {
          if (!content.trim()) throw new Error('Please enter text to shorten.')
          return aiApi.shortenContent(accessToken, {
            content: content.trim(),
            platform: plat,
            editorial_context: editCtx,
          })
        }
        case 'EXPAND': {
          if (!content.trim()) throw new Error('Please enter text to expand.')
          return aiApi.expandContent(accessToken, {
            content: content.trim(),
            platform: plat,
            editorial_context: editCtx,
          })
        }
        case 'CHANGE_TONE': {
          if (!content.trim()) throw new Error('Please enter text to transform.')
          return aiApi.changeTone(accessToken, {
            content: content.trim(),
            tone,
            platform: plat,
            editorial_context: editCtx,
          })
        }
        case 'ADAPT_PLATFORM': {
          if (!content.trim()) throw new Error('Please enter text to adapt.')
          if (!platform) throw new Error('Please select a target platform.')
          return aiApi.adaptPlatform(accessToken, {
            content: content.trim(),
            platform: platform as AIPlatform,
            tone,
            editorial_context: editCtx,
          })
        }
        case 'IDEATE': {
          if (!prompt.trim()) throw new Error('Please enter a topic or industry for brainstorming.')
          return aiApi.generateIdeas(accessToken, {
            topic: prompt.trim(),
            platform: plat,
            tone,
            target_audience: audience.trim() || undefined,
            editorial_context: editCtx,
          })
        }
        default:
          throw new Error('Unsupported AI action')
      }
    },
    onSuccess: (data) => {
      setResult(data)
      // Prepend to history
      const snippet = action === 'IDEATE' || action === 'GENERATE' ? prompt : content
      const historyItem: AIHistoryItem = {
        id: `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        action,
        platform: platform ? (platform as AIPlatform) : undefined,
        tone,
        inputSnippet: snippet.slice(0, 80),
        result: data,
        timestamp: new Date().toISOString(),
      }
      setHistory((prev) => [historyItem, ...prev.slice(0, 19)])
    },
    onError: (err: any) => {
      setError(err?.message || 'AI generation failed. Please try again.')
    },
  })

  const handleCopy = useCallback((textToCopy?: string) => {
    const text = textToCopy || result?.content
    if (!text) return
    void navigator.clipboard.writeText(text).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    })
  }, [result])

  const handleUseInPostEditor = useCallback((contentToUse?: string) => {
    const text = contentToUse || result?.content
    if (!text) return
    navigate('/posts/new', { state: { content: text } })
  }, [navigate, result])

  const handleSelectHistoryItem = useCallback((item: AIHistoryItem) => {
    setAction(item.action)
    if (item.platform) setPlatform(item.platform)
    if (item.tone) setTone(item.tone)
    setResult(item.result)
  }, [])

  const handleClearHistory = useCallback(() => {
    setHistory([])
    try {
      localStorage.removeItem(HISTORY_STORAGE_KEY)
    } catch {
      // Ignored
    }
  }, [])

  return {
    action,
    setAction,
    prompt,
    setPrompt,
    content,
    setContent,
    platform,
    setPlatform,
    tone,
    setTone,
    audience,
    setAudience,
    objective,
    setObjective,
    editorialContext,
    setEditorialContext,
    showEditorialContext,
    setShowEditorialContext,
    result,
    error,
    copied,
    isLoading: aiMutation.isPending,
    history,
    generate: aiMutation.mutate,
    handleCopy,
    handleUseInPostEditor,
    handleSelectHistoryItem,
    handleClearHistory,
  }
}
