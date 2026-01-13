import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button, Input, Card } from '../ui';

export function LoginForm({ onSwitchToRegister, onSuccess }) {
  const { login, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    setIsLoading(true);
    
    const result = await login(email, password);
    setIsLoading(false);
    
    if (result.success && onSuccess) {
      onSuccess();
    }
  };

  return (
    <Card className="w-full max-w-md p-6">
      <h2 className="text-2xl font-bold text-center mb-6 text-gray-900 dark:text-white">
        Welcome Back
      </h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Email
          </label>
          <Input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            disabled={isLoading}
          />
        </div>
        
        <div>
          <label htmlFor="password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
            Password
          </label>
          <Input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            disabled={isLoading}
          />
        </div>

        {error && (
          <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-md">
            {error}
          </div>
        )}
        
        <Button 
          type="submit" 
          className="w-full bg-indigo-600 hover:bg-indigo-700"
          disabled={isLoading}
        >
          {isLoading ? 'Signing in...' : 'Sign In'}
        </Button>
      </form>
      
      <p className="mt-4 text-center text-sm text-gray-600 dark:text-gray-400">
        Don't have an account?{' '}
        <button
          type="button"
          onClick={onSwitchToRegister}
          className="text-indigo-600 hover:text-indigo-500 dark:text-cyan-400 dark:hover:text-cyan-300 font-medium"
        >
          Sign up
        </button>
      </p>
    </Card>
  );
}

export default LoginForm;
