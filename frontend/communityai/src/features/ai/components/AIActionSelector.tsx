import type { AIAction } from '../types/ai'

interface AIActionSelectorProps {
  currentAction: AIAction
  onSelectAction: (action: AIAction) => void
  disabled?: boolean
}

const ACTIONS: { key: AIAction; label: string; icon: string; description: string }[] = [
  { key: 'GENERATE', label: 'Generate', icon: '✨', description: 'Create a post from a topic or idea' },
  { key: 'REWRITE', label: 'Rewrite', icon: '🔄', description: 'Rephrase text with fresh wording' },
  { key: 'IMPROVE', label: 'Improve', icon: '⚡', description: 'Enhance clarity, hook & engagement' },
  { key: 'SHORTEN', label: 'Shorten', icon: '✂️', description: 'Make copy concise & punchy' },
  { key: 'EXPAND', label: 'Expand', icon: '📖', description: 'Elaborate with details & structure' },
  { key: 'CHANGE_TONE', label: 'Change Tone', icon: '🎭', description: 'Switch to a specific brand voice' },
  { key: 'ADAPT_PLATFORM', label: 'Adapt Platform', icon: '🌐', description: 'Tailor for LinkedIn, IG or FB' },
  { key: 'IDEATE', label: 'Ideas', icon: '💡', description: 'Brainstorm 4-5 publication concepts' },
]

export function AIActionSelector({
  currentAction,
  onSelectAction,
  disabled = false,
}: AIActionSelectorProps) {
  return (
    <div className="ai-actions-bar">
      <div className="ai-actions-grid">
        {ACTIONS.map(({ key, label, icon }) => {
          const isActive = currentAction === key
          return (
            <button
              key={key}
              type="button"
              disabled={disabled}
              onClick={() => onSelectAction(key)}
              className={`ai-action-btn ${isActive ? 'active' : ''}`}
            >
              <span className="ai-action-icon">{icon}</span>
              <span className="ai-action-label">{label}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
