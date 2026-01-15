import { Phone, PhoneOff, Video } from 'lucide-react';
import { useCall } from '../../context/CallContext';
import { Avatar } from '../ui/Avatar';
import audioService from '../../lib/audio';

export function IncomingCall() {
  const { incomingCall, acceptCall, declineCall } = useCall();
  
  if (!incomingCall) return null;
  
  const isVideo = incomingCall.callType === 'video';
  
  const handleAccept = async () => {
    // Initialize audio on user interaction (required by browser autoplay policy)
    await audioService.init();
    acceptCall();
  };
  
  const handleDecline = async () => {
    // Initialize audio on user interaction
    await audioService.init();
    declineCall();
  };
  
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70">
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl max-w-sm w-full mx-4 text-center animate-pulse-slow">
        <div className="mb-6">
          <div className="relative inline-block">
            <Avatar 
              name={incomingCall.initiatorName || 'Unknown'} 
              size="xl" 
              className="mx-auto mb-4"
            />
            <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-green-500 rounded-full flex items-center justify-center animate-ping">
              {isVideo ? (
                <Video className="w-3 h-3 text-white" />
              ) : (
                <Phone className="w-3 h-3 text-white" />
              )}
            </div>
          </div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mt-4">
            {incomingCall.initiatorName || 'Unknown Caller'}
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Incoming {isVideo ? 'video' : 'voice'} call...
          </p>
        </div>
        
        <div className="flex justify-center gap-8">
          {/* Decline Button */}
          <div className="text-center">
            <button
              className="w-16 h-16 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center transition-colors shadow-lg"
              onClick={handleDecline}
            >
              <PhoneOff className="w-7 h-7" />
            </button>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Decline</p>
          </div>
          
          {/* Accept Button */}
          <div className="text-center">
            <button
              className="w-16 h-16 rounded-full bg-green-500 hover:bg-green-600 text-white flex items-center justify-center transition-colors shadow-lg animate-bounce"
              onClick={handleAccept}
            >
              {isVideo ? (
                <Video className="w-7 h-7" />
              ) : (
                <Phone className="w-7 h-7" />
              )}
            </button>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Accept</p>
          </div>
        </div>
      </div>
    </div>
  );
}
