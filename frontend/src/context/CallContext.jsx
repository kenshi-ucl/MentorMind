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
  const remoteStreamsRef = useRef({});

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

  useEffect(() => {
    remoteStreamsRef.current = remoteStreams;
  }, [remoteStreams]);

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

  const initiateCall = async (callType, contextType, contextId, retryAfterCleanup = true) => {
    let stream = null;
    
    try {
      // Clear any stale state from previous calls
      if (activeCallRef.current) {
        console.log('Clearing stale active call state before initiating new call');
        webrtcService.closeAllConnections();
        setActiveCall(null);
        setRemoteStreams({});
      }
      
      // Ensure websocket is connected
      if (!websocketService.connected) {
        await websocketService.connect(token);
      }

      // Get local media stream - this also sets webrtcService.localStream
      const isVideoCall = callType === 'video';
      stream = await webrtcService.getLocalStream(isVideoCall, true);
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
        // For group calls, we use a longer timeout
        const timeout = contextType === 'group' ? 60000 : CALL_TIMEOUT; // 60s for group, 30s for direct
        
        callTimeoutRef.current = setTimeout(async () => {
          const call = activeCallRef.current;
          if (!call) return;
          
          // Stop ringtone regardless
          stopRingtone();
          
          // Check if anyone has connected
          const hasConnections = Object.keys(remoteStreamsRef.current).length > 0;
          
          if (hasConnections) {
            // Someone is connected, just cancel ringing for others
            // Don't end the call
            console.log('Timeout reached but call is active with connections, canceling ringing only');
            try {
              await websocketService.cancelRinging(call.id);
            } catch (err) {
              console.error('Failed to cancel ringing:', err);
            }
          } else {
            // No one connected, end the call
            console.log('Timeout reached with no connections, ending call');
            endCall();
          }
        }, timeout);
        
        return { success: true, call: result.call };
      }
      
      // Clean up local stream if no call was created
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        setLocalStream(null);
      }
      return { success: false, error: 'Failed to initiate call' };
    } catch (err) {
      console.error('Failed to initiate call:', err);
      
      // Check if this is an "already active call" error and we should try cleanup
      const errorMessage = err.message || '';
      if (errorMessage.includes('already an active call') && retryAfterCleanup) {
        console.log('Got "already active call" error, attempting cleanup...');
        
        // Clean up current stream before retry
        if (stream) {
          stream.getTracks().forEach(track => track.stop());
          setLocalStream(null);
        }
        
        try {
          // Call the cleanup API endpoint
          const cleanupResponse = await fetch(
            `http://localhost:5000/api/calls/cleanup/${contextType}/${contextId}`,
            {
              method: 'POST',
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            }
          );
          
          if (cleanupResponse.ok) {
            const cleanupResult = await cleanupResponse.json();
            console.log('Cleanup result:', cleanupResult);
            
            if (cleanupResult.cleanedCount > 0) {
              // Retry the call initiation (but don't retry cleanup again)
              console.log('Retrying call initiation after cleanup...');
              return initiateCall(callType, contextType, contextId, false);
            }
          } else {
            console.error('Cleanup request failed:', cleanupResponse.status);
          }
        } catch (cleanupErr) {
          console.error('Failed to cleanup stale calls:', cleanupErr);
        }
      }
      
      // Clean up local stream on error
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
        setLocalStream(null);
      } else if (localStreamRef.current) {
        localStreamRef.current.getTracks().forEach(track => track.stop());
        setLocalStream(null);
      }
      
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
        // Use the updated call data from the server if available (includes current participants)
        const updatedCall = result.call || call;
        const acceptedCall = { ...updatedCall, status: 'active', isInitiator: false };
        setActiveCall(acceptedCall);
        setIncomingCall(null);
        
        // Play connected sound
        audioService.playConnected();
        
        // Start duration timer
        startDurationTimer();
        
        // Ensure local stream is set in webrtc service before creating offers
        console.log('Ensuring local stream is set before creating offers');
        webrtcService.setLocalStream(stream);
        
        // For group calls, we need to connect to ALL existing participants who have joined
        // For direct calls, just connect to the initiator
        console.log('All participants from server:', updatedCall.participants);
        
        // Get all participants who might be in the call (not declined/left)
        // We use the tie-breaker to determine who creates the offer
        let potentialParticipants = updatedCall.participants?.filter(p => 
          p.userId !== user?.id && 
          p.status !== 'declined' && 
          p.status !== 'left'
        ) || [];
        
        console.log('Potential participants to connect to:', potentialParticipants.map(p => ({ id: p.userId, name: p.userName, status: p.status })));
        
        // Always ensure the initiator is included (they should always be connected)
        const initiatorInList = potentialParticipants.some(p => p.userId === updatedCall.initiatorId);
        if (!initiatorInList && updatedCall.initiatorId !== user?.id) {
          console.log('Initiator not in list, adding them:', updatedCall.initiatorId);
          // Find initiator in all participants or create a minimal entry
          const initiator = updatedCall.participants?.find(p => p.userId === updatedCall.initiatorId);
          if (initiator) {
            potentialParticipants.push(initiator);
          } else {
            potentialParticipants.push({ userId: updatedCall.initiatorId, userName: updatedCall.initiatorName });
          }
        }
        
        console.log('Final participants to connect to:', potentialParticipants.map(p => p.userId));
        
        // Create offers for participants where we should be the offerer
        // To avoid "glare" (both sides creating offers simultaneously), we use a
        // deterministic tie-breaker: the user with the "higher" ID creates the offer
        for (const participant of potentialParticipants) {
          const shouldCreateOffer = user?.id > participant.userId;
          
          if (shouldCreateOffer) {
            console.log('We have higher ID, creating offer for participant:', participant.userId);
            try {
              const offer = await webrtcService.createOffer(
                participant.userId,
                (userId, candidate) => {
                  console.log('Sending ICE candidate to:', userId);
                  websocketService.sendIceCandidate(call.id, userId, candidate);
                }
              );
              
              console.log('Sending offer to participant:', participant.userId);
              await websocketService.sendOffer(call.id, participant.userId, offer);
            } catch (err) {
              console.error('Failed to create offer for participant:', participant.userId, err);
            }
          } else {
            console.log('Participant has higher ID, they will send us an offer:', participant.userId);
          }
        }
        
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
      const result = await websocketService.declineCall(call.id);
      console.log('Decline call result:', result);
    } catch (err) {
      console.error('Failed to decline call:', err);
    }
    
    // Always clear incoming call state after declining
    setIncomingCall(null);
    
    // Clean up any local stream that might have been created
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
      setLocalStream(null);
    }
  };

  const endCall = async () => {
    const call = activeCallRef.current;
    if (!call) return;
    
    stopRingtone();
    clearTimeout(callTimeoutRef.current);
    clearInterval(durationIntervalRef.current);
    
    try {
      const result = await websocketService.endCall(call.id);
      console.log('End call result:', result);
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
        const existingVideoTracks = currentStream?.getVideoTracks() || [];
        const hasEnabledVideoTrack = existingVideoTracks.some(t => t.readyState === 'live');
        
        console.log('toggleVideo ON: existingVideoTracks:', existingVideoTracks.length, 'hasEnabledVideoTrack:', hasEnabledVideoTrack);
        
        if (!hasEnabledVideoTrack) {
          // Get a new stream with both audio and video
          console.log('Getting new stream with video...');
          const stream = await webrtcService.getLocalStream(true, true);
          console.log('New stream obtained:', stream.getTracks().map(t => `${t.kind}:${t.enabled}:${t.readyState}`));
          
          // Update state first so UI can react
          setIsVideoOff(false);
          setLocalStream(stream);
          
          // Update all peer connections with the new stream
          const needsRenegotiation = await webrtcService.updateLocalStream(stream);
          
          // If we added new tracks, we need to renegotiate
          if (needsRenegotiation && call) {
            console.log('Renegotiating after adding video track');
            // Send renegotiation offers to all connected peers
            const peerIds = Array.from(webrtcService.peerConnections.keys());
            for (const peerId of peerIds) {
              try {
                const offer = await webrtcService.renegotiate(peerId);
                if (offer) {
                  console.log('Sending renegotiation offer to:', peerId);
                  await websocketService.sendOffer(call.id, peerId, offer);
                }
              } catch (err) {
                console.error('Failed to renegotiate with:', peerId, err);
              }
            }
          }
        } else {
          // Just enable existing video track
          console.log('Enabling existing video track');
          webrtcService.toggleVideo(false);
          setIsVideoOff(false);
        }
      } else {
        // Turn off video - just disable the track, don't remove it
        console.log('toggleVideo OFF: disabling video track');
        webrtcService.toggleVideo(true);
        setIsVideoOff(true);
      }
      
      if (call) {
        const newVideoOffState = !isVideoOff;
        console.log('Sending media state update, isVideoOff:', newVideoOffState);
        await websocketService.updateMediaState(call.id, { isVideoOff: newVideoOffState });
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
      
      // If we already have an active call, ignore the incoming call
      // (user is already in a call)
      if (activeCallRef.current) {
        console.log('Already in a call, ignoring incoming call');
        return;
      }
      
      // If we already have an incoming call from the same call ID, ignore
      if (incomingCallRef.current?.id === call.id) {
        console.log('Already have this incoming call, ignoring duplicate');
        return;
      }
      
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
        // Update participants list
        setActiveCall(prev => {
          if (!prev) return prev;
          const updatedParticipants = prev.participants?.map(p => 
            p.userId === data.userId ? { ...p, status: 'joined' } : p
          ) || [];
          
          // For group calls, transition to active when first person joins
          // For direct calls, also transition to active
          const newStatus = prev.status === 'ringing' ? 'active' : prev.status;
          
          return { ...prev, participants: updatedParticipants, status: newStatus };
        });
        
        // Only stop ringtone and start timer for the initiator on first accept
        if (call.isInitiator && call.status === 'ringing') {
          stopRingtone();
          clearTimeout(callTimeoutRef.current);
          
          // Play connected sound
          audioService.playConnected();
          
          // Start duration timer for the initiator
          startDurationTimer();
        }
        
        console.log('Call is now active, participant joined:', data.userId);
        
        // For the initiator, we need to establish connection with the new participant
        // Use tie-breaker: higher ID creates the offer
        if (data.userId !== user?.id) {
          const existingPc = webrtcService.getPeerConnection(data.userId);
          if (!existingPc) {
            const shouldCreateOffer = user?.id > data.userId;
            
            if (shouldCreateOffer) {
              console.log('We have higher ID, creating offer for accepted participant:', data.userId);
              
              const currentStream = localStreamRef.current;
              if (currentStream) {
                webrtcService.setLocalStream(currentStream);
                
                try {
                  const offer = await webrtcService.createOffer(
                    data.userId,
                    (userId, candidate) => {
                      console.log('Sending ICE candidate to accepted participant:', userId);
                      websocketService.sendIceCandidate(call.id, userId, candidate);
                    }
                  );
                  
                  console.log('Sending offer to accepted participant:', data.userId);
                  await websocketService.sendOffer(call.id, data.userId, offer);
                } catch (err) {
                  console.error('Failed to create offer for accepted participant:', data.userId, err);
                }
              }
            } else {
              console.log('Accepted participant has higher ID, waiting for their offer:', data.userId);
            }
          } else {
            console.log('Already have connection to accepted participant:', data.userId);
          }
        }
      }
    };

    // Handle when a new participant joins a group call (for existing participants)
    const handleParticipantJoined = async (data) => {
      console.log('Participant joined event received:', data);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId && data.userId !== user?.id) {
        // Update participants list
        setActiveCall(prev => {
          if (!prev) return prev;
          const updatedParticipants = prev.participants?.map(p => 
            p.userId === data.userId ? { ...p, status: 'joined' } : p
          ) || [];
          return { ...prev, participants: updatedParticipants };
        });
        
        console.log('New participant joined group call:', data.userId, data.userName);
        
        // Check if we already have a connection to this user
        const existingPc = webrtcService.getPeerConnection(data.userId);
        if (existingPc) {
          console.log('Already have connection to participant:', data.userId, 'state:', existingPc.connectionState);
        } else {
          // We don't have a connection yet - we should create one!
          // In a mesh topology, existing participants should also initiate connections
          // to new joiners to ensure full connectivity
          
          // To avoid "glare" (both sides creating offers simultaneously), we use a
          // deterministic tie-breaker: the user with the "higher" ID creates the offer
          const shouldCreateOffer = user?.id > data.userId;
          
          if (shouldCreateOffer) {
            console.log('We have higher ID, creating offer to new participant:', data.userId);
            
            // Ensure local stream is set
            const currentStream = localStreamRef.current;
            if (currentStream) {
              webrtcService.setLocalStream(currentStream);
              
              try {
                const offer = await webrtcService.createOffer(
                  data.userId,
                  (userId, candidate) => {
                    console.log('Sending ICE candidate to new participant:', userId);
                    websocketService.sendIceCandidate(call.id, userId, candidate);
                  }
                );
                
                console.log('Sending offer to new participant:', data.userId);
                await websocketService.sendOffer(call.id, data.userId, offer);
              } catch (err) {
                console.error('Failed to create offer for new participant:', data.userId, err);
              }
            } else {
              console.warn('No local stream available to create offer for new participant');
            }
          } else {
            console.log('New participant has higher ID, waiting for their offer:', data.userId);
          }
        }
      }
    };

    // Handle when a participant leaves a group call
    const handleParticipantLeft = (data) => {
      console.log('Participant left event received:', data);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId && data.userId !== user?.id) {
        // Close the peer connection for this user
        webrtcService.closePeerConnection(data.userId);
        
        // Remove their stream from state
        setRemoteStreams(prev => {
          const updated = { ...prev };
          delete updated[data.userId];
          return updated;
        });
        
        // Update participants list
        setActiveCall(prev => {
          if (!prev) return prev;
          const updatedParticipants = prev.participants?.map(p => 
            p.userId === data.userId ? { ...p, status: 'left' } : p
          ) || [];
          return { ...prev, participants: updatedParticipants };
        });
        
        console.log('Participant left group call:', data.userId, data.userName);
      }
    };

    const handleDeclined = (data) => {
      console.log('Call declined:', data);
      const call = activeCallRef.current;
      const incoming = incomingCallRef.current;
      
      // This event is only sent when the call actually ends (direct call declined or all group members declined)
      if (call?.id === data.callId) {
        stopRingtone();
        audioService.playEnded();
        
        clearTimeout(callTimeoutRef.current);
        clearInterval(durationIntervalRef.current);
        webrtcService.closeAllConnections();
        
        // Stop local stream
        if (localStreamRef.current) {
          localStreamRef.current.getTracks().forEach(track => track.stop());
        }
        
        setActiveCall(null);
        setLocalStream(null);
        setRemoteStreams({});
        setCallDuration(0);
        setIsMinimized(false);
        setIsMuted(false);
        setIsVideoOff(true);
        setIsScreenSharing(false);
        
        // Show notification to user
        if ('Notification' in window && Notification.permission === 'granted') {
          new Notification('Call Declined', {
            body: `${data.userName || 'User'} declined the call`,
            icon: '/logo.svg'
          });
        }
      }
      
      // Also handle if this was an incoming call that got declined/ended
      if (incoming?.id === data.callId) {
        stopRingtone();
        clearTimeout(callTimeoutRef.current);
        setIncomingCall(null);
      }
    };

    // Handle when a specific participant declines (for group calls, doesn't end the call)
    const handleParticipantDeclined = (data) => {
      console.log('Participant declined:', data);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        // Update participants list to show they declined
        setActiveCall(prev => {
          if (!prev) return prev;
          const updatedParticipants = prev.participants?.map(p => 
            p.userId === data.userId ? { ...p, status: 'declined' } : p
          ) || [];
          return { ...prev, participants: updatedParticipants };
        });
        
        console.log('Participant declined group call:', data.userId, data.userName);
      }
    };

    const handleEnded = (data) => {
      console.log('Call ended:', data);
      const call = activeCallRef.current;
      const incoming = incomingCallRef.current;
      
      // Handle active call ending
      if (call?.id === data.callId) {
        stopRingtone();
        clearInterval(durationIntervalRef.current);
        clearTimeout(callTimeoutRef.current);
        audioService.playEnded();
        webrtcService.closeAllConnections();
        
        // Stop local stream
        if (localStreamRef.current) {
          localStreamRef.current.getTracks().forEach(track => track.stop());
        }
        
        setActiveCall(null);
        setLocalStream(null);
        setRemoteStreams({});
        setCallDuration(0);
        setIsMinimized(false);
        setIsMuted(false);
        setIsVideoOff(true);
        setIsScreenSharing(false);
      }
      
      // Handle incoming call ending (e.g., caller hung up before we answered)
      if (incoming?.id === data.callId) {
        stopRingtone();
        clearTimeout(callTimeoutRef.current);
        setIncomingCall(null);
      }
    };

    // Handle offer from the receiver (when we are the initiator) or renegotiation
    const handleOffer = async (data) => {
      console.log('Received offer from:', data.fromUserId);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        // Check if this is a renegotiation (connection already exists and is stable)
        const existingPc = webrtcService.getPeerConnection(data.fromUserId);
        const isRenegotiation = existingPc && 
          (existingPc.connectionState === 'connected' || existingPc.signalingState === 'stable');
        
        console.log('Offer handling - isRenegotiation:', isRenegotiation, 
          'connectionState:', existingPc?.connectionState, 
          'signalingState:', existingPc?.signalingState);
        
        if (isRenegotiation) {
          console.log('This is a renegotiation offer');
          try {
            const answer = await webrtcService.handleRenegotiationOffer(data.fromUserId, data.offer);
            if (answer) {
              console.log('Sending renegotiation answer to:', data.fromUserId);
              await websocketService.sendAnswer(data.callId, data.fromUserId, answer);
            }
          } catch (err) {
            console.error('Failed to handle renegotiation offer:', err);
          }
          return;
        }
        
        // Initial offer - receiving an offer means the call was accepted
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

    // Handle answer from the initiator (when we are the receiver) or renegotiation answer
    const handleAnswer = async (data) => {
      console.log('Received answer from:', data.fromUserId);
      const call = activeCallRef.current;
      
      if (call?.id === data.callId) {
        try {
          const pc = webrtcService.getPeerConnection(data.fromUserId);
          
          if (!pc) {
            console.error('No peer connection found for:', data.fromUserId);
            return;
          }
          
          console.log('Peer connection signaling state:', pc.signalingState);
          
          // If we're in have-local-offer state, we can set the remote description
          if (pc.signalingState === 'have-local-offer') {
            console.log('Setting remote description (answer)');
            await pc.setRemoteDescription(new RTCSessionDescription(data.answer));
            console.log('Answer processed successfully, new signaling state:', pc.signalingState);
          } else {
            console.warn('Unexpected signaling state for answer:', pc.signalingState);
          }
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
        
        // Force re-render of remote streams when media state changes
        // This helps update the UI when remote user toggles video
        setRemoteStreams(prev => ({ ...prev }));
      }
    };

    // Set up remote stream handler
    webrtcService.onRemoteStream = (userId, stream) => {
      console.log('Remote stream received from:', userId);
      console.log('Stream tracks:', stream?.getTracks().map(t => `${t.kind}:${t.enabled}:${t.readyState}`));
      
      const audioTracks = stream?.getAudioTracks();
      const videoTracks = stream?.getVideoTracks();
      console.log('Audio tracks:', audioTracks?.length, audioTracks?.map(t => `enabled:${t.enabled}, muted:${t.muted}`));
      console.log('Video tracks:', videoTracks?.length, videoTracks?.map(t => `enabled:${t.enabled}, muted:${t.muted}`));
      
      // Update remote streams state
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
    const unsubParticipantDeclined = websocketService.on('call:participant-declined', handleParticipantDeclined);
    const unsubEnded = websocketService.on('call:ended', handleEnded);
    const unsubOffer = websocketService.on('call:offer', handleOffer);
    const unsubAnswer = websocketService.on('call:answer', handleAnswer);
    const unsubIce = websocketService.on('call:ice-candidate', handleIceCandidate);
    const unsubMedia = websocketService.on('call:media-state', handleMediaState);
    const unsubParticipantJoined = websocketService.on('call:participant-joined', handleParticipantJoined);
    const unsubParticipantLeft = websocketService.on('call:participant-left', handleParticipantLeft);

    return () => {
      unsubRing();
      unsubAccepted();
      unsubDeclined();
      unsubParticipantDeclined();
      unsubEnded();
      unsubOffer();
      unsubAnswer();
      unsubIce();
      unsubMedia();
      unsubParticipantJoined();
      unsubParticipantLeft();
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
