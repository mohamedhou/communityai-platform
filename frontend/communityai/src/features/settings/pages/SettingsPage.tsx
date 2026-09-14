import { useState } from 'react'

import { NotificationSettings } from '../components/NotificationSettings'
import { ProfileSettings } from '../components/ProfileSettings'
import { SecuritySettings } from '../components/SecuritySettings'
import { SettingsSidebar, type SettingsSection } from '../components/SettingsSidebar'
import { SocialSettings } from '../components/SocialSettings'
import { WorkspaceSettings } from '../components/WorkspaceSettings'
import { useChangePassword, useSettings, useUpdateSettings } from '../hooks/useSettings'
import type { UserSettingsUpdate } from '../types/settings'

export function SettingsPage() {
  const [active, setActive] = useState<SettingsSection>('profile')
  const [success, setSuccess] = useState('')
  const { data: settings, isLoading, isError, error } = useSettings()
  const updateMutation = useUpdateSettings()
  const passwordMutation = useChangePassword()
  const saveSettings = (payload: UserSettingsUpdate) => { setSuccess(''); updateMutation.mutate(payload, { onSuccess: () => setSuccess('Changes saved successfully.') }) }
  const changePassword = (payload: Parameters<typeof passwordMutation.mutate>[0]) => { setSuccess(''); passwordMutation.mutate(payload, { onSuccess: () => setSuccess('Password changed successfully.') }) }
  const mutationError = (mutation: { error: Error | null }) => mutation.error?.message

  if (isLoading) return <main className="page-shell"><div className="settings-loading">Loading settings...</div></main>
  if (isError || !settings) return <main className="page-shell"><div className="settings-error">Unable to load settings: {(error as Error)?.message ?? 'Unknown error'}</div></main>

  return <main className="page-shell settings-page"><header className="settings-page-header"><div><p className="eyebrow">Workspace control</p><h1>Settings</h1><p className="page-subtitle">Shape your CommunityAI workspace around the way you work.</p></div></header><div className="settings-layout"><SettingsSidebar active={active} onChange={(section) => { setActive(section); setSuccess('') }} /><div className="settings-content">{active === 'profile' && <ProfileSettings settings={settings} onSave={saveSettings} isSaving={updateMutation.isPending} error={mutationError(updateMutation)} success={success} />}{active === 'security' && <SecuritySettings onChangePassword={changePassword} isSaving={passwordMutation.isPending} error={mutationError(passwordMutation)} success={success} />}{active === 'workspace' && <WorkspaceSettings settings={settings} onSave={saveSettings} isSaving={updateMutation.isPending} error={mutationError(updateMutation)} success={success} />}{active === 'notifications' && <NotificationSettings settings={settings} onSave={saveSettings} isSaving={updateMutation.isPending} error={mutationError(updateMutation)} success={success} />}{active === 'social' && <SocialSettings settings={settings} />}</div></div></main>
}