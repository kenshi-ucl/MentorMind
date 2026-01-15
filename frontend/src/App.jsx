import { MainLayout } from './components/layout'
import { LandingPage } from './components/pages'
import { AuthProvider, useAuth, FriendsProvider, ChatProvider, CallProvider } from './context'
import { IncomingCall } from './components/calls'
import { CallBubble } from './components/calls'
import websocketService from './lib/websocket'
import { useEffect } from 'react'
import './App.css'

function AppContent() {
  const { isAuthenticated, isLoading, token } = useAuth();

  // Connect WebSocket when authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      websocketService.connect(token).catch(err => {
        console.error('WebSocket connection failed:', err);
      });
    }
    
    return () => {
      if (!isAuthenticated) {
        websocketService.disconnect();
      }
    };
  }, [isAuthenticated, token]);

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
    <FriendsProvider>
      <ChatProvider>
        <CallProvider>
          <MainLayout />
          <IncomingCall />
          <CallBubble />
        </CallProvider>
      </ChatProvider>
    </FriendsProvider>
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
