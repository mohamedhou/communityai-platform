import { useState, useMemo, useCallback } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import { fetchCalendarPosts, rescheduleCalendarPost } from '../services/calendarApi'
import type { CalendarFilterStatus, CalendarViewMode, CalendarDayCell } from '../types/calendar'
import type { Post } from '../../posts/types/post'

const pad = (n: number) => n.toString().padStart(2, '0')

export function toDateKey(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export function getPostDate(post: Post): Date {
  if (post.scheduled_at) {
    return new Date(post.scheduled_at)
  }
  if (post.published_at) {
    return new Date(post.published_at)
  }
  return new Date(post.created_at)
}

export function useEditorialCalendar() {
  const { accessToken } = useAuth()
  const queryClient = useQueryClient()

  const [currentDate, setCurrentDate] = useState<Date>(() => new Date())
  const [viewMode, setViewMode] = useState<CalendarViewMode>('month')
  const [statusFilter, setStatusFilter] = useState<CalendarFilterStatus>('ALL')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  // Fetch all user posts (cached by React Query)
  const {
    data: allPosts = [],
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['posts'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return fetchCalendarPosts(accessToken)
    },
    enabled: !!accessToken,
  })

  // Status counts for filters
  const filterCounts = useMemo(() => {
    const counts: Record<CalendarFilterStatus, number> = {
      ALL: allPosts.length,
      DRAFT: 0,
      SCHEDULED: 0,
      PUBLISHING: 0,
      PUBLISHED: 0,
      FAILED: 0,
      CANCELLED: 0,
    }
    for (const p of allPosts) {
      if (counts[p.status] !== undefined) {
        counts[p.status]++
      }
    }
    return counts
  }, [allPosts])

  // Filtered posts
  const filteredPosts = useMemo(() => {
    if (statusFilter === 'ALL') return allPosts
    return allPosts.filter((p) => p.status === statusFilter)
  }, [allPosts, statusFilter])

  // Map filtered posts by date key
  const postsByDateKey = useMemo(() => {
    const map = new Map<string, Post[]>()
    for (const post of filteredPosts) {
      const date = getPostDate(post)
      const key = toDateKey(date)
      if (!map.has(key)) {
        map.set(key, [])
      }
      map.get(key)!.push(post)
    }

    // Sort posts within each date cell by time
    map.forEach((list) => {
      list.sort((a, b) => getPostDate(a).getTime() - getPostDate(b).getTime())
    })

    return map
  }, [filteredPosts])

  // Navigation handlers
  const navigatePrev = useCallback(() => {
    setCurrentDate((prev) => {
      const next = new Date(prev)
      if (viewMode === 'month') {
        next.setMonth(prev.getMonth() - 1)
      } else {
        next.setDate(prev.getDate() - 7)
      }
      return next
    })
  }, [viewMode])

  const navigateNext = useCallback(() => {
    setCurrentDate((prev) => {
      const next = new Date(prev)
      if (viewMode === 'month') {
        next.setMonth(prev.getMonth() + 1)
      } else {
        next.setDate(prev.getDate() + 7)
      }
      return next
    })
  }, [viewMode])

  const goToToday = useCallback(() => {
    setCurrentDate(new Date())
  }, [])

  // Header Title
  const headerTitle = useMemo(() => {
    if (viewMode === 'month') {
      return currentDate.toLocaleDateString(undefined, {
        month: 'long',
        year: 'numeric',
      })
    }
    // Week title
    const curr = new Date(currentDate)
    const dayOfWeek = (curr.getDay() + 6) % 7 // Monday = 0
    const monday = new Date(curr)
    monday.setDate(curr.getDate() - dayOfWeek)
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)

    const monMonth = monday.toLocaleDateString(undefined, { month: 'short' })
    const sunMonth = sunday.toLocaleDateString(undefined, { month: 'short' })
    const year = sunday.getFullYear()

    if (monMonth === sunMonth) {
      return `${monday.getDate()} – ${sunday.getDate()} ${sunMonth} ${year}`
    }
    return `${monday.getDate()} ${monMonth} – ${sunday.getDate()} ${sunMonth} ${year}`
  }, [currentDate, viewMode])

  // Calculate cells for Month view
  const monthCells = useMemo<CalendarDayCell[]>(() => {
    const year = currentDate.getFullYear()
    const month = currentDate.getMonth()
    const todayKey = toDateKey(new Date())
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    const firstDayOfMonth = new Date(year, month, 1)
    const lastDayOfMonth = new Date(year, month + 1, 0)

    // Monday start: 0 = Mon, 6 = Sun
    const startDayOfWeek = (firstDayOfMonth.getDay() + 6) % 7
    const daysInMonth = lastDayOfMonth.getDate()

    const cells: CalendarDayCell[] = []

    // 1. Previous month padding
    const prevMonthLastDay = new Date(year, month, 0).getDate()
    for (let i = startDayOfWeek - 1; i >= 0; i--) {
      const d = new Date(year, month - 1, prevMonthLastDay - i)
      const key = toDateKey(d)
      d.setHours(0, 0, 0, 0)
      cells.push({
        date: d,
        dateString: key,
        dayNumber: d.getDate(),
        isCurrentMonth: false,
        isToday: key === todayKey,
        isPast: d < today,
        posts: postsByDateKey.get(key) || [],
      })
    }

    // 2. Current month days
    for (let day = 1; day <= daysInMonth; day++) {
      const d = new Date(year, month, day)
      const key = toDateKey(d)
      d.setHours(0, 0, 0, 0)
      cells.push({
        date: d,
        dateString: key,
        dayNumber: day,
        isCurrentMonth: true,
        isToday: key === todayKey,
        isPast: d < today,
        posts: postsByDateKey.get(key) || [],
      })
    }

    // 3. Next month padding to make full 7-day rows (up to 35 or 42 cells)
    const totalCells = cells.length <= 35 ? 35 : 42
    const remaining = totalCells - cells.length
    for (let day = 1; day <= remaining; day++) {
      const d = new Date(year, month + 1, day)
      const key = toDateKey(d)
      d.setHours(0, 0, 0, 0)
      cells.push({
        date: d,
        dateString: key,
        dayNumber: day,
        isCurrentMonth: false,
        isToday: key === todayKey,
        isPast: d < today,
        posts: postsByDateKey.get(key) || [],
      })
    }

    return cells
  }, [currentDate, postsByDateKey])

  // Calculate cells for Week view
  const weekCells = useMemo<CalendarDayCell[]>(() => {
    const curr = new Date(currentDate)
    const dayOfWeek = (curr.getDay() + 6) % 7 // Monday = 0
    const monday = new Date(curr)
    monday.setDate(curr.getDate() - dayOfWeek)

    const todayKey = toDateKey(new Date())
    const today = new Date()
    today.setHours(0, 0, 0, 0)

    const cells: CalendarDayCell[] = []
    for (let i = 0; i < 7; i++) {
      const d = new Date(monday)
      d.setDate(monday.getDate() + i)
      const key = toDateKey(d)
      const isCurrentMonth = d.getMonth() === currentDate.getMonth()
      d.setHours(0, 0, 0, 0)
      cells.push({
        date: d,
        dateString: key,
        dayNumber: d.getDate(),
        isCurrentMonth,
        isToday: key === todayKey,
        isPast: d < today,
        posts: postsByDateKey.get(key) || [],
      })
    }
    return cells
  }, [currentDate, postsByDateKey])

  // Drag & drop mutation with optimistic update and rollback
  const rescheduleMutation = useMutation({
    mutationFn: async ({
      postId,
      targetIsoDate,
    }: {
      postId: number
      targetIsoDate: string
    }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return rescheduleCalendarPost(accessToken, postId, targetIsoDate)
    },
    onMutate: async ({ postId, targetIsoDate }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['posts'] })
      // Snapshot previous posts
      const previousPosts = queryClient.getQueryData<Post[]>(['posts'])

      // Optimistically update
      if (previousPosts) {
        queryClient.setQueryData<Post[]>(
          ['posts'],
          previousPosts.map((p) =>
            p.id === postId
              ? { ...p, scheduled_at: targetIsoDate, status: 'SCHEDULED' }
              : p
          )
        )
      }

      return { previousPosts }
    },
    onError: (err: any, _variables, context) => {
      // Rollback to snapshot
      if (context?.previousPosts) {
        queryClient.setQueryData(['posts'], context.previousPosts)
      }
      setErrorMessage(err?.message || 'Failed to move scheduled post. Reverted.')
      setTimeout(() => setErrorMessage(null), 5000)
    },
    onSuccess: (updatedPost) => {
      // Invalidate to guarantee fresh server state
      void queryClient.invalidateQueries({ queryKey: ['posts'] })
      const dateStr = new Date(updatedPost.scheduled_at!).toLocaleString()
      setSuccessMessage(`Post successfully rescheduled to ${dateStr}`)
      setTimeout(() => setSuccessMessage(null), 4000)
    },
  })

  // Handle Drop onto a day cell
  const handleDropPost = useCallback(
    (post: Post, targetDate: Date) => {
      // Only SCHEDULED posts can be dragged
      if (post.status !== 'SCHEDULED') {
        setErrorMessage(`Only SCHEDULED posts can be moved. Post is ${post.status}.`)
        setTimeout(() => setErrorMessage(null), 4000)
        return
      }

      // Preserve original hour and minute if post had a scheduled_at, else default to 10:00
      let hours = 10
      let minutes = 0
      if (post.scheduled_at) {
        const orig = new Date(post.scheduled_at)
        hours = orig.getHours()
        minutes = orig.getMinutes()
      }

      const newScheduledDate = new Date(targetDate)
      newScheduledDate.setHours(hours, minutes, 0, 0)

      // Ensure the new date and time is strictly in the future
      if (newScheduledDate.getTime() <= Date.now()) {
        setErrorMessage('Cannot move a post to a past date/time. Please select a future date.')
        setTimeout(() => setErrorMessage(null), 5000)
        return
      }

      rescheduleMutation.mutate({
        postId: post.id,
        targetIsoDate: newScheduledDate.toISOString(),
      })
    },
    [rescheduleMutation]
  )

  return {
    currentDate,
    viewMode,
    setViewMode,
    statusFilter,
    setStatusFilter,
    filterCounts,
    headerTitle,
    monthCells,
    weekCells,
    isLoading,
    isError,
    error,
    errorMessage,
    successMessage,
    navigatePrev,
    navigateNext,
    goToToday,
    handleDropPost,
    isMoving: rescheduleMutation.isPending,
  }
}
