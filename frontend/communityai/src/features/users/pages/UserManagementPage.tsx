import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { useAuth } from '../../auth/hooks/useAuth'
import type { UserRole } from '../../auth/types/auth'
import * as usersApi from '../services/usersApi'

export function UserManagementPage() {
  const { user: currentUser, accessToken } = useAuth()
  const queryClient = useQueryClient()

  // Fetch all users
  const { data: users, isLoading, error } = useQuery({
    queryKey: ['users'],
    queryFn: () => {
      if (!accessToken) throw new Error('Not authenticated')
      return usersApi.getUsers(accessToken)
    },
    enabled: !!accessToken,
  })

  // Mutation to toggle status
  const statusMutation = useMutation({
    mutationFn: (data: { userId: number; isActive: boolean }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return usersApi.updateUserStatus(accessToken, data.userId, data.isActive)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  // Mutation to update role
  const roleMutation = useMutation({
    mutationFn: (data: { userId: number; role: UserRole }) => {
      if (!accessToken) throw new Error('Not authenticated')
      return usersApi.updateUserRole(accessToken, data.userId, data.role)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['users'] })
    },
  })

  if (isLoading) {
    return <div className="users-loading">Loading users...</div>
  }

  if (error) {
    return <div className="users-error">Error loading users: {(error as Error).message}</div>
  }

  const handleStatusToggle = (userId: number, currentStatus: boolean) => {
    if (userId === currentUser?.id) {
      alert('You cannot deactivate yourself!')
      return
    }
    statusMutation.mutate({ userId, isActive: !currentStatus })
  }

  const handleRoleChange = (userId: number, role: UserRole) => {
    if (userId === currentUser?.id) {
      alert('You cannot change your own role!')
      return
    }
    roleMutation.mutate({ userId, role })
  }

  return (
    <main className="page-shell">
      <div className="management-container">
        <h1>User Management</h1>
        <p className="page-subtitle">Manage system users, activate/deactivate accounts, and edit roles.</p>

        <div className="users-table-card">
          <table className="users-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {users?.map((user) => {
                const isSelf = user.id === currentUser?.id

                return (
                  <tr key={user.id} className={isSelf ? 'user-row-self' : ''}>
                    <td>{user.id}</td>
                    <td>
                      {user.first_name} {user.last_name} {isSelf && <span className="self-badge">(You)</span>}
                    </td>
                    <td>{user.email}</td>
                    <td>
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.id, e.target.value as UserRole)}
                        disabled={isSelf || roleMutation.isPending}
                        className="role-select"
                      >
                        <option value="ADMIN">ADMIN</option>
                        <option value="COMMUNITY_MANAGER">COMMUNITY_MANAGER</option>
                        <option value="CLIENT">CLIENT</option>
                      </select>
                    </td>
                    <td>
                      <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() => handleStatusToggle(user.id, user.is_active)}
                        disabled={isSelf || statusMutation.isPending}
                        className={`status-btn ${user.is_active ? 'btn-deactivate' : 'btn-activate'}`}
                      >
                        {user.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  )
}
