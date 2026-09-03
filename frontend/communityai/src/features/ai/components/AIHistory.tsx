import type { AIHistoryItem } from '../types/ai'

interface AIHistoryProps {
  history: AIHistoryItem[]
  onSelect: (item: AIHistoryItem) => void
  onClear: () => void
  onUseInEditor: (content: string) => void
}

export function AIHistory({
  history,
  onSelect,
  onClear,
  onUseInEditor,
}: AIHistoryProps) {
  if (history.length === 0) {
    return null
  }

  return (
    <div className="ai-history-panel">
      <div className="ai-history-header">
        <h4 className="ai-history-title">🕒 Recent AI Generations</h4>
        <button
          type="button"
          onClick={onClear}
          className="ai-history-clear-btn"
          title="Clear local history"
        >
          Clear History
        </button>
      </div>

      <div className="ai-history-list">
        {history.map((item) => {
          const timeFormatted = new Date(item.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })

          return (
            <div
              key={item.id}
              className="ai-history-card"
              onClick={() => onSelect(item)}
              role="button"
              tabIndex={0}
            >
              <div className="ai-history-card-top">
                <span className="ai-history-action">{item.action}</span>
                {item.platform && (
                  <span className="ai-history-platform">{item.platform}</span>
                )}
                <span className="ai-history-time">{timeFormatted}</span>
              </div>

              <p className="ai-history-snippet">
                {item.result.content.slice(0, 100)}...
              </p>

              <div className="ai-history-actions">
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onUseInEditor(item.result.content)
                  }}
                  className="ai-history-use-btn"
                >
                  Use in Editor
                </button>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
