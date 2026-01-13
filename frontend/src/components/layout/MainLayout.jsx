import { useState } from 'react'
import { Sidebar } from './Sidebar'
import { TopBar } from './TopBar'

export function MainLayout({ children }) {
  const [currentPath, setCurrentPath] = useState('/dashboard')

  const handleNavigate = (path) => {
    setCurrentPath(path)
  }

  return (
    <div className="h-screen flex bg-gray-50 dark:bg-gray-900">
      {/* Left sidebar */}
      <Sidebar currentPath={currentPath} onNavigate={handleNavigate} />

      {/* Main content area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <TopBar />

        {/* Content area */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  )
}
