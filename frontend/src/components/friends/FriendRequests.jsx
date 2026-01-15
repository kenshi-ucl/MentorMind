import { Check, X } from 'lucide-react';
import { useFriends } from '../../context/FriendsContext';
import { Button } from '../ui';
import { Avatar } from '../ui/Avatar';

export function FriendRequests() {
  const { pendingRequests, acceptRequest, declineRequest } = useFriends();
  
  if (pendingRequests.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <p>No pending friend requests</p>
      </div>
    );
  }
  
  const handleAccept = async (requestId) => {
    await acceptRequest(requestId);
  };
  
  const handleDecline = async (requestId) => {
    await declineRequest(requestId);
  };
  
  return (
    <div className="space-y-2">
      {pendingRequests.map(request => (
        <div
          key={request.id}
          className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        >
          <div className="flex items-center gap-3">
            <Avatar name={request.sender?.name} />
            <div>
              <p className="font-medium text-gray-900 dark:text-white">
                {request.sender?.name}
              </p>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {request.sender?.email}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={() => handleAccept(request.id)}
              className="bg-green-500 hover:bg-green-600"
            >
              <Check className="w-4 h-4 mr-1" />
              Accept
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => handleDecline(request.id)}
            >
              <X className="w-4 h-4 mr-1" />
              Decline
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
