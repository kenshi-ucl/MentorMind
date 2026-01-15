import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Mic, MicOff, PhoneOff, Maximize2 } from 'lucide-react';
import { useCall } from '../../context/CallContext';
import { Button } from '../ui';
import { cn } from '../../lib/utils';

export function CallBubble() {
  const { 
    activeCall, 
    isMinimized, 
    setIsMinimized, 
    isMuted, 
    toggleMute, 
    endCall,
    callDuration,
    localStream
  } = useCall();
  
  const [position, setPosition] = useState(() => {
    const saved = localStorage.getItem('callBubblePosition');
    return saved ? JSON.parse(saved) : { x: 20, y: 20 };
  });
  const [isDragging, setIsDragging] = useState(false);
  const dragRef = useRef({ startX: 0, startY: 0 });
  const bubbleRef = useRef(null);
  const videoRef = useRef(null);
  
  // Attach local stream to video element
  useEffect(() => {
    if (videoRef.current && localStream && activeCall?.callType === 'video') {
      videoRef.current.srcObject = localStream;
    }
  }, [localStream, activeCall]);
  
  // Save position to localStorage
  useEffect(() => {
    localStorage.setItem('callBubblePosition', JSON.stringify(position));
  }, [position]);
  
  const handleMouseDown = (e) => {
    if (e.target.closest('button')) return;
    
    setIsDragging(true);
    dragRef.current = {
      startX: e.clientX - position.x,
      startY: e.clientY - position.y
    };
  };
  
  const handleMouseMove = (e) => {
    if (!isDragging) return;
    
    const newX = e.clientX - dragRef.current.startX;
    const newY = e.clientY - dragRef.current.startY;
    
    // Keep within viewport
    const maxX = window.innerWidth - (bubbleRef.current?.offsetWidth || 200);
    const maxY = window.innerHeight - (bubbleRef.current?.offsetHeight || 150);
    
    setPosition({
      x: Math.max(0, Math.min(newX, maxX)),
      y: Math.max(0, Math.min(newY, maxY))
    });
  };
  
  const handleMouseUp = () => {
    setIsDragging(false);
  };
  
  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);
      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  }, [isDragging]);
  
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  if (!activeCall || !isMinimized) return null;
  
  const isVideo = activeCall.callType === 'video';
  
  return createPortal(
    <div
      ref={bubbleRef}
      className={cn(
        "fixed z-50 rounded-2xl shadow-xl overflow-hidden cursor-move select-none",
        isVideo ? "w-48 h-36" : "w-48 h-20",
        "bg-gray-900"
      )}
      style={{ left: position.x, top: position.y }}
      onMouseDown={handleMouseDown}
    >
      {/* Video preview */}
      {isVideo && (
        <video
          ref={videoRef}
          autoPlay
          muted
          playsInline
          className="absolute inset-0 w-full h-full object-cover"
        />
      )}
      
      {/* Overlay */}
      <div className={cn(
        "absolute inset-0 flex flex-col justify-between p-2",
        isVideo ? "bg-black/30" : "bg-gray-900"
      )}>
        {/* Duration */}
        <div className="flex items-center justify-between">
          <span className="text-white text-sm font-medium">
            {formatDuration(callDuration)}
          </span>
          {isMuted && (
            <span className="flex items-center gap-1 text-red-400 text-xs">
              <MicOff className="w-3 h-3" />
              Muted
            </span>
          )}
        </div>
        
        {/* Controls */}
        <div className="flex items-center justify-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            className={cn(
              "rounded-full w-8 h-8 p-0",
              isMuted ? "bg-red-500 text-white" : "bg-white/20 text-white"
            )}
            onClick={toggleMute}
          >
            {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </Button>
          
          <Button
            size="sm"
            variant="ghost"
            className="rounded-full w-8 h-8 p-0 bg-red-500 text-white hover:bg-red-600"
            onClick={endCall}
          >
            <PhoneOff className="w-4 h-4" />
          </Button>
          
          <Button
            size="sm"
            variant="ghost"
            className="rounded-full w-8 h-8 p-0 bg-white/20 text-white"
            onClick={() => setIsMinimized(false)}
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>,
    document.body
  );
}
