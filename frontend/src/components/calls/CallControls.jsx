import { Mic, MicOff, Video, VideoOff, Monitor, PhoneOff } from 'lucide-react';
import { Button } from '../ui';
import { cn } from '../../lib/utils';

export function CallControls({
  isMuted,
  isVideoOff,
  isScreenSharing,
  isVideo,
  onToggleMute,
  onToggleVideo,
  onToggleScreenShare,
  onEndCall
}) {
  return (
    <div className="flex items-center justify-center gap-4">
      <Button
        size="lg"
        variant="ghost"
        className={cn(
          "rounded-full w-14 h-14",
          isMuted ? "bg-red-500 text-white" : "bg-white/20 text-white hover:bg-white/30"
        )}
        onClick={onToggleMute}
        title={isMuted ? "Unmute" : "Mute"}
      >
        {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
      </Button>
      
      {isVideo && (
        <Button
          size="lg"
          variant="ghost"
          className={cn(
            "rounded-full w-14 h-14",
            isVideoOff ? "bg-red-500 text-white" : "bg-white/20 text-white hover:bg-white/30"
          )}
          onClick={onToggleVideo}
          title={isVideoOff ? "Turn on camera" : "Turn off camera"}
        >
          {isVideoOff ? <VideoOff className="w-6 h-6" /> : <Video className="w-6 h-6" />}
        </Button>
      )}
      
      <Button
        size="lg"
        variant="ghost"
        className={cn(
          "rounded-full w-14 h-14",
          isScreenSharing ? "bg-green-500 text-white" : "bg-white/20 text-white hover:bg-white/30"
        )}
        onClick={onToggleScreenShare}
        title={isScreenSharing ? "Stop sharing" : "Share screen"}
      >
        <Monitor className="w-6 h-6" />
      </Button>
      
      <Button
        size="lg"
        className="rounded-full w-14 h-14 bg-red-500 hover:bg-red-600"
        onClick={onEndCall}
        title="End call"
      >
        <PhoneOff className="w-6 h-6" />
      </Button>
    </div>
  );
}
