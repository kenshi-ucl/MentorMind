import { useState } from 'react';
import { Button } from '../ui';
import { LoginForm, RegisterForm, AnonymousButton } from '../auth';

export function LandingPage({ onAuthSuccess }) {
  const [showAuth, setShowAuth] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // 'login' or 'register'

  const handleGetStarted = () => {
    setShowAuth(true);
    setAuthMode('register');
  };

  const handleSignIn = () => {
    setShowAuth(true);
    setAuthMode('login');
  };

  if (showAuth) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex flex-col items-center justify-center p-4">
        <div className="mb-8 flex items-center gap-3">
          <img src="/logo.svg" alt="MentorMind" className="w-12 h-12" />
          <span className="text-2xl font-bold text-indigo-600 dark:text-cyan-400">MentorMind</span>
        </div>
        
        {authMode === 'login' ? (
          <LoginForm 
            onSwitchToRegister={() => setAuthMode('register')}
            onSuccess={onAuthSuccess}
          />
        ) : (
          <RegisterForm 
            onSwitchToLogin={() => setAuthMode('login')}
            onSuccess={onAuthSuccess}
          />
        )}
        
        <div className="mt-6 w-full max-w-md">
          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-gray-300 dark:border-gray-600"></div>
            </div>
            <div className="relative flex justify-center text-sm">
              <span className="px-2 bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 text-gray-500">
                or
              </span>
            </div>
          </div>
          
          <div className="mt-6">
            <AnonymousButton onSuccess={onAuthSuccess} />
          </div>
        </div>
        
        <button
          onClick={() => setShowAuth(false)}
          className="mt-6 text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
        >
          ← Back to home
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Navigation */}
      <nav className="flex items-center justify-between p-6 max-w-7xl mx-auto">
        <div className="flex items-center gap-3">
          <img src="/logo.svg" alt="MentorMind" className="w-10 h-10" />
          <span className="text-xl font-bold text-indigo-600 dark:text-cyan-400">MentorMind</span>
        </div>
        <Button 
          variant="outline" 
          onClick={handleSignIn}
          className="border-indigo-600 text-indigo-600 hover:bg-indigo-50 dark:border-cyan-400 dark:text-cyan-400 dark:hover:bg-cyan-900/20"
        >
          Sign In
        </Button>
      </nav>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-6 pt-20 pb-32">
        <div className="text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
            Your Personal AI Tutor
            <span className="block text-indigo-600 dark:text-cyan-400">Learn Smarter</span>
          </h1>
          
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-2xl mx-auto mb-10">
            Get personalized explanations, upload your study materials, take adaptive quizzes, 
            and track your progress — all powered by AI that adapts to your learning style.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button 
              onClick={handleGetStarted}
              className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-3 text-lg"
            >
              Get Started Free
            </Button>
            <Button 
              variant="outline"
              onClick={handleSignIn}
              className="border-gray-300 text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-800 px-8 py-3 text-lg"
            >
              I have an account
            </Button>
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-32 grid md:grid-cols-3 gap-8">
          <FeatureCard
            icon="💬"
            title="AI Chat Tutor"
            description="Ask questions and get clear, personalized explanations on any topic."
          />
          <FeatureCard
            icon="📚"
            title="Content Upload"
            description="Upload videos and PDFs — our AI extracts key points and helps you study."
          />
          <FeatureCard
            icon="📝"
            title="Smart Quizzes"
            description="Test your knowledge with AI-generated quizzes tailored to your content."
          />
        </div>
      </main>
    </div>
  );
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-100 dark:border-gray-700">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">{title}</h3>
      <p className="text-gray-600 dark:text-gray-400">{description}</p>
    </div>
  );
}

export default LandingPage;
