import { useAuth } from '../../context/AuthContext';
import { cn } from '../../lib/utils';

export function MessageList({ messages, onLoadMore }) {
  const { user } = useAuth();
  
  if (messages.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
        No messages yet. Start the conversation!
      </div>
    );
  }
  
  return (
    <div className="space-y-4">
      {messages.map((message, index) => {
        const isOwn = message.senderId === user?.id;
        const showDate = index === 0 || 
          new Date(message.createdAt).toDateString() !== 
          new Date(messages[index - 1].createdAt).toDateString();
        
        return (
          <div key={message.id}>
            {showDate && (
              <div className="flex justify-center my-4">
                <span className="px-3 py-1 text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 rounded-full">
                  {new Date(message.createdAt).toLocaleDateString()}
                </span>
              </div>
            )}
            
            <div className={cn(
              "flex",
              isOwn ? "justify-end" : "justify-start"
            )}>
              <div className={cn(
                "max-w-[70%] px-4 py-2 rounded-2xl",
                isOwn 
                  ? "bg-indigo-500 text-white rounded-br-md" 
                  : "bg-white dark:bg-gray-800 text-gray-900 dark:text-white rounded-bl-md border border-gray-200 dark:border-gray-700"
              )}>
                {!isOwn && (
                  <p className="text-xs font-medium text-indigo-500 mb-1">
                    {message.senderName}
                  </p>
                )}
                <p className="whitespace-pre-wrap break-words">
                  {message.content}
                </p>
                <p className={cn(
                  "text-xs mt-1",
                  isOwn ? "text-indigo-200" : "text-gray-400"
                )}>
                  {new Date(message.createdAt).toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
                </p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
