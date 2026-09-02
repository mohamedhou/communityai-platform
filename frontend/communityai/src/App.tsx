import { Navigate, Route, Routes, Outlet } from 'react-router-dom'
import type { ReactElement } from 'react'

import { LoginPage } from './features/auth/pages/LoginPage'
import { RegisterPage } from './features/auth/pages/RegisterPage'
import { useAuth } from './features/auth/hooks/useAuth'

import { HomePage } from './pages/HomePage'

import { Navbar } from './components/Navbar'

import { ProfilePage } from './features/users/pages/ProfilePage'
import { UserManagementPage } from './features/users/pages/UserManagementPage'

import { SocialAccountsPage } from './features/social-accounts/pages/SocialAccountsPage'

import { PostsPage } from './features/posts/pages/PostsPage'
import { CreatePostPage } from './features/posts/pages/CreatePostPage'
import { EditorialCalendarPage } from './features/calendar/pages/EditorialCalendarPage'


function ProtectedLayout() {
  const { accessToken, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return (
      <div className="auth-loading">
        Checking session...
      </div>
    )
  }

  if (!accessToken) {
    return <Navigate to="/login" replace />
  }

  return (
    <div className="app-layout">
      <Navbar />
      <Outlet />
    </div>
  )
}


function AdminRoute({
  children,
}: {
  children: ReactElement
}) {
  const { user, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return (
      <div className="auth-loading">
        Checking session...
      </div>
    )
  }

  if (!user || user.role !== 'ADMIN') {
    return <Navigate to="/" replace />
  }

  return children
}


function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={<LoginPage />}
      />

      <Route
        path="/register"
        element={<RegisterPage />}
      />

      {/* Protected routes */}
      <Route element={<ProtectedLayout />}>
        <Route
          path="/"
          element={<HomePage />}
        />

        <Route
          path="/profile"
          element={<ProfilePage />}
        />

        <Route
          path="/social-accounts"
          element={<SocialAccountsPage />}
        />

        {/* Posts */}
        <Route
          path="/posts"
          element={<PostsPage />}
        />

        <Route
          path="/posts/new"
          element={<CreatePostPage />}
        />

        <Route
          path="/posts/:postId/edit"
          element={<CreatePostPage />}
        />

        {/* Calendar */}
        <Route
          path="/calendar"
          element={<EditorialCalendarPage />}
        />

        {/* Admin */}
        <Route
          path="/admin/users"
          element={
            <AdminRoute>
              <UserManagementPage />
            </AdminRoute>
          }
        />
      </Route>

      {/* Fallback */}
      <Route
        path="*"
        element={<Navigate to="/" replace />}
      />
    </Routes>

  )
}

export default App