import { useEffect, useRef, useState } from 'react';
import { Mic, MicOff, Video, VideoOff, Monitor, PhoneOff, Minimize2 } from 'lucide-react';
import { useCall } from '../../context/CallContext';
import { useAuth } from '../../context/AuthContext';
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
  
  const { user } = useAuth();
  
  const localVideoRef = useRef(null);
  const remoteAudioRefs = useRef({});
  const [hasRemoteVideo, setHasRemoteVideo] = useState(false);
  
  // Attach local stream to video element
  useEffect(() => {
    if (localVideoRef.current && localStream) {
      localVideoRef.current.srcObject = localStream;
    }
  }, [localStream]);
  
  // Check for remote video tracks
  useEffect(() => {
    const checkRemoteVideo = () => {
      const hasVideo = Object.values(remoteStreams).some(stream => {
        const videoTracks = stream?.getVideoTracks() || [];
        return videoTracks.some(track => track.enabled && track.readyState === 'live');
      });
      console.log('Has remote video:', hasVideo);
      setHasRemoteVideo(hasVideo);
    };
    
    checkRemoteVideo();
    
    // Listen for track changes on all remote streams
    const cleanupFns = [];
    Object.entries(remoteStreams).forEach(([userId, stream]) => {
      if (stream) {
        const handleChange = () => {
          console.log('Remote stream track change for:', userId);
          checkRemoteVideo();
        };
        
        stream.addEventListener('addtrack', handleChange);
        stream.addEventListener('removetrack', handleChange);
        
        // Also listen to individual track events
        stream.getTracks().forEach(track => {
          track.onmute = handleChange;
          track.onunmute = handleChange;
          track.onended = handleChange;
        });
        
        cleanupFns.push(() => {
          stream.removeEventListener('addtrack', handleChange);
          stream.removeEventListener('removetrack', handleChange);
          stream.getTracks().forEach(track => {
            track.onmute = null;
            track.onunmute = null;
            track.onended = null;
          });
        });
      }
    });
    
    return () => {
      cleanupFns.forEach(fn => fn());
    };
  }, [remoteStreams]);
  
  // Play remote audio streams
  useEffect(() => {
    console.log('Remote streams updated:', Object.keys(remoteStreams));
    
    Object.entries(remoteStreams).forEach(([userId, stream]) => {
      if (stream) {
        const tracks = stream.getTracks();
        const audioTracks = stream.getAudioTracks();
        console.log('Processing stream for user:', userId);
        console.log('Stream tracks:', tracks.map(t => `${t.kind}:${t.enabled}:${t.readyState}`));
        console.log('Audio tracks:', audioTracks.length, audioTracks.map(t => `id:${t.id},enabled:${t.enabled},muted:${t.muted},readyState:${t.readyState}`));
        
        // Skip if no audio tracks
        if (audioTracks.length === 0) {
          console.log('No audio tracks for user:', userId);
          return;
        }
        
        // Verify audio tracks are enabled and live
        const hasLiveAudio = audioTracks.some(t => t.enabled && t.readyState === 'live');
        if (!hasLiveAudio) {
          console.warn('Audio tracks exist but none are enabled and live for user:', userId);
        }
        
        // Create or get audio element for this user
        let audioEl = remoteAudioRefs.current[userId];
        
        if (!audioEl) {
          audioEl = document.createElement('audio');
          audioEl.autoplay = true;
          audioEl.playsInline = true;
          audioEl.muted = false; // CRITICAL: Don't mute remote audio
          audioEl.id = `remote-audio-${userId}`;
          audioEl.volume = 1.0;
          audioEl.controls = false; // Hide controls
          
          // Add event listeners for debugging
          audioEl.onloadedmetadata = () => {
            console.log('Audio metadata loaded for:', userId);
          };
          audioEl.oncanplay = () => {
            console.log('Audio can play for:', userId);
          };
          audioEl.onplay = () => {
            console.log('Audio play event fired for:', userId);
          };
          audioEl.onpause = () => {
            console.log('Audio pause event fired for:', userId);
          };
          audioEl.onerror = (e) => {
            console.error('Audio error for:', userId, e);
          };
          
          // Add to DOM
          document.body.appendChild(audioEl);
          remoteAudioRefs.current[userId] = audioEl;
          console.log('Created audio element for user:', userId);
        }
        
        // Always update srcObject to ensure latest tracks are used
        console.log('Updating audio element srcObject for:', userId);
        audioEl.srcObject = stream;
        
        // Force load
        try {
          audioEl.load();
        } catch (e) {
          console.warn('Audio load() failed:', e);
        }
        
        console.log('Audio element state:', {
          userId,
          srcObject: !!audioEl.srcObject,
          srcObjectTracks: audioEl.srcObject?.getTracks().length,
          paused: audioEl.paused,
          muted: audioEl.muted,
          volume: audioEl.volume,
          readyState: audioEl.readyState,
          networkState: audioEl.networkState,
          currentTime: audioEl.currentTime,
          duration: audioEl.duration
        });
        
        // Try to play
        const playAudio = async () => {
          try {
            // Ensure not muted
            audioEl.muted = false;
            audioEl.volume = 1.0;
            
            await audioEl.play();
            console.log('✓ Audio playing for user:', userId, {
              paused: audioEl.paused,
              muted: audioEl.muted,
              volume: audioEl.volume,
              currentTime: audioEl.currentTime,
              readyState: audioEl.readyState
            });
            
            // Double-check after a short delay
            setTimeout(() => {
              console.log('Audio status check after 500ms:', {
                userId,
                paused: audioEl.paused,
                muted: audioEl.muted,
                volume: audioEl.volume,
                currentTime: audioEl.currentTime,
                srcObject: !!audioEl.srcObject,
                audioTracks: audioEl.srcObject?.getAudioTracks().map(t => ({
                  id: t.id,
                  enabled: t.enabled,
                  muted: t.muted,
                  readyState: t.readyState
                }))
              });
            }, 500);
          } catch (err) {
            console.error('✗ Failed to play audio for user:', userId, err);
            
            // If autoplay is blocked, retry on user interaction
            if (err.name === 'NotAllowedError' || err.name === 'NotSupportedError') {
              console.log('Autoplay blocked, will retry on user interaction');
              const retryPlay = async () => {
                try {
                  audioEl.muted = false;
                  audioEl.volume = 1.0;
                  await audioEl.play();
                  console.log('✓ Audio playing after user interaction:', userId);
                } catch (e) {
                  console.error('✗ Retry play failed:', e);
                }
                document.removeEventListener('click', retryPlay);
                document.removeEventListener('touchstart', retryPlay);
              };
              document.addEventListener('click', retryPlay, { once: true });
              document.addEventListener('touchstart', retryPlay, { once: true });
            }
          }
        };
        
        // Small delay to ensure stream is ready
        setTimeout(playAudio, 100);
      }
    });
    
    // Cleanup removed streams
    Object.keys(remoteAudioRefs.current).forEach(userId => {
      if (!remoteStreams[userId]) {
        const audioEl = remoteAudioRefs.current[userId];
        if (audioEl) {
          audioEl.pause();
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
  const hasLocalVideo = localStream?.getVideoTracks().some(t => t.enabled) && !isVideoOff;
  const isRinging = activeCall.status === 'ringing';
  const isActive = activeCall.status === 'active';
  
  return (
    <div className="fixed inset-0 z-50 bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between p-4 bg-black/30">
        <div className="text-white">
          <h2 className="font-semibold">
            {activeCall.contextType === 'direct' ? 'Call' : 'Group Call'}
          </h2>
          <p className="text-sm text-gray-300">
            {isRinging ? 'Calling...' : formatDuration(callDuration)}
            {isActive && activeCall.contextType === 'group' && (
              <span className="ml-2">
                • {Object.keys(remoteStreams).length + 1} participants
              </span>
            )}
          </p>
        </div>
        
        <button
          className="p-2 text-white hover:bg-white/10 rounded-lg transition-colors"
          onClick={() => setIsMinimized(true)}
          title="Minimize"
        >
          <Minimize2 className="w-5 h-5" />
        </button>
      </div>
      
      {/* Content Area */}
      <div className="flex-1 min-h-0 overflow-hidden">
        {isRinging ? (
          // Show "Calling..." UI when ringing
          <div className="h-full flex items-center justify-center">
            <div className="text-center text-white">
              {/* Show local video preview if video call */}
              {isVideo && localStream && (
                <div className="w-48 h-48 mx-auto mb-6 rounded-full overflow-hidden bg-gray-800">
                  <video
                    ref={(el) => {
                      if (el && localStream) {
                        el.srcObject = localStream;
                      }
                    }}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover transform scale-x-[-1]"
                  />
                </div>
              )}
              
              {/* Avatar for voice call */}
              {!isVideo && (
                <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-indigo-500 flex items-center justify-center">
                  <span className="text-3xl font-bold">
                    {user?.name?.charAt(0).toUpperCase() || 'U'}
                  </span>
                </div>
              )}
              
              <p className="text-2xl font-semibold mb-2">Calling...</p>
              <p className="text-gray-400">
                {activeCall.contextType === 'direct' 
                  ? 'Waiting for answer' 
                  : `Calling ${activeCall.participants?.filter(p => p.status === 'ringing').length || 0} group members`}
              </p>
              
              {/* Show who has joined for group calls */}
              {activeCall.contextType === 'group' && Object.keys(remoteStreams).length > 0 && (
                <p className="text-green-400 text-sm mt-2">
                  {Object.keys(remoteStreams).length} participant(s) joined
                </p>
              )}
              
              {/* Animated dots */}
              <div className="flex justify-center gap-2 mt-4">
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                <div className="w-2 h-2 bg-indigo-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
              </div>
            </div>
          </div>
        ) : isActive && (isVideo || hasLocalVideo || hasRemoteVideo) ? (
          // Show video grid when call is active and has video
          <VideoGrid
            localStream={localStream}
            remoteStreams={remoteStreams}
            participants={activeCall.participants}
            currentUserId={user?.id}
            isVideoOff={isVideoOff}
          />
        ) : (
          // Show voice call UI when active but no video
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
