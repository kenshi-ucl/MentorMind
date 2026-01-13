import { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../ui';

export function AnonymousButton({ onSuccess }) {
  const { continueAnonymously, error } = useAuth();
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    setIsLoading(true);
    const result = await continueAnonymously();
    setIsLoading(false);
    
    if (result.success && onSuccess) {
      onSuccess();
    }
  };

  return (
    <div className="text-center">
      <Button
        variant="outline"
        onClick={handleClick}
        disabled={isLoading}
        className="w-full border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800"
      >
        {isLoading ? 'Starting...' : 'Continue without account'}
      </Button>
      {error && (
        <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
    </div>
  );
}

export default AnonymousButton;
