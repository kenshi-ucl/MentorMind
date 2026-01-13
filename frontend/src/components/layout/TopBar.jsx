import { Sun, Moon, User } from 'lucide-react'
import { useTheme } from '../../context/ThemeContext'
import { useAuth } from '../../context/AuthContext'
import { Button } from '../ui'

export function TopBar({ title = 'MentorMind' }) {
  const { theme, toggleTheme } = useTheme()
  const { user, isAnonymous } = useAuth()

  const displayName = isAnonymous ? 'Guest' : (user?.name || 'User')

  return (
    <header className="h-16 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-6">
      {/* App title */}
      <h1 className="text-xl font-semibold text-gray-900 dark:text-gray-100">
        {title}
      </h1>

      {/* Right side controls */}
      <div className="flex items-center gap-4">
        {/* Theme toggle */}
        <Button
          variant="ghost"
          size="icon"
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
        >
          {theme === 'light' ? (
            <Moon className="w-5 h-5" />
          ) : (
            <Sun className="w-5 h-5" />
          )}
        </Button>

        {/* User profile area */}
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-700">
          <User className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {displayName}
          </span>
        </div>
      </div>
    </header>
  )
}
