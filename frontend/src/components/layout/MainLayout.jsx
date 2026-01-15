import { useState } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { ProgressDashboard } from '../progress/ProgressDashboard'
import { DashboardView } from '../pages/DashboardView'
import { SettingsView } from '../pages/SettingsView'
import { PracticeView } from '../pages/PracticeView'
import { LessonsView } from '../pages/LessonsView'

export function MainLayout({ children }) {
  const [currentPath, setCurrentPath] = useState('/dashboard')

  const handleNavigate = (path) => {
    setCurrentPath(path)
  }

  // Render content based on current path
  const renderContent = () => {
    switch (currentPath) {
      case '/lessons':
        return <LessonsView />;
      case '/practice':
        return <PracticeView />;
      case '/progress':
        return (
          <div className="p-6 overflow-auto h-full">
            <ProgressDashboard />
          </div>
        );
      case '/settings':
        return <SettingsView />;
      case '/dashboard':
      default:
        return children || <DashboardView onNavigate={handleNavigate} />;
    }
  };

  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Left sidebar */}
      <Sidebar currentPath={currentPath} onNavigate={handleNavigate} />

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <TopBar />

        {/* Content area */}
        <main className="flex-1 min-h-0 overflow-hidden">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}
