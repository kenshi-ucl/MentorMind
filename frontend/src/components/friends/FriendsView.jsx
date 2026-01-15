import { useState } from 'react';
import { Users, UserPlus, Bell } from 'lucide-react';
import { useFriends } from '../../context/FriendsContext';
import { useChat } from '../../context/ChatContext';
import { useCall } from '../../context/CallContext';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../ui';
import { Badge } from '../ui/Badge';
import { FriendsList } from './FriendsList';
import { FriendSearch } from './FriendSearch';
import { FriendRequests } from './FriendRequests';
import { DirectChatView } from '../chat/DirectChatView';
import audioService from '../../lib/audio';

export function FriendsView() {
  const { pendingCount } = useFriends();
  const { getOrCreateChat, openChat } = useChat();
  const { initiateCall } = useCall();
  const [selectedFriend, setSelectedFriend] = useState(null);
  const [activeTab, setActiveTab] = useState('friends');
  
  const handleChat = async (friend) => {
    const chat = await getOrCreateChat(friend.id);
    if (chat) {
      await openChat(chat.id, 'direct');
      setSelectedFriend(friend);
    }
  };
  
  const handleVoiceCall = async (friend) => {
    // Initialize audio on user interaction
    await audioService.init();
    
    const chat = await getOrCreateChat(friend.id);
    if (chat) {
      await initiateCall('voice', 'direct', chat.id);
    }
  };
  
  const handleVideoCall = async (friend) => {
    // Initialize audio on user interaction
    await audioService.init();
    
    const chat = await getOrCreateChat(friend.id);
    if (chat) {
      await initiateCall('video', 'direct', chat.id);
    }
  };
  
  const handleCloseChat = () => {
    setSelectedFriend(null);
  };
  
  if (selectedFriend) {
    return (
      <DirectChatView 
        friend={selectedFriend} 
        onClose={handleCloseChat}
        onVoiceCall={() => handleVoiceCall(selectedFriend)}
        onVideoCall={() => handleVideoCall(selectedFriend)}
      />
    );
  }
  
  return (
    <div className="h-full flex flex-col p-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Friends
        </h1>
        <p className="text-gray-500 dark:text-gray-400">
          Connect and learn together
        </p>
      </div>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="flex-1 flex flex-col">
        <TabsList className="mb-4">
          <TabsTrigger value="friends" className="flex items-center gap-2">
            <Users className="w-4 h-4" />
            Friends
          </TabsTrigger>
          <TabsTrigger value="search" className="flex items-center gap-2">
            <UserPlus className="w-4 h-4" />
            Add Friends
          </TabsTrigger>
          <TabsTrigger value="requests" className="flex items-center gap-2">
            <Bell className="w-4 h-4" />
            Requests
            <Badge count={pendingCount} />
          </TabsTrigger>
        </TabsList>
        
        <div className="flex-1 overflow-auto">
          <TabsContent value="friends" className="h-full">
            <FriendsList 
              onChat={handleChat}
              onVoiceCall={handleVoiceCall}
              onVideoCall={handleVideoCall}
            />
          </TabsContent>
          
          <TabsContent value="search" className="h-full">
            <FriendSearch />
          </TabsContent>
          
          <TabsContent value="requests" className="h-full">
            <FriendRequests />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
