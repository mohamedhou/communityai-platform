import { useState, useCallback, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'

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

  // New Generation Controls
  const [language, setLanguage] = useState('fr')
  const [length, setLength] = useState<'short' | 'medium' | 'long' | ''>('')
  const [includeHashtags, setIncludeHashtags] = useState<boolean>(true)
  const [includeCta, setIncludeCta] = useState<boolean>(true)

  // Result & UI State
  const [result, setResult] = useState<AIResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Provider Status Query
  const {
    data: providerStatus,
    isLoading: isStatusLoading,
    refetch: refetchStatus,
  } = useQuery({
    queryKey: ['ai-provider-status'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return aiApi.getAIStatus(accessToken)
    },
    enabled: !!accessToken,
    refetchInterval: 30000,
  })

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
      const lenVal = length || undefined

      switch (action) {
        case 'GENERATE': {
          if (!prompt.trim()) throw new Error('Veuillez saisir un sujet ou une instruction.')
          return aiApi.generatePost(accessToken, {
            prompt: prompt.trim(),
            platform: plat,
            tone,
            audience: audience.trim() || undefined,
            objective: objective.trim() || undefined,
            editorial_context: editCtx,
            language,
            length: lenVal,
            include_hashtags: includeHashtags,
            include_cta: includeCta,
          })
        }
        case 'REWRITE': {
          if (!content.trim()) throw new Error('Veuillez saisir le texte à réécrire.')
          return aiApi.rewriteContent(accessToken, {
            content: content.trim(),
            tone,
            platform: plat,
            editorial_context: editCtx,
            language,
            include_hashtags: includeHashtags,
            include_cta: includeCta,
          })
        }
        case 'IMPROVE': {
          if (!content.trim()) throw new Error('Veuillez saisir le texte à améliorer.')
          return aiApi.improveContent(accessToken, {
            content: content.trim(),
            platform: plat,
            editorial_context: editCtx,
            language,
            include_hashtags: includeHashtags,
            include_cta: includeCta,
          })
        }
        case 'SHORTEN': {
          if (!content.trim()) throw new Error('Veuillez saisir le texte à raccourcir.')
          return aiApi.shortenContent(accessToken, {
            content: content.trim(),
            platform: plat,
            editorial_context: editCtx,
            language,
          })
        }
        case 'EXPAND': {
          if (!content.trim()) throw new Error('Veuillez saisir le texte à développer.')
          return aiApi.expandContent(accessToken, {
            content: content.trim(),
            platform: plat,
            editorial_context: editCtx,
            language,
            include_hashtags: includeHashtags,
            include_cta: includeCta,
          })
        }
        case 'CHANGE_TONE': {
          if (!content.trim()) throw new Error('Veuillez saisir le texte dont vous souhaitez changer le ton.')
          return aiApi.changeTone(accessToken, {
            content: content.trim(),
            tone,
            platform: plat,
            editorial_context: editCtx,
            language,
          })
        }
        case 'ADAPT_PLATFORM': {
          if (!content.trim()) throw new Error('Veuillez saisir le texte à adapter.')
          if (!platform) throw new Error('Veuillez sélectionner un réseau social cible.')
          return aiApi.adaptPlatform(accessToken, {
            content: content.trim(),
            platform: platform as AIPlatform,
            tone,
            editorial_context: editCtx,
            language,
            include_hashtags: includeHashtags,
            include_cta: includeCta,
          })
        }
        case 'IDEATE': {
          if (!prompt.trim()) throw new Error('Veuillez entrer un sujet pour générer des idées.')
          return aiApi.generateIdeas(accessToken, {
            topic: prompt.trim(),
            platform: plat,
            tone,
            target_audience: audience.trim() || undefined,
            editorial_context: editCtx,
            language,
          })
        }
        default:
          throw new Error('Action IA non supportée')
      }
    },
    onSuccess: (data) => {
      setResult(data)
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
      setError(err?.message || 'La génération IA a échoué. Veuillez réessayer.')
    },
  })

  const updateResultContent = useCallback((newContent: string) => {
    setResult((prev) => (prev ? { ...prev, content: newContent } : null))
  }, [])

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
    language,
    setLanguage,
    length,
    setLength,
    includeHashtags,
    setIncludeHashtags,
    includeCta,
    setIncludeCta,
    result,
    updateResultContent,
    error,
    copied,
    isLoading: aiMutation.isPending,
    providerStatus,
    isStatusLoading,
    refetchStatus,
    history,
    generate: aiMutation.mutate,
    handleCopy,
    handleUseInPostEditor,
    handleSelectHistoryItem,
    handleClearHistory,
  }
}
