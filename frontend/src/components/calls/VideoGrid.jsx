import { useEffect, useRef, useState, useCallback } from 'react';
import { MicOff, VideoOff } from 'lucide-react';
import { Avatar } from '../ui/Avatar';
import { cn } from '../../lib/utils';

function VideoTile({ stream, participant, isLocal, isVideoOff, isMuted }) {
  const videoRef = useRef(null);
  const [hasEnabledVideoTrack, setHasEnabledVideoTrack] = useState(false);
  const [trackCount, setTrackCount] = useState(0);
  
  // Check if stream has enabled video tracks
  const checkVideoTracks = useCallback(() => {
    if (!stream) {
      setHasEnabledVideoTrack(false);
      setTrackCount(0);
      return;
    }
    const videoTracks = stream.getVideoTracks();
    const hasVideo = videoTracks.length > 0 && videoTracks.some(t => t.enabled && t.readyState === 'live');
    console.log(`VideoTile [${isLocal ? 'local' : participant?.userName}] checkVideoTracks:`, hasVideo, 
      'tracks:', videoTracks.map(t => `enabled:${t.enabled},state:${t.readyState}`));
    setHasEnabledVideoTrack(hasVideo);
    setTrackCount(stream.getTracks().length);
  }, [stream, isLocal, participant?.userName]);
  
  // Set up stream and track listeners
  useEffect(() => {
    if (!stream) {
      setHasEnabledVideoTrack(false);
      setTrackCount(0);
      return;
    }
    
    // Assign stream to video element
    if (videoRef.current) {
      videoRef.current.srcObject = stream;
    }
    
    // Initial check
    checkVideoTracks();
    
    // Listen for track additions/removals on the stream
    const handleTrackChange = () => {
      console.log(`VideoTile [${isLocal ? 'local' : participant?.userName}] track change event`);
      checkVideoTracks();
      // Re-assign stream to video element to pick up new tracks
      if (videoRef.current) {
        videoRef.current.srcObject = null;
        videoRef.current.srcObject = stream;
      }
    };
    
    stream.addEventListener('addtrack', handleTrackChange);
    stream.addEventListener('removetrack', handleTrackChange);
    
    // Listen for track enabled/disabled changes on current video tracks
    const videoTracks = stream.getVideoTracks();
    const trackListeners = [];
    
    videoTracks.forEach(track => {
      const listener = () => {
        console.log(`VideoTile [${isLocal ? 'local' : participant?.userName}] track event:`, track.enabled, track.readyState);
        checkVideoTracks();
      };
      track.addEventListener('mute', listener);
      track.addEventListener('unmute', listener);
      track.addEventListener('ended', listener);
      trackListeners.push({ track, listener });
    });
    
    return () => {
      stream.removeEventListener('addtrack', handleTrackChange);
      stream.removeEventListener('removetrack', handleTrackChange);
      trackListeners.forEach(({ track, listener }) => {
        track.removeEventListener('mute', listener);
        track.removeEventListener('unmute', listener);
        track.removeEventListener('ended', listener);
      });
    };
  }, [stream, checkVideoTracks, isLocal, participant?.userName]);
  
  // Re-check when isVideoOff prop changes (for local video toggle)
  useEffect(() => {
    checkVideoTracks();
  }, [isVideoOff, checkVideoTracks]);
  
  // Re-check periodically to catch track changes that might not trigger events
  // This is a fallback for when tracks are merged into the stream
  useEffect(() => {
    if (!stream) return;
    
    const interval = setInterval(() => {
      const currentTrackCount = stream.getTracks().length;
      if (currentTrackCount !== trackCount) {
        console.log(`VideoTile [${isLocal ? 'local' : participant?.userName}] track count changed: ${trackCount} -> ${currentTrackCount}`);
        checkVideoTracks();
        // Re-assign stream to video element
        if (videoRef.current) {
          videoRef.current.srcObject = null;
          videoRef.current.srcObject = stream;
        }
      }
    }, 200); // Check every 200ms for faster updates
    
    return () => clearInterval(interval);
  }, [stream, trackCount, checkVideoTracks, isLocal, participant?.userName]);
  
  // For local video, we show video if we have enabled tracks AND isVideoOff is false
  // For remote video, we show video if we have enabled tracks AND participant's isVideoOff is false
  const showVideo = stream && hasEnabledVideoTrack && !isVideoOff;
  
  console.log(`VideoTile [${isLocal ? 'local' : participant?.userName}] render: showVideo=${showVideo}, hasEnabledVideoTrack=${hasEnabledVideoTrack}, isVideoOff=${isVideoOff}`);
  
  return (
    <div className="relative bg-gray-800 rounded-lg overflow-hidden" style={{ minHeight: 0 }}>
      {/* Always render video element to maintain ref, but hide when not showing */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted={isLocal}
        className={cn(
          "absolute inset-0 w-full h-full object-cover",
          isLocal && "transform scale-x-[-1]",
          !showVideo && "hidden"
        )}
      />
      
      {/* Show avatar when video is off */}
      {!showVideo && (
        <div className="absolute inset-0 flex items-center justify-center">
          <Avatar 
            name={participant?.userName || 'You'} 
            size="lg" 
          />
        </div>
      )}
      
      {/* Overlay */}
      <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/60 to-transparent">
        <div className="flex items-center justify-between">
          <span className="text-white text-sm font-medium truncate">
            {isLocal ? 'You' : participant?.userName}
          </span>
          
          <div className="flex items-center gap-1 flex-shrink-0">
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

export function VideoGrid({ localStream, remoteStreams, participants, currentUserId, isVideoOff }) {
  // Filter out the current user from participants
  // Show remote participants if we have a stream for them OR if they're in the call
  const allRemoteParticipants = participants?.filter(p => p.userId !== currentUserId) || [];
  
  // Get participants that we actually have streams for
  const remoteParticipantsWithStreams = allRemoteParticipants.filter(p => 
    remoteStreams[p.userId]
  );
  
  const totalParticipants = remoteParticipantsWithStreams.length + 1; // +1 for local
  
  console.log('VideoGrid - currentUserId:', currentUserId);
  console.log('VideoGrid - all participants:', participants?.map(p => ({ userId: p.userId, userName: p.userName, status: p.status })));
  console.log('VideoGrid - remote participants with streams:', remoteParticipantsWithStreams.map(p => ({ userId: p.userId, userName: p.userName })));
  console.log('VideoGrid - remoteStreams keys:', Object.keys(remoteStreams));
  console.log('VideoGrid - totalParticipants:', totalParticipants);
  
  // Determine grid layout based on participant count
  let gridCols;
  
  if (totalParticipants === 1) {
    gridCols = 1;
  } else if (totalParticipants === 2) {
    gridCols = 2;
  } else if (totalParticipants <= 4) {
    gridCols = 2;
  } else if (totalParticipants <= 9) {
    gridCols = 3;
  } else {
    gridCols = 4;
  }
  
  // Calculate rows needed
  const gridRows = Math.ceil(totalParticipants / gridCols);
  
  console.log('VideoGrid - gridCols:', gridCols, 'gridRows:', gridRows);
  
  return (
    <div 
      className="h-full w-full grid gap-2 p-2"
      style={{
        gridTemplateColumns: `repeat(${gridCols}, 1fr)`,
        gridTemplateRows: `repeat(${gridRows}, 1fr)`,
        gridAutoRows: '1fr'
      }}
    >
      {/* Local video */}
      <VideoTile
        stream={localStream}
        isLocal
        isVideoOff={isVideoOff}
      />
      
      {/* Remote videos */}
      {remoteParticipantsWithStreams.map(participant => (
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
