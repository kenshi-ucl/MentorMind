import { Avatar } from '../ui/Avatar';
import { Badge } from '../ui/Badge';

export function ParticipantList({ participants, currentUserId, creatorId, onRemove }) {
  const isCreator = currentUserId === creatorId;

  const getRoleBadge = (role) => {
    switch (role) {
      case 'creator':
        return <Badge variant="primary">Creator</Badge>;
      case 'admin':
        return <Badge variant="secondary">Admin</Badge>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-2">
      {participants.map(participant => (
        <div
          key={participant.id}
          className="flex items-center gap-3 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
        >
          <div className="relative">
            <Avatar name={participant.name} size="sm" />
            {participant.isOnline && (
              <span className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <span className="font-medium text-gray-900 dark:text-white truncate">
                {participant.name}
                {participant.id === currentUserId && (
                  <span className="text-gray-500 dark:text-gray-400 ml-1">(you)</span>
                )}
              </span>
              {getRoleBadge(participant.role)}
            </div>
            {participant.joinedAt && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Joined {new Date(participant.joinedAt).toLocaleDateString()}
              </p>
            )}
          </div>

          {isCreator && participant.id !== currentUserId && participant.role !== 'creator' && (
            <button
              onClick={() => onRemove(participant.id)}
              className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
              title="Remove from group"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
