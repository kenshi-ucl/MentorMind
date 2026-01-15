import { useState } from 'react';
import { Search, UserPlus, Check, Clock } from 'lucide-react';
import { useFriends } from '../../context/FriendsContext';
import { Input, Button } from '../ui';
import { Avatar } from '../ui/Avatar';

export function FriendSearch() {
  const [query, setQuery] = useState('');
  const { searchResults, searchUsers, sendFriendRequest, isLoading, clearSearch } = useFriends();
  
  const handleSearch = (e) => {
    const value = e.target.value;
    setQuery(value);
    
    if (value.length >= 2) {
      searchUsers(value);
    } else {
      clearSearch();
    }
  };
  
  const handleSendRequest = async (userId) => {
    const result = await sendFriendRequest(userId);
    if (result.success) {
      // Refresh search to update button state
      searchUsers(query);
    }
  };
  
  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
        <Input
          type="text"
          placeholder="Search by name or email..."
          value={query}
          onChange={handleSearch}
          className="pl-10"
        />
      </div>
      
      {isLoading && (
        <div className="text-center py-4 text-gray-500">
          Searching...
        </div>
      )}
      
      {!isLoading && searchResults.length > 0 && (
        <div className="space-y-2">
          {searchResults.map(user => (
            <div
              key={user.id}
              className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-center gap-3">
                <Avatar name={user.name} />
                <div>
                  <p className="font-medium text-gray-900 dark:text-white">
                    {user.name}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {user.email}
                  </p>
                </div>
              </div>
              
              {user.isFriend ? (
                <span className="flex items-center gap-1 text-sm text-green-500">
                  <Check className="w-4 h-4" />
                  Friends
                </span>
              ) : user.hasPendingRequest ? (
                <span className="flex items-center gap-1 text-sm text-yellow-500">
                  <Clock className="w-4 h-4" />
                  Pending
                </span>
              ) : user.hasReceivedRequest ? (
                <span className="text-sm text-blue-500">
                  Sent you a request
                </span>
              ) : (
                <Button
                  size="sm"
                  onClick={() => handleSendRequest(user.id)}
                >
                  <UserPlus className="w-4 h-4 mr-1" />
                  Add Friend
                </Button>
              )}
            </div>
          ))}
        </div>
      )}
      
      {!isLoading && query.length >= 2 && searchResults.length === 0 && (
        <div className="text-center py-4 text-gray-500">
          No users found
        </div>
      )}
    </div>
  );
}
