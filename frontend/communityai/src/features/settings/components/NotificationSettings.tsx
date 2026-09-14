import { useEffect, useState } from 'react'

import type { UserSettings, UserSettingsUpdate } from '../types/settings'
import { SaveState, SettingsSection } from './ProfileSettings'

const options: Array<{ key: keyof UserSettingsUpdate; label: string }> = [
  { key: 'notifications_enabled', label: 'In-app notifications' },
  { key: 'post_notifications_enabled', label: 'Post publishing updates' },
  { key: 'inbox_notifications_enabled', label: 'Inbox interactions' },
  { key: 'social_notifications_enabled', label: 'Social account alerts' },
  { key: 'analytics_notifications_enabled', label: 'Analytics alerts' },
]

export function NotificationSettings({ settings, onSave, isSaving, error, success }: { settings: UserSettings; onSave: (payload: UserSettingsUpdate) => void; isSaving: boolean; error?: string; success: string }) {
  const [form, setForm] = useState<UserSettingsUpdate>({})
  useEffect(() => { setForm(Object.fromEntries(options.map(({ key }) => [key, settings[key as keyof UserSettings] as boolean])) as UserSettingsUpdate) }, [settings])
  return <SettingsSection title="Notifications" description="Choose which activity deserves your attention.">
    <form className="settings-form" onSubmit={(event) => { event.preventDefault(); onSave(form) }}>
      <div className="settings-toggle-list">{options.map(({ key, label }) => <label className="settings-toggle" key={key}><span><strong>{label}</strong><small>{key === 'notifications_enabled' ? 'Master switch for the notification center.' : 'Receive this category in the app.'}</small></span><input type="checkbox" checked={Boolean(form[key])} onChange={(event) => setForm((current) => ({ ...current, [key]: event.target.checked }))} /></label>)}</div>
      <SaveState isSaving={isSaving} error={error} success={success} /><button className="settings-save-button" type="submit" disabled={isSaving}>{isSaving ? 'Saving...' : 'Save notifications'}</button>
    </form>
  </SettingsSection>
}