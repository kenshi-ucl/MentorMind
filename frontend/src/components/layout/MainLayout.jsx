import { useState } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'
import { ChatInterface } from '../chat/ChatInterface'
import { ProgressDashboard } from '../progress/ProgressDashboard'

export function MainLayout({ children }) {
  const [currentPath, setCurrentPath] = useState('/dashboard')

  const handleNavigate = (path) => {
    setCurrentPath(path)
  }

  // Render content based on current path
  const renderContent = () => {
    switch (currentPath) {
      case '/lessons':
        return <ChatInterface />;
      case '/practice':
        return (
          <div className="flex flex-col items-center justify-center h-full">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Practice
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Quiz and practice features coming soon.
            </p>
          </div>
        );
      case '/progress':
        return (
          <div className="p-6 overflow-auto h-full">
            <ProgressDashboard />
          </div>
        );
      case '/settings':
        return (
          <div className="flex flex-col items-center justify-center h-full">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              Settings
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Settings page coming soon.
            </p>
          </div>
        );
      case '/dashboard':
      default:
        return children || (
          <div className="flex flex-col items-center justify-center h-full">
            <h2 className="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mb-4">
              Welcome to MentorMind
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              Your Personal AI Tutor — Learn Smarter
            </p>
          </div>
        );
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
        <main className="flex-1 overflow-hidden">
          {renderContent()}
        </main>
      </div>
    </div>
  )
}
