import { NavLink, useNavigate } from 'react-router-dom'

import { useAuth } from '../features/auth/hooks/useAuth'

export function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="app-navbar">
      <div className="navbar-container">
        <NavLink to="/" className="navbar-brand">
          CommunityAI
        </NavLink>

        <nav className="navbar-links">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `navbar-link ${isActive ? 'active' : ''}`
            }
            end
          >
            Home
          </NavLink>

          <NavLink
            to="/profile"
            className={({ isActive }) =>
              `navbar-link ${isActive ? 'active' : ''}`
            }
          >
            Profile
          </NavLink>

          <NavLink
            to="/social-accounts"
            className={({ isActive }) =>
              `navbar-link ${isActive ? 'active' : ''}`
            }
          >
            Social Accounts
          </NavLink>

          <NavLink
            to="/posts"
            className={({ isActive }) =>
              `navbar-link ${isActive ? 'active' : ''}`
            }
          >
            Posts
          </NavLink>

          <NavLink
            to="/calendar"
            className={({ isActive }) =>
              `navbar-link ${isActive ? 'active' : ''}`
            }
          >
            Calendar
          </NavLink>

          <NavLink
            to="/ai"
            className={({ isActive }) =>
              `navbar-link ${isActive ? 'active' : ''}`
            }
          >
            AI Assistant
          </NavLink>

          <NavLink
            to="/inbox"
            className={({ isActive }) =>
              `navbar-link ${isActive ? 'active' : ''}`
            }
          >
            Inbox
          </NavLink>

          {user?.role === 'ADMIN' && (
            <NavLink
              to="/admin/users"
              className={({ isActive }) =>
                `navbar-link ${isActive ? 'active' : ''}`
              }
            >
              User Management
            </NavLink>
          )}
        </nav>

        <div className="navbar-user">
          {user && (
            <span className="navbar-user-text">
              {user.first_name} {user.last_name} ({user.role})
            </span>
          )}

          <button
            type="button"
            onClick={handleLogout}
            className="navbar-logout-btn"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}