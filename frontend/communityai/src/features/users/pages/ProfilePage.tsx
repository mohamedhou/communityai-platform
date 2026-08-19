import { useMutation } from '@tanstack/react-query'
import { useState, useEffect } from 'react'

import { useAuth } from '../../auth/hooks/useAuth'
import * as usersApi from '../services/usersApi'
import type { ChangePasswordRequest } from '../types/users'

export function ProfilePage() {
  const { user, accessToken, updateCurrentUser } = useAuth()

  const [firstName, setFirstName] = useState(user?.first_name ?? '')
  const [lastName, setLastName] = useState(user?.last_name ?? '')

  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')

  const [profileSuccess, setProfileSuccess] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState('')

  useEffect(() => {
    if (user) {
      setFirstName(user.first_name)
      setLastName(user.last_name)
    }
  }, [user])

  const profileMutation = useMutation({
    mutationFn: (data: { first_name: string; last_name: string }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return usersApi.updateProfile(accessToken, data)
    },
    onSuccess: (updatedUser) => {
      updateCurrentUser(updatedUser)
      setProfileSuccess('Profile updated successfully!')
      setTimeout(() => setProfileSuccess(''), 4000)
    },
  })

  const passwordMutation = useMutation({
    mutationFn: (data: ChangePasswordRequest) => {
      if (!accessToken) throw new Error('Not authenticated')
      return usersApi.changePassword(accessToken, data)
    },
    onSuccess: () => {
      setPasswordSuccess('Password changed successfully!')
      setCurrentPassword('')
      setNewPassword('')
      setTimeout(() => setPasswordSuccess(''), 4000)
    },
  })

  const onUpdateProfile = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setProfileSuccess('')
    profileMutation.mutate({ first_name: firstName, last_name: lastName })
  }

  const onChangePassword = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPasswordSuccess('')
    passwordMutation.mutate({ current_password: currentPassword, new_password: newPassword })
  }

  return (
    <main className="page-shell">
      <div className="profile-container">
        <h1>User Profile</h1>
        <p className="page-subtitle">Manage your account information and security.</p>

        <div className="profile-grid">
          {/* Profile Edit Section */}
          <section className="profile-card-section">
            <h2>Profile Details</h2>
            <form className="profile-form" onSubmit={onUpdateProfile}>
              <label>
                Email Address
                <input type="email" value={user?.email ?? ''} disabled className="disabled-input" />
              </label>

              <label>
                First Name
                <input
                  type="text"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  required
                />
              </label>

              <label>
                Last Name
                <input
                  type="text"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  required
                />
              </label>

              {profileMutation.isError ? (
                <p className="form-error">{(profileMutation.error as Error).message}</p>
              ) : null}

              {profileSuccess ? <p className="form-success">{profileSuccess}</p> : null}

              <button type="submit" disabled={profileMutation.isPending}>
                {profileMutation.isPending ? 'Saving...' : 'Save Profile'}
              </button>
            </form>
          </section>

          {/* Change Password Section */}
          <section className="profile-card-section">
            <h2>Security & Password</h2>
            <form className="profile-form" onSubmit={onChangePassword}>
              <label>
                Current Password
                <input
                  type="password"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </label>

              <label>
                New Password
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  minLength={8}
                />
              </label>

              {passwordMutation.isError ? (
                <p className="form-error">{(passwordMutation.error as Error).message}</p>
              ) : null}

              {passwordSuccess ? <p className="form-success">{passwordSuccess}</p> : null}

              <button type="submit" disabled={passwordMutation.isPending}>
                {passwordMutation.isPending ? 'Changing...' : 'Change Password'}
              </button>
            </form>
          </section>
        </div>
      </div>
    </main>
  )
}
