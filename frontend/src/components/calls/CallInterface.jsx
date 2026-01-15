import { useEffect, useRef } from 'react';
import { Mic, MicOff, Video, VideoOff, Monitor, PhoneOff, Minimize2 } from 'lucide-react';
import { useCall } from '../../context/CallContext';
import { VideoGrid } from './VideoGrid';

export function CallInterface() {
  const {
    activeCall,
    localStream,
    remoteStreams,
    isMuted,
    isVideoOff,
    isScreenSharing,
    callDuration,
    isMinimized,
    toggleMute,
    toggleVideo,
    toggleScreenShare,
    endCall,
    setIsMinimized
  } = useCall();
  
  const localVideoRef = useRef(null);
  const remoteAudioRefs = useRef({});
  
  // Attach local stream to video element
  useEffect(() => {
    if (localVideoRef.current && localStream) {
      localVideoRef.current.srcObject = localStream;
    }
  }, [localStream]);
  
  // Play remote audio streams
  useEffect(() => {
    console.log('Remote streams updated:', Object.keys(remoteStreams));
    
    Object.entries(remoteStreams).forEach(([userId, stream]) => {
      if (stream) {
        console.log('Processing stream for user:', userId);
        console.log('Stream tracks:', stream.getTracks().map(t => `${t.kind}:${t.enabled}:${t.readyState}`));
        
        // Create or get audio element for this user
        let audioEl = remoteAudioRefs.current[userId];
        if (!audioEl) {
          audioEl = document.createElement('audio');
          audioEl.autoplay = true;
          audioEl.playsInline = true;
          // Don't mute remote audio!
          audioEl.muted = false;
          audioEl.id = `remote-audio-${userId}`;
          // Set volume to max
          audioEl.volume = 1.0;
          document.body.appendChild(audioEl);
          remoteAudioRefs.current[userId] = audioEl;
          console.log('Created audio element for user:', userId);
        }
        
        if (audioEl.srcObject !== stream) {
          audioEl.srcObject = stream;
          console.log('Set audio stream for user:', userId);
          
          // Try to play with user interaction handling
          const playAudio = () => {
            audioEl.play().then(() => {
              console.log('Audio playing for user:', userId, 'volume:', audioEl.volume);
            }).catch(err => {
              console.error('Failed to play audio for user:', userId, err);
              // If autoplay is blocked, we'll try again on user interaction
              if (err.name === 'NotAllowedError') {
                console.log('Autoplay blocked, will retry on user interaction');
                const retryPlay = () => {
                  audioEl.play().catch(e => console.error('Retry play failed:', e));
                  document.removeEventListener('click', retryPlay);
                };
                document.addEventListener('click', retryPlay, { once: true });
              }
            });
          };
          
          playAudio();
        }
      }
    });
    
    // Cleanup removed streams
    Object.keys(remoteAudioRefs.current).forEach(userId => {
      if (!remoteStreams[userId]) {
        const audioEl = remoteAudioRefs.current[userId];
        if (audioEl) {
          audioEl.srcObject = null;
          audioEl.remove();
          delete remoteAudioRefs.current[userId];
          console.log('Removed audio element for user:', userId);
        }
      }
    });
  }, [remoteStreams]);
  
  // Cleanup audio elements on unmount
  useEffect(() => {
    return () => {
      Object.values(remoteAudioRefs.current).forEach(audioEl => {
        if (audioEl) {
          audioEl.srcObject = null;
          audioEl.remove();
        }
      });
      remoteAudioRefs.current = {};
    };
  }, []);
  
  if (!activeCall || isMinimized) return null;
  
  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };
  
  const isVideo = activeCall.callType === 'video';
  const hasVideo = localStream?.getVideoTracks().length > 0 && !isVideoOff;
  const hasRemoteVideo = Object.values(remoteStreams).some(stream => 
    stream?.getVideoTracks().some(track => track.enabled)
  );
  
  return (
    <div className="fixed inset-0 z-50 bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-black/30">
        <div className="text-white">
          <h2 className="font-semibold">{activeCall.contextType === 'direct' ? 'Call' : 'Group Call'}</h2>
          <p className="text-sm text-gray-300">{formatDuration(callDuration)}</p>
        </div>
        
        <button
          className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
          onClick={() => setIsMinimized(true)}
          title="Minimize"
        >
          <Minimize2 className="w-5 h-5" />
        </button>
      </div>
      
      {/* Video Grid or Voice Call Display */}
      <div className="flex-1 p-4">
        {(isVideo || hasVideo || hasRemoteVideo) ? (
          <VideoGrid
            localStream={localStream}
            remoteStreams={remoteStreams}
            participants={activeCall.participants}
            isVideoOff={isVideoOff}
          />
        ) : (
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-white">
              <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-indigo-500 flex items-center justify-center">
                <span className="text-3xl font-bold">
                  {Object.keys(remoteStreams).length + 1}
                </span>
              </div>
              <p className="text-lg">{isVideo ? 'Video Call' : 'Voice Call'}</p>
              <p className="text-gray-400">{formatDuration(callDuration)}</p>
              {Object.keys(remoteStreams).length > 0 && (
                <p className="text-green-400 text-sm mt-2">Connected</p>
              )}
            </div>
          </div>
        )}
      </div>
      
      {/* Controls */}
      <div className="p-6 bg-black/30">
        <div className="flex items-center justify-center gap-4">
          {/* Mute Button */}
          <button
            className={`rounded-full w-14 h-14 flex items-center justify-center transition-colors ${
              isMuted 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-gray-600 hover:bg-gray-500 text-white'
            }`}
            onClick={toggleMute}
            title={isMuted ? 'Unmute' : 'Mute'}
          >
            {isMuted ? <MicOff className="w-6 h-6" /> : <Mic className="w-6 h-6" />}
          </button>
          
          {/* Video Toggle Button - Always show */}
          <button
            className={`rounded-full w-14 h-14 flex items-center justify-center transition-colors ${
              isVideoOff 
                ? 'bg-red-500 hover:bg-red-600 text-white' 
                : 'bg-gray-600 hover:bg-gray-500 text-white'
            }`}
            onClick={toggleVideo}
            title={isVideoOff ? 'Turn on camera' : 'Turn off camera'}
          >
            {isVideoOff ? <VideoOff className="w-6 h-6" /> : <Video className="w-6 h-6" />}
          </button>
          
          {/* Screen Share Button */}
          <button
            className={`rounded-full w-14 h-14 flex items-center justify-center transition-colors ${
              isScreenSharing 
                ? 'bg-green-500 hover:bg-green-600 text-white' 
                : 'bg-gray-600 hover:bg-gray-500 text-white'
            }`}
            onClick={toggleScreenShare}
            title={isScreenSharing ? 'Stop sharing' : 'Share screen'}
          >
            <Monitor className="w-6 h-6" />
          </button>
          
          {/* End Call Button */}
          <button
            className="rounded-full w-14 h-14 flex items-center justify-center bg-red-500 hover:bg-red-600 text-white transition-colors"
            onClick={endCall}
            title="End call"
          >
            <PhoneOff className="w-6 h-6" />
          </button>
        </div>
      </div>
    </div>
  );
}
