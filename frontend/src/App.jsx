import { MainLayout } from './components/layout'
import { LandingPage } from './components/pages'
import { AuthProvider, useAuth } from './context/AuthContext'
import './App.css'

function AppContent() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-gray-600 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <LandingPage onAuthSuccess={() => {}} />;
  }

  return (
    <MainLayout>
      <div className="flex flex-col items-center justify-center h-full">
        <h2 className="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mb-4">
          Welcome to MentorMind
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Your Personal AI Tutor — Learn Smarter
        </p>
      </div>
    </MainLayout>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  )
}

export default App
