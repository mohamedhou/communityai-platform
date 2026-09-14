import { useEffect, useState } from 'react'

import type { UserSettings, UserSettingsUpdate } from '../types/settings'

export function ProfileSettings({ settings, onSave, isSaving, error, success }: { settings: UserSettings; onSave: (payload: UserSettingsUpdate) => void; isSaving: boolean; error?: string; success: string }) {
  const [firstName, setFirstName] = useState(settings.first_name)
  const [lastName, setLastName] = useState(settings.last_name)
  useEffect(() => { setFirstName(settings.first_name); setLastName(settings.last_name) }, [settings.first_name, settings.last_name])
  return (
    <SettingsSection title="Profile" description="Keep your personal account details up to date.">
      <form className="settings-form" onSubmit={(event) => { event.preventDefault(); onSave({ first_name: firstName.trim(), last_name: lastName.trim() }) }}>
        <label>Email<input type="email" value={settings.email} disabled /></label>
        <div className="settings-form-grid"><label>First name<input value={firstName} onChange={(event) => setFirstName(event.target.value)} required maxLength={100} /></label><label>Last name<input value={lastName} onChange={(event) => setLastName(event.target.value)} required maxLength={100} /></label></div>
        <label>Role<input value={settings.role} disabled /></label>
        <SaveState isSaving={isSaving} error={error} success={success} />
        <button className="settings-save-button" type="submit" disabled={isSaving}>{isSaving ? 'Saving...' : 'Save profile'}</button>
      </form>
    </SettingsSection>
  )
}

export function SettingsSection({ title, description, children }: { title: string; description: string; children: React.ReactNode }) {
  return <section className="settings-card"><div className="settings-card-heading"><h2>{title}</h2><p>{description}</p></div>{children}</section>
}

export function SaveState({ isSaving, error, success }: { isSaving: boolean; error?: string; success: string }) {
  return <>{error && <p className="form-error">{error}</p>}{success && <p className="form-success">{success}</p>}{isSaving && <span className="settings-status">Saving changes...</span>}</>
}