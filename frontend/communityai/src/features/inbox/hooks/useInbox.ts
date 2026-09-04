import { useState, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import {
  getInboxMessages,
  getInboxUnreadCount,
  markInboxMessageRead,
  markInboxMessageResolved,
  seedMockInboxMessages,
  sendInboxReply,
  suggestInboxReply,
} from '../services/inboxApi'
import type { InboxFiltersState, InboxMessage, InboxSuggestReplyRequest } from '../types/inbox'

export function useInbox() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()

  const [filters, setFilters] = useState<InboxFiltersState>({
    type: 'ALL',
    platform: 'ALL',
    sentiment: 'ALL',
    status: 'ALL',
    search: '',
  })
  const [selectedMessageId, setSelectedMessageId] = useState<number | null>(null)

  // Query: messages list
  const {
    data: inboxData,
    isLoading: isLoadingMessages,
    isError,
    error,
    refetch: refetchMessages,
  } = useQuery({
    queryKey: ['inbox-messages', filters],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getInboxMessages(accessToken, filters)
    },
    enabled: !!accessToken,
  })

  // Query: unread count
  const { data: unreadData } = useQuery({
    queryKey: ['inbox-unread-count'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return getInboxUnreadCount(accessToken)
    },
    enabled: !!accessToken,
  })

  const messages = inboxData?.items || []
  const total = inboxData?.total || 0
  const unreadCount = unreadData?.unread_count ?? inboxData?.unread_count ?? 0

  // Derive selected message from items list
  const selectedMessage =
    messages.find((m) => m.id === selectedMessageId) ||
    (messages.length > 0 && selectedMessageId === null ? messages[0] : null)

  const selectMessage = useCallback(
    async (message: InboxMessage) => {
      setSelectedMessageId(message.id)
      // If unread, auto mark as read on open
      if (!message.is_read && accessToken) {
        try {
          await markInboxMessageRead(accessToken, message.id, true)
          queryClient.invalidateQueries({ queryKey: ['inbox-messages'] })
          queryClient.invalidateQueries({ queryKey: ['inbox-unread-count'] })
        } catch {
          // Ignore background read error
        }
      }
    },
    [accessToken, queryClient],
  )

  // Mutation: Mark Read / Unread
  const toggleReadMutation = useMutation({
    mutationFn: async ({ messageId, currentRead }: { messageId: number; currentRead: boolean }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return markInboxMessageRead(accessToken, messageId, !currentRead)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox-messages'] })
      queryClient.invalidateQueries({ queryKey: ['inbox-unread-count'] })
    },
  })

  // Mutation: Mark Resolved / Open
  const toggleResolvedMutation = useMutation({
    mutationFn: async ({ messageId, currentResolved }: { messageId: number; currentResolved: boolean }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return markInboxMessageResolved(accessToken, messageId, !currentResolved)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox-messages'] })
    },
  })

  // Mutation: Suggest Reply
  const suggestReplyMutation = useMutation({
    mutationFn: async ({
      messageId,
      payload,
    }: {
      messageId: number
      payload?: InboxSuggestReplyRequest
    }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return suggestInboxReply(accessToken, messageId, payload)
    },
  })

  // Mutation: Send Reply
  const sendReplyMutation = useMutation({
    mutationFn: async ({ messageId, content }: { messageId: number; content: string }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return sendInboxReply(accessToken, messageId, content)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inbox-messages'] })
      queryClient.invalidateQueries({ queryKey: ['inbox-unread-count'] })
    },
  })

  // Mutation: Seed Mock
  const seedMockMutation = useMutation({
    mutationFn: async () => {
      if (!accessToken) throw new Error('Not authenticated')
      return seedMockInboxMessages(accessToken)
    },
    onSuccess: (seeded) => {
      queryClient.invalidateQueries({ queryKey: ['inbox-messages'] })
      queryClient.invalidateQueries({ queryKey: ['inbox-unread-count'] })
      if (seeded.length > 0) {
        setSelectedMessageId(seeded[0].id)
      }
    },
  })

  const resetFilters = useCallback(() => {
    setFilters({
      type: 'ALL',
      platform: 'ALL',
      sentiment: 'ALL',
      status: 'ALL',
      search: '',
    })
  }, [])

  const hasActiveFilters = Boolean(
    (filters.type && filters.type !== 'ALL') ||
      (filters.platform && filters.platform !== 'ALL') ||
      (filters.sentiment && filters.sentiment !== 'ALL') ||
      (filters.status && filters.status !== 'ALL') ||
      (filters.search && filters.search.trim().length > 0),
  )

  return {
    filters,
    setFilters,
    hasActiveFilters,
    resetFilters,
    messages,
    total,
    unreadCount,
    selectedMessage,
    selectMessage,
    isLoading: isLoadingMessages,
    isError,
    error,
    refetchMessages,
    toggleRead: (messageId: number, currentRead: boolean) =>
      toggleReadMutation.mutateAsync({ messageId, currentRead }),
    toggleResolved: (messageId: number, currentResolved: boolean) =>
      toggleResolvedMutation.mutateAsync({ messageId, currentResolved }),
    suggestReply: async (messageId: number, tone: string, instructions?: string) => {
      const res = await suggestReplyMutation.mutateAsync({
        messageId,
        payload: { tone, instructions },
      })
      return res.content
    },
    sendReply: (messageId: number, content: string) =>
      sendReplyMutation.mutateAsync({ messageId, content }),
    seedMock: () => seedMockMutation.mutateAsync(),
    isSuggesting: suggestReplyMutation.isPending,
    isSending: sendReplyMutation.isPending,
    isSeeding: seedMockMutation.isPending,
  }
}
