export type SettingsSection = 'profile' | 'security' | 'workspace' | 'notifications' | 'social'

const sections: Array<{ id: SettingsSection; label: string; icon: string }> = [
  { id: 'profile', label: 'Profile', icon: '◉' },
  { id: 'security', label: 'Security', icon: '⌑' },
  { id: 'workspace', label: 'Workspace', icon: '▦' },
  { id: 'notifications', label: 'Notifications', icon: '♧' },
  { id: 'social', label: 'Social Accounts', icon: '◎' },
]

export function SettingsSidebar({ active, onChange }: { active: SettingsSection; onChange: (section: SettingsSection) => void }) {
  return (
    <aside className="settings-sidebar" aria-label="Settings sections">
      <p className="settings-sidebar-label">Manage your space</p>
      {sections.map((section) => (
        <button key={section.id} type="button" className={active === section.id ? 'active' : ''} onClick={() => onChange(section.id)}>
          <span aria-hidden="true">{section.icon}</span>{section.label}
        </button>
      ))}
    </aside>
  )
}