import { cn } from '../../lib/utils'

export function Avatar({ 
  name, 
  src, 
  size = 'md', 
  isOnline, 
  showStatus = false,
  className 
}) {
  const sizeClasses = {
    sm: 'w-8 h-8 text-xs',
    md: 'w-10 h-10 text-sm',
    lg: 'w-12 h-12 text-base',
    xl: 'w-16 h-16 text-lg'
  };
  
  const statusSizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-2.5 h-2.5',
    lg: 'w-3 h-3',
    xl: 'w-4 h-4'
  };
  
  const initials = name
    ?.split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2) || '?';
  
  return (
    <div className={cn("relative inline-block", className)}>
      {src ? (
        <img
          src={src}
          alt={name}
          className={cn(
            "rounded-full object-cover",
            sizeClasses[size]
          )}
        />
      ) : (
        <div className={cn(
          "rounded-full flex items-center justify-center font-medium",
          "bg-indigo-100 dark:bg-indigo-900 text-indigo-600 dark:text-indigo-400",
          sizeClasses[size]
        )}>
          {initials}
        </div>
      )}
      
      {showStatus && (
        <span className={cn(
          "absolute bottom-0 right-0 rounded-full border-2 border-white dark:border-gray-800",
          statusSizeClasses[size],
          isOnline ? "bg-green-500" : "bg-gray-400"
        )} />
      )}
    </div>
  );
}
