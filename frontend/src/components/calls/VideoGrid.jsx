import { useEffect, useRef } from 'react';
import { MicOff, VideoOff } from 'lucide-react';
import { Avatar } from '../ui/Avatar';
import { cn } from '../../lib/utils';

function VideoTile({ stream, participant, isLocal, isVideoOff, isMuted }) {
  const videoRef = useRef(null);
  
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
    }
  }, [stream]);
  
  const showVideo = stream && !isVideoOff;
  
  return (
    <div className="relative bg-gray-800 rounded-lg overflow-hidden aspect-video">
      {showVideo ? (
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted={isLocal}
          className={cn(
            "w-full h-full object-cover",
            isLocal && "transform scale-x-[-1]"
          )}
        />
      ) : (
        <div className="w-full h-full flex items-center justify-center">
          <Avatar 
            name={participant?.userName || 'You'} 
            size="xl" 
          />
        </div>
      )}
      
      {/* Overlay */}
      <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/60 to-transparent">
        <div className="flex items-center justify-between">
          <span className="text-white text-sm font-medium">
            {isLocal ? 'You' : participant?.userName}
          </span>
          
          <div className="flex items-center gap-1">
            {isMuted && (
              <span className="p-1 bg-red-500 rounded-full">
                <MicOff className="w-3 h-3 text-white" />
              </span>
            )}
            {isVideoOff && (
              <span className="p-1 bg-red-500 rounded-full">
                <VideoOff className="w-3 h-3 text-white" />
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function VideoGrid({ localStream, remoteStreams, participants, isVideoOff }) {
  const remoteParticipants = participants?.filter(p => p.status === 'joined') || [];
  const totalParticipants = remoteParticipants.length + 1; // +1 for local
  
  // Determine grid layout
  const gridCols = totalParticipants <= 1 ? 1 
    : totalParticipants <= 4 ? 2 
    : totalParticipants <= 9 ? 3 
    : 4;
  
  return (
    <div 
      className={cn(
        "h-full grid gap-4",
        `grid-cols-${gridCols}`
      )}
      style={{
        gridTemplateColumns: `repeat(${gridCols}, minmax(0, 1fr))`
      }}
    >
      {/* Local video */}
      <VideoTile
        stream={localStream}
        isLocal
        isVideoOff={isVideoOff}
      />
      
      {/* Remote videos */}
      {remoteParticipants.map(participant => (
        <VideoTile
          key={participant.userId}
          stream={remoteStreams[participant.userId]}
          participant={participant}
          isVideoOff={participant.isVideoOff}
          isMuted={participant.isMuted}
        />
      ))}
    </div>
  );
}
