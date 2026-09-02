import type { Post, PostStatus } from '../../posts/types/post'

export type CalendarViewMode = 'month' | 'week'

export type CalendarFilterStatus = 'ALL' | PostStatus

export interface CalendarDayCell {
  date: Date
  dateString: string // YYYY-MM-DD
  dayNumber: number
  isCurrentMonth: boolean
  isToday: boolean
  isPast: boolean
  posts: Post[]
}

export interface DraggedPostItem {
  post: Post
}
