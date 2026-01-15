import { Users } from 'lucide-react';

export function GroupList({ groups = [], selectedId, onSelect }) {
  if (!groups || groups.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-4 text-gray-500 dark:text-gray-400">
        <Users className="w-12 h-12 mb-2 opacity-50" />
        <p>No groups yet</p>
        <p className="text-sm">Create a group to start learning together</p>
      </div>
    );
  }
  
  return (
    <div className="flex-1 overflow-y-auto p-2 space-y-1">
      {groups.map(group => (
        <button
          key={group.id}
          onClick={() => onSelect?.(group)}
          className={`w-full flex items-center gap-3 p-3 rounded-lg transition-colors text-left ${
            selectedId === group.id
              ? 'bg-indigo-50 dark:bg-indigo-900/30 border-indigo-200 dark:border-indigo-700'
              : 'hover:bg-gray-50 dark:hover:bg-gray-700'
          }`}
        >
          <div className="w-10 h-10 rounded-full bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center flex-shrink-0">
            <Users className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-medium text-gray-900 dark:text-white truncate">
              {group.name || 'Unnamed Group'}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {group.memberCount || 0} members
            </p>
          </div>
        </button>
      ))}
    </div>
  );
}
