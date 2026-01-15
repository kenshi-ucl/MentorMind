import { Users, Check, X } from 'lucide-react';

export function GroupInvitations({ invitations = [], onAccept, onDecline }) {
  if (!invitations || invitations.length === 0) return null;

  return (
    <div className="p-3 border-b border-gray-200 dark:border-gray-700 bg-indigo-50 dark:bg-indigo-900/20">
      <h3 className="text-sm font-medium text-indigo-700 dark:text-indigo-300 mb-2">
        Pending Invitations ({invitations.length})
      </h3>
      <div className="space-y-2">
        {invitations.map(invitation => (
          <div
            key={invitation.membershipId || invitation.group?.id}
            className="flex items-center gap-2 p-2 bg-white dark:bg-gray-800 rounded-lg"
          >
            <div className="w-8 h-8 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center flex-shrink-0">
              <Users className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {invitation.group?.name || 'Unknown Group'}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {invitation.group?.memberCount || 0} members
              </p>
            </div>
            <div className="flex gap-1">
              <button
                onClick={() => onAccept(invitation.group?.id)}
                className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                title="Accept"
              >
                <Check className="w-4 h-4" />
              </button>
              <button
                onClick={() => onDecline(invitation.group?.id)}
                className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded"
                title="Decline"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
