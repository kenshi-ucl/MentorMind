import { useFriends } from '../../context/FriendsContext';
import { FriendCard } from './FriendCard';

export function FriendsList({ onChat, onVoiceCall, onVideoCall }) {
  const { friends, removeFriend } = useFriends();
  
  const handleRemove = async (friend) => {
    if (confirm(`Remove ${friend.name} from friends?`)) {
      await removeFriend(friend.id);
    }
  };
  
  if (friends.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500 dark:text-gray-400">
        <p>No friends yet</p>
        <p className="text-sm mt-1">Search for users to add friends</p>
      </div>
    );
  }
  
  // Sort: online friends first
  const sortedFriends = [...friends].sort((a, b) => {
    if (a.isOnline && !b.isOnline) return -1;
    if (!a.isOnline && b.isOnline) return 1;
    return a.name.localeCompare(b.name);
  });
  
  const onlineFriends = sortedFriends.filter(f => f.isOnline);
  const offlineFriends = sortedFriends.filter(f => !f.isOnline);
  
  return (
    <div className="space-y-4">
      {onlineFriends.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            Online — {onlineFriends.length}
          </h3>
          <div className="space-y-2">
            {onlineFriends.map(friend => (
              <FriendCard
                key={friend.id}
                friend={friend}
                onChat={onChat}
                onVoiceCall={onVoiceCall}
                onVideoCall={onVideoCall}
                onRemove={handleRemove}
              />
            ))}
          </div>
        </div>
      )}
      
      {offlineFriends.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">
            Offline — {offlineFriends.length}
          </h3>
          <div className="space-y-2">
            {offlineFriends.map(friend => (
              <FriendCard
                key={friend.id}
                friend={friend}
                onChat={onChat}
                onVoiceCall={onVoiceCall}
                onVideoCall={onVideoCall}
                onRemove={handleRemove}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
