import { cn } from '../../lib/utils'

export function Badge({ count, className, max = 99 }) {
  if (!count || count <= 0) return null;
  
  const displayCount = count > max ? `${max}+` : count;
  
  return (
    <span className={cn(
      "inline-flex items-center justify-center min-w-[18px] h-[18px] px-1",
      "text-xs font-medium text-white bg-red-500 rounded-full",
      className
    )}>
      {displayCount}
    </span>
  );
}
