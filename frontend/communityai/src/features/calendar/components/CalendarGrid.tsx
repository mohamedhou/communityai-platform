import React, { useState } from 'react'
import { CalendarEvent } from './CalendarEvent'
import type { CalendarDayCell, CalendarViewMode } from '../types/calendar'
import type { Post } from '../../posts/types/post'
import type { SocialAccount } from '../../social-accounts/types/social'

interface CalendarGridProps {
  viewMode: CalendarViewMode
  monthCells: CalendarDayCell[]
  weekCells: CalendarDayCell[]
  socialAccounts?: SocialAccount[]
  onDropPost: (post: Post, targetDate: Date) => void
}

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function CalendarGrid({
  viewMode,
  monthCells,
  weekCells,
  socialAccounts = [],
  onDropPost,
}: CalendarGridProps) {
  const [dragOverDateKey, setDragOverDateKey] = useState<string | null>(null)

  const handleDragOver = (e: React.DragEvent, cell: CalendarDayCell) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
    if (dragOverDateKey !== cell.dateString) {
      setDragOverDateKey(cell.dateString)
    }
  }

  const handleDragLeave = (e: React.DragEvent, cell: CalendarDayCell) => {
    // Only clear if leaving the cell itself
    if (e.currentTarget.contains(e.relatedTarget as Node)) {
      return
    }
    if (dragOverDateKey === cell.dateString) {
      setDragOverDateKey(null)
    }
  }

  const handleDrop = (e: React.DragEvent, cell: CalendarDayCell) => {
    e.preventDefault()
    setDragOverDateKey(null)
    try {
      const dataStr = e.dataTransfer.getData('application/json')
      if (!dataStr) return
      const post = JSON.parse(dataStr) as Post
      onDropPost(post, cell.date)
    } catch {
      // Invalid drag data ignored
    }
  }

  if (viewMode === 'week') {
    return (
      <div className="calendar-week-container">
        <div className="calendar-week-grid">
          {weekCells.map((cell) => {
            const isDragTarget = dragOverDateKey === cell.dateString
            const dayName = cell.date.toLocaleDateString(undefined, { weekday: 'short' })
            const formattedDate = cell.date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })

            return (
              <div
                key={cell.dateString}
                className={`calendar-week-column ${cell.isToday ? 'is-today' : ''} ${isDragTarget ? 'drag-over' : ''}`}
                onDragOver={(e) => handleDragOver(e, cell)}
                onDragLeave={(e) => handleDragLeave(e, cell)}
                onDrop={(e) => handleDrop(e, cell)}
              >
                <div className="calendar-week-column-header">
                  <span className="calendar-week-dayname">{dayName}</span>
                  <span className={`calendar-week-daynum ${cell.isToday ? 'today-pill' : ''}`}>
                    {formattedDate}
                  </span>
                </div>

                <div className="calendar-week-events-list">
                  {cell.posts.length > 0 ? (
                    cell.posts.map((post) => (
                      <CalendarEvent
                        key={post.id}
                        post={post}
                        socialAccounts={socialAccounts}
                      />
                    ))
                  ) : (
                    <div className="calendar-empty-slot">
                      <span>No posts</span>
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    )
  }

  // Month View
  return (
    <div className="calendar-month-container">
      {/* Weekday headers */}
      <div className="calendar-weekdays-header">
        {WEEKDAYS.map((day) => (
          <div key={day} className="calendar-weekday-cell">
            {day}
          </div>
        ))}
      </div>

      {/* Grid of days */}
      <div className="calendar-month-grid">
        {monthCells.map((cell) => {
          const isDragTarget = dragOverDateKey === cell.dateString

          return (
            <div
              key={cell.dateString}
              className={`calendar-day-cell ${cell.isCurrentMonth ? 'in-month' : 'out-month'} ${
                cell.isToday ? 'is-today' : ''
              } ${isDragTarget ? 'drag-over' : ''}`}
              onDragOver={(e) => handleDragOver(e, cell)}
              onDragLeave={(e) => handleDragLeave(e, cell)}
              onDrop={(e) => handleDrop(e, cell)}
            >
              <div className="calendar-day-cell-top">
                <span className={`calendar-day-number ${cell.isToday ? 'today-indicator' : ''}`}>
                  {cell.dayNumber}
                </span>
                {cell.posts.length > 0 && (
                  <span className="calendar-cell-badge">
                    {cell.posts.length} {cell.posts.length === 1 ? 'post' : 'posts'}
                  </span>
                )}
              </div>

              <div className="calendar-cell-events">
                {cell.posts.map((post) => (
                  <CalendarEvent
                    key={post.id}
                    post={post}
                    socialAccounts={socialAccounts}
                  />
                ))}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
