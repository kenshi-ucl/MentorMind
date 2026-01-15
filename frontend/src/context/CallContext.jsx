import { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { useAuth } from './AuthContext';
import websocketService from '../lib/websocket';
import webrtcService from '../lib/webrtc';
import audioService from '../lib/audio';

const CallContext = createContext(null);

const CALL_TIMEOUT = 30000; // 30 seconds

export function CallProvider({ children }) {
  const { token, user, isAuthenticated } = useAuth();
  const [activeCall, setActiveCall] = useState(null);
  const [incomingCall, setIncomingCall] = useState(null);
  const [localStream, setLocalStream] = useState(null);
  const [remoteStreams, setRemoteStreams] = useState({});
  const [isMuted, setIsMuted] = useState(false);
  const [isVideoOff, setIsVideoOff] = useState(true);
  const [isScreenSharing, setIsScreenSharing] = useState(false);
  const [callDuration, setCallDuration] = useState(0);
  const [isMinimized, setIsMinimized] = useState(false);
  
  const callTimeoutRef = useRef(null);
  const durationIntervalRef = useRef(null);
  const activeCallRef = useRef(null);
  const incomingCallRef = useRef(null);
  const localStreamRef = useRef(null);

  // Keep refs in sync
  useEffect(() => {
    activeCallRef.current = activeCall;
  }, [activeCall]);

  useEffect(() => {
    incomingCallRef.current = incomingCall;
  }, [incomingCall]);

  useEffect(() => {
    localStreamRef.current = localStream;
  }, [localStream]);

  const playRingtone = useCallback(() => {
    audioService.playRingtone();
  }, []);

  const stopRingtone = useCallback(() => {
    audioService.stopRingtone();
  }, []);

  const startDurationTimer = useCallback(() => {
    // Clear any existing timer
    if (durationIntervalRef.current) {
      clearInterval(durationIntervalRef.current);
    }
    setCallDuration(0);
    durationIntervalRef.current = setInterval(() => {
      setCallDuration(prev => prev + 1);
    }, 1000);
  }, []);

  const initiateCall = async (callType, contextType, contextId) => {
    try {
      // Ensure websocket is connected
      if (!websocketService.connected) {
        await websocketService.connect(token);
      }

      // Get local media stream - this also sets webrtcService.localStream
      const isVideoCall = callType === 'video';
      const stream = await webrtcService.getLocalStream(isVideoCall, true);
      setLocalStream(stream);
      setIsVideoOff(!isVideoCall);
      
      console.log('Local stream obtained for initiator:', stream.getTracks().map(t => `${t.kind}:${t.enabled}`));

      // Initiate call via WebSocket
      const result = await websocketService.initiateCall(callType, contextType, contextId);
      
      console.log('Call initiated:', result);
      
      if (result?.call) {
        setActiveCall({ ...result.call, isInitiator: true });
        
        // Play outgoing ring tone
        audioService.playRingtone();
        
        // Set timeout for unanswered call
        callTimeoutRef.current = setTimeout(() => {
          const call = activeCallRef.current;
          if (call?.status === 'ringing') {
            endCall();
          }
        }, CALL_TIMEOUT);
        
        return { success: true, call: result.call };
      }
      
      return { success: false, error: 'Failed to initiate call' };
    } catch (err) {
      console.error('Failed to initiate call:', err);
      return { success: false, error: err.message };
    }
  };

  const acceptCall = async () => {
    const call = incomingCallRef.current;
    if (!call) return { success: false };
    
    try {
      stopRingtone();
      clearTimeout(callTimeoutRef.current);
      
      // Ensure websocket is connected
      if (!websocketService.connected) {
        await websocketService.connect(token);
      }

      // Get local media stream - this also sets webrtcService.localStream
      const isVideoCall = call.callType === 'video';
      const stream = await webrtcService.getLocalStream(isVideoCall, true);
      setLocalStream(stream);
      setIsVideoOff(!isVideoCall);
      
      console.log('Local stream obtained for receiver:', stream.getTracks().map(t => `${t.kind}:${t.enabled}`));

      // Accept call via WebSocket
      const result = await websocketService.acceptCall(call.id);
      
      console.log('Call accepted:', result);
      
      if (result?.success) {
        const acceptedCall = { ...call, status: 'active', isInitiator: false };
        setActiveCall(acceptedCall);
        setIncomingCall(null);
        
        // Play connected sound
        audioService.playConnected();
        
        // Start duration timer
        startDurationTimer();
        
        // Ensure local stream is set in webrtc service before creating offer
        console.log('Ensuring local stream is set before creating offer');
        webrtcService.setLocalStream(stream);
        
        // The receiver creates an offer and sends it to the initiator
        console.log('Creating offer for initiator:', call.initiatorId);
        const offer = await webrtcService.createOffer(
          call.initiatorId,
          (userId, candidate) => {
            console.log('Sending ICE candidate to:', userId);
            websocketService.sendIceCandidate(call.id, userId, candidate);
          }
        );
        
        console.log('Sending offer to initiator');
        await websocketService.sendOffer(call.id, call.initiatorId, offer);
        
        return { success: true };
      }
      
      return { success: false };
    } catch (err) {
      console.error('Failed to accept call:', err);
      return { success: false, error: err.message };
    }
  };

  const declineCall = async () => {
    const call = incomingCallRef.current;
    if (!call) return;
    
    stopRingtone();
    clearTimeout(callTimeoutRef.current);
    
    try {
      await websocketService.declineCall(call.id);
    } catch (err) {
      console.error('Failed to decline call:', err);
    }
    
    setIncomingCall(null);
  };

  const endCall = async () => {
    const call = activeCallRef.current;
    if (!call) return;
    
    stopRingtone();
    clearTimeout(callTimeoutRef.current);
    clearInterval(durationIntervalRef.current);
    
    try {
      await websocketService.endCall(call.id);
    } catch (err) {
      console.error('Failed to end call:', err);
    }
    
    // Play ended sound
    audioService.playEnded();
    
    webrtcService.closeAllConnections();
    
    setActiveCall(null);
    setLocalStream(null);
    setRemoteStreams({});
    setIsMuted(false);
    setIsVideoOff(true);
    setIsScreenSharing(false);
    setCallDuration(0);
    setIsMinimized(false);
  };

  const toggleMute = async () => {
    const newMuted = !isMuted;
    setIsMuted(newMuted);
    webrtcService.toggleAudio(newMuted);
    
    const call = activeCallRef.current;
    if (call) {
      try {
        await websocketService.updateMediaState(call.id, { isMuted: newMuted });
      } catch (err) {
        console.error('Failed to update media state:', err);
      }
    }
  };

  const toggleVideo = async () => {
    const call = activeCallRef.current;
    
    try {
      if (isVideoOff) {
        // Turn on video - need to get video stream if we don't have it
        const currentStream = localStreamRef.current;
        if (!currentStream?.getVideoTracks().length) {
          const stream = await webrtcService.getLocalStream(true, true);
          setLocalStream(stream);
        }
        webrtcService.toggleVideo(false);
        setIsVideoOff(false);
      } else {
        // Turn off video
        webrtcService.toggleVideo(true);
        setIsVideoOff(true);
      }
      
      if (call) {
        await websocketService.updateMediaState(call.id, { isVideoOff: !isVideoOff });
      }
    } catch (err) {
      console.error('Failed to toggle video:', err);
    }
  };

  const toggleScreenShare = async () => {
    const call = activeCallRef.current;
    
    try {
      if (isScreenSharing) {
        webrtcService.stopScreenShare();
        setIsScreenSharing(false);
      } else {
        await webrtcService.startScreenShare();
        setIsScreenSharing(true);
      }
      
      if (call) {
        await websocketService.updateMediaState(call.id, { 
          isScreenSharing: !isScreenSharing 
        });
      }
    } catch (err) {
      console.error('Failed to toggle screen share:', err);
    }
  };

  // Handle WebSocket call events
  useEffect(() => {
    if (!isAuthenticated) return;

    const handleRing = (call) => {
      console.log('Incoming call:', call);
      setIncomingCall(call);
      playRingtone();
      
      // Auto-decline after timeout
      callTimeoutRef.current = setTimeout(() => {
        const currentIncoming = incomingCallRef.current;
        if (currentIncoming?.id === call.id) {
          declineCall();
        }
      }, CALL_TIMEOUT);
    };

    const handleAccepted = async (data) => {
      console.log('Call accepted event received:', data);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        stopRingtone();
        clearTimeout(callTimeoutRef.current);
        
        // Play connected sound
        audioService.playConnected();
        
        // Start duration timer for the initiator
        startDurationTimer();
        
        setActiveCall(prev => ({ ...prev, status: 'active' }));
        
        console.log('Call is now active, waiting for offer from receiver');
      }
    };

    const handleDeclined = (data) => {
      console.log('Call declined:', data);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        stopRingtone();
        audioService.playEnded();
        
        clearTimeout(callTimeoutRef.current);
        clearInterval(durationIntervalRef.current);
        webrtcService.closeAllConnections();
        
        setActiveCall(null);
        setLocalStream(null);
        setRemoteStreams({});
        setCallDuration(0);
        setIsMinimized(false);
      }
    };

    const handleEnded = (data) => {
      console.log('Call ended:', data);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        stopRingtone();
        clearInterval(durationIntervalRef.current);
        audioService.playEnded();
        webrtcService.closeAllConnections();
        
        setActiveCall(null);
        setLocalStream(null);
        setRemoteStreams({});
        setCallDuration(0);
        setIsMinimized(false);
      }
    };

    // Handle offer from the receiver (when we are the initiator)
    const handleOffer = async (data) => {
      console.log('Received offer from:', data.fromUserId);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        // Receiving an offer means the call was accepted - stop ringtone and start timer
        // This is a fallback in case call:accepted event doesn't arrive
        if (call.status === 'ringing' || call.isInitiator) {
          console.log('Offer received - call is now active, stopping ringtone');
          stopRingtone();
          clearTimeout(callTimeoutRef.current);
          
          // Play connected sound if not already played
          audioService.playConnected();
          
          // Start duration timer if not already started
          if (!durationIntervalRef.current) {
            startDurationTimer();
          }
          
          // Update call status
          setActiveCall(prev => ({ ...prev, status: 'active' }));
        }
        
        try {
          // Ensure local stream is available in webrtc service
          // The initiator already has a local stream from initiateCall
          const currentStream = localStreamRef.current;
          if (currentStream) {
            console.log('Ensuring local stream is set in webrtc service');
            webrtcService.setLocalStream(currentStream);
          } else {
            console.warn('No local stream available when handling offer!');
          }
          
          // Handle the offer and create an answer
          const answer = await webrtcService.handleOffer(
            data.fromUserId,
            data.offer,
            (userId, candidate) => {
              console.log('Sending ICE candidate to:', userId);
              websocketService.sendIceCandidate(data.callId, userId, candidate);
            }
          );
          
          console.log('Sending answer to:', data.fromUserId);
          await websocketService.sendAnswer(data.callId, data.fromUserId, answer);
        } catch (err) {
          console.error('Failed to handle offer:', err);
        }
      }
    };

    // Handle answer from the initiator (when we are the receiver)
    const handleAnswer = async (data) => {
      console.log('Received answer from:', data.fromUserId);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        try {
          await webrtcService.handleAnswer(data.fromUserId, data.answer);
          console.log('Answer processed successfully');
        } catch (err) {
          console.error('Failed to handle answer:', err);
        }
      }
    };

    const handleIceCandidate = async (data) => {
      console.log('Received ICE candidate from:', data.fromUserId);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        try {
          await webrtcService.handleIceCandidate(data.fromUserId, data.candidate);
        } catch (err) {
          console.error('Failed to handle ICE candidate:', err);
        }
      }
    };

    const handleMediaState = (data) => {
      console.log('Media state update:', data);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        setActiveCall(prev => ({
          ...prev,
          participants: prev?.participants?.map(p => 
            p.userId === data.userId 
              ? { ...p, isMuted: data.isMuted, isVideoOff: data.isVideoOff, isScreenSharing: data.isScreenSharing }
              : p
          )
        }));
      }
    };

    // Set up remote stream handler
    webrtcService.onRemoteStream = (userId, stream) => {
      console.log('Remote stream received from:', userId);
      console.log('Stream tracks:', stream?.getTracks().map(t => `${t.kind}:${t.enabled}:${t.readyState}`));
      
      // Verify stream has audio tracks
      const audioTracks = stream?.getAudioTracks();
      console.log('Audio tracks:', audioTracks?.length, audioTracks?.map(t => `enabled:${t.enabled}, muted:${t.muted}`));
      
      setRemoteStreams(prev => {
        const updated = { ...prev, [userId]: stream };
        console.log('Updated remote streams:', Object.keys(updated));
        return updated;
      });
    };

    // Set up connection state change handler
    webrtcService.onConnectionStateChange = (userId, state) => {
      console.log('Connection state changed for', userId, ':', state);
      if (state === 'connected') {
        console.log('WebRTC connection established with:', userId);
      } else if (state === 'failed') {
        console.error('WebRTC connection failed with:', userId);
      }
    };

    const unsubRing = websocketService.on('call:ring', handleRing);
    const unsubAccepted = websocketService.on('call:accepted', handleAccepted);
    const unsubDeclined = websocketService.on('call:declined', handleDeclined);
    const unsubEnded = websocketService.on('call:ended', handleEnded);
    const unsubOffer = websocketService.on('call:offer', handleOffer);
    const unsubAnswer = websocketService.on('call:answer', handleAnswer);
    const unsubIce = websocketService.on('call:ice-candidate', handleIceCandidate);
    const unsubMedia = websocketService.on('call:media-state', handleMediaState);

    return () => {
      unsubRing();
      unsubAccepted();
      unsubDeclined();
      unsubEnded();
      unsubOffer();
      unsubAnswer();
      unsubIce();
      unsubMedia();
      clearTimeout(callTimeoutRef.current);
      clearInterval(durationIntervalRef.current);
      stopRingtone();
    };
  }, [isAuthenticated, playRingtone, stopRingtone, startDurationTimer]);

  // Request notification permission on mount
  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }
  }, []);

  const value = {
    activeCall,
    incomingCall,
    localStream,
    remoteStreams,
    isMuted,
    isVideoOff,
    isScreenSharing,
    callDuration,
    isMinimized,
    isInCall: !!activeCall,
    initiateCall,
    acceptCall,
    declineCall,
    endCall,
    toggleMute,
    toggleVideo,
    toggleScreenShare,
    setIsMinimized
  };

  return (
    <CallContext.Provider value={value}>
      {children}
    </CallContext.Provider>
  );
}

export function useCall() {
  const context = useContext(CallContext);
  if (!context) {
    throw new Error('useCall must be used within a CallProvider');
  }
  return context;
}

export default CallContext;
