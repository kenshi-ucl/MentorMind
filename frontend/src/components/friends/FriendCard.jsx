import { MessageCircle, Phone, Video, UserMinus } from 'lucide-react';
import { Avatar } from '../ui/Avatar';
import { Button } from '../ui';

export function FriendCard({ friend, onChat, onVoiceCall, onVideoCall, onRemove }) {
  return (
    <div className="flex items-center justify-between p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
      <div className="flex items-center gap-3">
        <Avatar 
          name={friend.name} 
          isOnline={friend.isOnline} 
          showStatus 
        />
        <div>
          <p className="font-medium text-gray-900 dark:text-white">
            {friend.name}
          </p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {friend.isOnline ? (
              <span className="text-green-500">Online</span>
            ) : friend.lastSeen ? (
              `Last seen ${new Date(friend.lastSeen).toLocaleDateString()}`
            ) : (
              'Offline'
            )}
          </p>
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onChat?.(friend)}
          title="Send message"
        >
          <MessageCircle className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onVoiceCall?.(friend)}
          title="Voice call"
        >
          <Phone className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onVideoCall?.(friend)}
          title="Video call"
        >
          <Video className="w-4 h-4" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => onRemove?.(friend)}
          title="Remove friend"
          className="text-red-500 hover:text-red-600"
        >
          <UserMinus className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
