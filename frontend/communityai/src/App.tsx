import { Navigate, Route, Routes } from 'react-router-dom'
import type { ReactElement } from 'react'

import { LoginPage } from './features/auth/pages/LoginPage'
import { RegisterPage } from './features/auth/pages/RegisterPage'
import { useAuth } from './features/auth/hooks/useAuth'
import { HomePage } from './pages/HomePage'

function ProtectedRoute({ children }: { children: ReactElement }) {
  const { accessToken, isBootstrapping } = useAuth()

  if (isBootstrapping) {
    return <div className="auth-loading">Checking session...</div>
  }

  if (!accessToken) {
    return <Navigate to="/login" replace />
  }

  return children
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <HomePage />
          </ProtectedRoute>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default App
