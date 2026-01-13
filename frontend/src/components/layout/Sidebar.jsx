import { LayoutDashboard, BookOpen, Dumbbell, TrendingUp, Settings } from 'lucide-react'

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: BookOpen, label: 'Lessons', path: '/lessons' },
  { icon: Dumbbell, label: 'Practice', path: '/practice' },
  { icon: TrendingUp, label: 'Progress', path: '/progress' },
  { icon: Settings, label: 'Settings', path: '/settings' },
]

export function Sidebar({ currentPath = '/dashboard', onNavigate }) {
  return (
    <aside className="w-64 h-full bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 flex flex-col">
      {/* Logo area */}
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <img src="/logo.svg" alt="MentorMind" className="w-8 h-8" />
          <span className="text-xl font-bold text-indigo-600 dark:text-indigo-400">
            MentorMind
          </span>
        </div>
      </div>
      
      {/* Navigation */}
      <nav className="flex-1 p-4">
        <ul className="space-y-2">
          {navItems.map(({ icon: Icon, label, path }) => {
            const isActive = currentPath === path
            return (
              <li key={path}>
                <button
                  onClick={() => onNavigate?.(path)}
                  className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{label}</span>
                </button>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}
