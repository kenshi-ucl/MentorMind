import { LayoutDashboard, BookOpen, Dumbbell, TrendingUp, History, Settings, Users, UsersRound } from 'lucide-react'
import { useFriends } from '../../context/FriendsContext'
import { Badge } from '../ui/Badge'

const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: BookOpen, label: 'Lessons', path: '/lessons' },
  { icon: Dumbbell, label: 'Practice', path: '/practice' },
  { icon: Users, label: 'Friends', path: '/friends', hasBadge: true },
  { icon: UsersRound, label: 'Study Groups', path: '/groups' },
  { icon: TrendingUp, label: 'Progress', path: '/progress' },
  { icon: History, label: 'History', path: '/history' },
  { icon: Settings, label: 'Settings', path: '/settings' },
]

export function Sidebar({ currentPath = '/dashboard', onNavigate }) {
  const friendsContext = useFriends?.() || { pendingCount: 0 };
  const { pendingCount } = friendsContext;
  
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
          {navItems.map(({ icon: Icon, label, path, hasBadge }) => {
            const isActive = currentPath === path
            const badgeCount = hasBadge && path === '/friends' ? pendingCount : 0
            
            return (
              <li key={path}>
                <button
                  onClick={() => onNavigate?.(path)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{label}</span>
                  </div>
                  {badgeCount > 0 && <Badge count={badgeCount} />}
                </button>
              </li>
            )
          })}
        </ul>
      </nav>
    </aside>
  )
}
