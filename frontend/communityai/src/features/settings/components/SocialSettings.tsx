import { Link } from 'react-router-dom'

import { SettingsSection } from './ProfileSettings'
import type { UserSettings } from '../types/settings'

export function SocialSettings({ settings }: { settings: UserSettings }) {
  return <SettingsSection title="Social Accounts" description="Manage connected publishing accounts in one dedicated place.">
    <div className="settings-social-summary"><span className="settings-social-count">{settings.connected_account_count}</span><div><strong>Connected accounts</strong><p>OAuth credentials stay protected and are never shown here.</p></div></div>
    <Link className="settings-link-button" to="/social-accounts">Open Social Accounts <span aria-hidden="true">→</span></Link>
  </SettingsSection>
}