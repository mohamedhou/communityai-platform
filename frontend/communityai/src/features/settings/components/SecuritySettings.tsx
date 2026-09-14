import { useState } from 'react'

import { SettingsSection, SaveState } from './ProfileSettings'
import type { ChangePasswordRequest } from '../types/settings'

export function SecuritySettings({ onChangePassword, isSaving, error, success }: { onChangePassword: (payload: ChangePasswordRequest) => void; isSaving: boolean; error?: string; success: string }) {
  const [form, setForm] = useState<ChangePasswordRequest>({ current_password: '', new_password: '', confirm_password: '' })
  const update = (key: keyof ChangePasswordRequest, value: string) => setForm((current) => ({ ...current, [key]: value }))
  return <SettingsSection title="Security" description="Change your password and protect your account.">
    <form className="settings-form" onSubmit={(event) => { event.preventDefault(); onChangePassword(form) }}>
      <label>Current password<input type="password" value={form.current_password} onChange={(event) => update('current_password', event.target.value)} minLength={8} required /></label>
      <label>New password<input type="password" value={form.new_password} onChange={(event) => update('new_password', event.target.value)} minLength={8} required /></label>
      <label>Confirm new password<input type="password" value={form.confirm_password} onChange={(event) => update('confirm_password', event.target.value)} minLength={8} required /></label>
      <SaveState isSaving={isSaving} error={error} success={success} />
      <button className="settings-save-button" type="submit" disabled={isSaving}>{isSaving ? 'Changing...' : 'Change password'}</button>
    </form>
  </SettingsSection>
}