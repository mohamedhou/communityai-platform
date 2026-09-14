import { useEffect, useState } from 'react'

import type { UserSettings, UserSettingsUpdate } from '../types/settings'
import { SaveState, SettingsSection } from './ProfileSettings'

export function WorkspaceSettings({ settings, onSave, isSaving, error, success }: { settings: UserSettings; onSave: (payload: UserSettingsUpdate) => void; isSaving: boolean; error?: string; success: string }) {
  const [form, setForm] = useState({ workspace_name: settings.workspace_name, workspace_description: settings.workspace_description ?? '', timezone: settings.timezone, language: settings.language, default_platform: settings.default_platform ?? '' })
  useEffect(() => { setForm({ workspace_name: settings.workspace_name, workspace_description: settings.workspace_description ?? '', timezone: settings.timezone, language: settings.language, default_platform: settings.default_platform ?? '' }) }, [settings])
  const update = (key: keyof typeof form, value: string) => setForm((current) => ({ ...current, [key]: value }))
  return <SettingsSection title="Workspace" description="Set the defaults for your CommunityAI workspace.">
    <form className="settings-form" onSubmit={(event) => { event.preventDefault(); onSave({ ...form, default_platform: form.default_platform || null }) }}>
      <label>Workspace name<input value={form.workspace_name} onChange={(event) => update('workspace_name', event.target.value)} maxLength={150} required /></label>
      <label>Description<textarea value={form.workspace_description} onChange={(event) => update('workspace_description', event.target.value)} maxLength={500} rows={4} /></label>
      <div className="settings-form-grid"><label>Timezone<input value={form.timezone} onChange={(event) => update('timezone', event.target.value)} placeholder="Europe/Paris" required /></label><label>Language<select value={form.language} onChange={(event) => update('language', event.target.value)}><option value="en">English</option><option value="fr">Français</option></select></label></div>
      <label>Default platform<select value={form.default_platform} onChange={(event) => update('default_platform', event.target.value)}><option value="">No default</option><option value="meta">Meta</option><option value="facebook">Facebook</option><option value="instagram">Instagram</option><option value="linkedin">LinkedIn</option></select></label>
      <SaveState isSaving={isSaving} error={error} success={success} /><button className="settings-save-button" type="submit" disabled={isSaving}>{isSaving ? 'Saving...' : 'Save workspace'}</button>
    </form>
  </SettingsSection>
}