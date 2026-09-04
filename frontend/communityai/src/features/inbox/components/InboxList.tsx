import type { InboxMessage } from '../types/inbox'
import { InboxEmptyState } from './InboxEmptyState'
import { InboxItem } from './InboxItem'

interface InboxListProps {
  messages: InboxMessage[]
  total: number
  selectedMessage: InboxMessage | null
  onSelectMessage: (message: InboxMessage) => void
  isLoading: boolean
  hasFilters: boolean
  onResetFilters: () => void
  onSeedMock?: () => void
  isSeeding?: boolean
}

export function InboxList({
  messages,
  total,
  selectedMessage,
  onSelectMessage,
  isLoading,
  hasFilters,
  onResetFilters,
  onSeedMock,
  isSeeding,
}: InboxListProps) {
  if (isLoading) {
    return (
      <div className="inbox-list-loading">
        <div className="spinner-medium" />
        <p>Chargement des interactions...</p>
      </div>
    )
  }

  if (messages.length === 0) {
    return (
      <InboxEmptyState
        hasFilters={hasFilters}
        onResetFilters={onResetFilters}
        onSeedMock={onSeedMock}
        isSeeding={isSeeding}
      />
    )
  }

  return (
    <div className="inbox-list-container">
      <div className="inbox-list-header">
        <span className="inbox-list-count">
          {total} interaction{total > 1 ? 's' : ''}
        </span>
      </div>

      <div className="inbox-items-scroll">
        {messages.map((message) => (
          <InboxItem
            key={message.id}
            message={message}
            isSelected={selectedMessage?.id === message.id}
            onSelect={onSelectMessage}
          />
        ))}
      </div>
    </div>
  )
}
