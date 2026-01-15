# Design Document: Friends & Communication System

## Overview

This document describes the technical design for implementing a comprehensive Friends & Communication system in MentorMind. The system enables users to connect with other learners, engage in real-time messaging, and conduct voice/video calls with a persistent call bubble for navigation during active calls.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                       │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ FriendsView  │ │  DirectChat  │ │  CallInterface│             │
│  │  Component   │ │  Component   │ │   Component   │             │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘             │
│         │                │                │                      │
│  ┌──────┴────────────────┴────────────────┴──────┐              │
│  │           FriendsContext Provider             │              │
│  │    (friends, requests, chats, calls state)    │              │
│  └──────────────────────┬────────────────────────┘              │
│                         │                                        │
│  ┌──────────────────────┴────────────────────────┐              │
│  │         WebSocketService + WebRTCService       │              │
│  └──────────────────────┬────────────────────────┘              │
└─────────────────────────┼────────────────────────────────────────┘
                          │ WebSocket + HTTP
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (Flask)                             │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    API Routes                            │    │
│  │  /friends  │  /chat  │  /groups  │  /calls  │  /presence │    │
│  └──────┬─────────┬─────────┬───────────┬──────────┬───────┘    │
│         │         │         │           │          │             │
│  ┌──────┴─────────┴─────────┴───────────┴──────────┴───────┐    │
│  │                   Service Layer                          │    │
│  │  FriendService │ ChatService │ GroupService │ CallService│    │
│  └──────────────────────────┬───────────────────────────────┘    │
│                             │                                    │
│  ┌──────────────────────────┴───────────────────────────────┐    │
│  │              Flask-SocketIO (Signaling Server)            │    │
│  └───────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Models

### Friend Model

```python
class Friend(db.Model):
    __tablename__ = 'friends'
    
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    friend_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'friend_id', name='unique_friendship'),
    )
```

### FriendRequest Model
```python
class FriendRequest(db.Model):
    __tablename__ = 'friend_requests'
    
    id = db.Column(db.String(36), primary_key=True)
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
```

### DirectChat Model
```python
class DirectChat(db.Model):
    __tablename__ = 'direct_chats'
    
    id = db.Column(db.String(36), primary_key=True)
    user1_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    user2_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_message_at = db.Column(db.DateTime)
```

### Message Model
```python
class Message(db.Model):
    __tablename__ = 'messages'
    
    id = db.Column(db.String(36), primary_key=True)
    chat_id = db.Column(db.String(36), nullable=False)
    chat_type = db.Column(db.String(20), nullable=False)  # 'direct' or 'group'
    sender_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    read_by = db.Column(db.JSON, default=list)
```

### GroupLearning Model
```python
class GroupLearning(db.Model):
    __tablename__ = 'group_learning'
    
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    creator_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity_at = db.Column(db.DateTime)
```

### GroupMember Model
```python
class GroupMember(db.Model):
    __tablename__ = 'group_members'
    
    id = db.Column(db.String(36), primary_key=True)
    group_id = db.Column(db.String(36), db.ForeignKey('group_learning.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), default='member')  # creator, member
    status = db.Column(db.String(20), default='pending')  # pending, active, left
    joined_at = db.Column(db.DateTime)
```

### Call Model
```python
class Call(db.Model):
    __tablename__ = 'calls'
    
    id = db.Column(db.String(36), primary_key=True)
    call_type = db.Column(db.String(20), nullable=False)  # 'voice' or 'video'
    context_type = db.Column(db.String(20), nullable=False)  # 'direct' or 'group'
    context_id = db.Column(db.String(36), nullable=False)
    initiator_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='ringing')  # ringing, active, ended
    started_at = db.Column(db.DateTime)
    ended_at = db.Column(db.DateTime)
```

### CallParticipant Model
```python
class CallParticipant(db.Model):
    __tablename__ = 'call_participants'
    
    id = db.Column(db.String(36), primary_key=True)
    call_id = db.Column(db.String(36), db.ForeignKey('calls.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='invited')  # invited, joined, left, declined
    is_muted = db.Column(db.Boolean, default=False)
    is_video_enabled = db.Column(db.Boolean, default=True)
    joined_at = db.Column(db.DateTime)
    left_at = db.Column(db.DateTime)
```

### UserPresence Model
```python
class UserPresence(db.Model):
    __tablename__ = 'user_presence'
    
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    socket_id = db.Column(db.String(255))
```

## API Endpoints

### Friends API (`/api/friends`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/friends` | Get user's friend list with online status |
| GET | `/api/friends/search?q={query}` | Search users by name or email |
| POST | `/api/friends/request` | Send friend request |
| GET | `/api/friends/requests` | Get pending friend requests |
| POST | `/api/friends/requests/{id}/accept` | Accept friend request |
| POST | `/api/friends/requests/{id}/decline` | Decline friend request |
| DELETE | `/api/friends/{friend_id}` | Remove friend |

### Chat API (`/api/chat`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/chat/direct/{friend_id}` | Get or create direct chat |
| GET | `/api/chat/{chat_id}/messages` | Get messages with pagination |
| POST | `/api/chat/{chat_id}/messages` | Send message |
| POST | `/api/chat/{chat_id}/read` | Mark messages as read |

### Groups API (`/api/groups`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/groups` | Create group learning session |
| GET | `/api/groups` | Get user's groups |
| GET | `/api/groups/{id}` | Get group details |
| POST | `/api/groups/{id}/invite` | Invite friends to group |
| POST | `/api/groups/{id}/join` | Accept group invitation |
| POST | `/api/groups/{id}/leave` | Leave group |
| DELETE | `/api/groups/{id}/members/{user_id}` | Remove member |

### Calls API (`/api/calls`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/calls/initiate` | Initiate voice/video call |
| POST | `/api/calls/{id}/join` | Join active call |
| POST | `/api/calls/{id}/leave` | Leave call |
| POST | `/api/calls/{id}/end` | End call |
| PATCH | `/api/calls/{id}/media` | Toggle mute/video |


## WebSocket Events

### Connection Events
- `connect` - Client connects, authenticate and set online
- `disconnect` - Client disconnects, set offline

### Chat Events
- `chat:message` - New message sent/received
- `chat:typing` - User typing indicator
- `chat:read` - Messages marked as read

### Call Signaling Events
- `call:initiate` - Start a call
- `call:ring` - Incoming call notification
- `call:accept` - Accept incoming call
- `call:decline` - Decline incoming call
- `call:offer` - WebRTC SDP offer
- `call:answer` - WebRTC SDP answer
- `call:ice-candidate` - ICE candidate exchange
- `call:end` - Call ended
- `call:participant-joined` - Participant joined
- `call:participant-left` - Participant left
- `call:media-toggle` - Mute/video toggle

### Presence Events
- `presence:online` - Friend came online
- `presence:offline` - Friend went offline

## Frontend Components

### New Components Structure
```
frontend/src/components/
├── friends/
│   ├── FriendsView.jsx          # Main friends page
│   ├── FriendsList.jsx          # List of friends
│   ├── FriendSearch.jsx         # Search for users
│   ├── FriendRequests.jsx       # Pending requests
│   ├── FriendCard.jsx           # Individual friend
│   └── index.js
├── chat/
│   ├── DirectChatView.jsx       # 1-on-1 chat interface
│   ├── MessageList.jsx          # Message display
│   ├── MessageInput.jsx         # Message composition
│   ├── TypingIndicator.jsx      # Typing status
│   └── (existing files)
├── groups/
│   ├── GroupLearningView.jsx    # Group session interface
│   ├── GroupList.jsx            # List of groups
│   ├── GroupCreate.jsx          # Create group modal
│   ├── GroupInvite.jsx          # Invite friends modal
│   ├── ParticipantList.jsx      # Group members
│   └── index.js
├── calls/
│   ├── CallInterface.jsx        # Full call view
│   ├── VideoGrid.jsx            # Participant video grid
│   ├── CallControls.jsx         # Mute, video, end
│   ├── CallBubble.jsx           # Floating minimized call
│   ├── IncomingCall.jsx         # Incoming call modal
│   ├── ScreenShare.jsx          # Screen sharing
│   └── index.js
└── ui/
    ├── Badge.jsx                # Notification badge
    ├── Avatar.jsx               # User avatar with status
    └── (existing files)
```

### Context Providers

#### FriendsContext
```javascript
const FriendsContext = createContext({
  friends: [],
  friendRequests: [],
  pendingRequestCount: 0,
  onlineStatus: {},
  sendFriendRequest: async (userId) => {},
  acceptRequest: async (requestId) => {},
  declineRequest: async (requestId) => {},
  removeFriend: async (friendId) => {},
  searchUsers: async (query) => {},
});
```

#### ChatContext
```javascript
const ChatContext = createContext({
  activeChat: null,
  messages: [],
  unreadCounts: {},
  setActiveChat: (chatId) => {},
  sendMessage: async (content) => {},
  markAsRead: async (chatId) => {},
  loadMoreMessages: async () => {},
});
```

#### CallContext
```javascript
const CallContext = createContext({
  activeCall: null,
  isMinimized: false,
  localStream: null,
  remoteStreams: {},
  isMuted: false,
  isVideoEnabled: true,
  initiateCall: async (type, contextType, contextId) => {},
  acceptCall: async (callId) => {},
  declineCall: async (callId) => {},
  endCall: async () => {},
  toggleMute: () => {},
  toggleVideo: () => {},
  minimizeCall: () => {},
  maximizeCall: () => {},
  startScreenShare: async () => {},
  stopScreenShare: () => {},
});
```

## WebRTC Architecture

### Signaling Flow
```
Caller                    Server                    Callee
  │                         │                         │
  │──call:initiate─────────▶│                         │
  │                         │──call:ring─────────────▶│
  │                         │◀──call:accept───────────│
  │◀──call:accepted─────────│                         │
  │──call:offer────────────▶│──call:offer────────────▶│
  │                         │◀──call:answer───────────│
  │◀──call:answer───────────│                         │
  │◀─────────────ice-candidates──────────────────────▶│
  │◀═══════════════WebRTC P2P Connection═════════════▶│
```

### ICE Configuration
```javascript
const iceConfig = {
  iceServers: [
    { urls: 'stun:stun.l.google.com:19302' },
    { urls: 'stun:stun1.l.google.com:19302' },
    {
      urls: process.env.VITE_TURN_URL,
      username: process.env.VITE_TURN_USERNAME,
      credential: process.env.VITE_TURN_CREDENTIAL,
    },
  ],
};
```

### Reconnection Strategy
1. Monitor `iceConnectionState` for disconnection
2. On disconnect, attempt ICE restart
3. If ICE restart fails, re-negotiate connection
4. After 3 failed attempts, notify user and end call

## Sidebar Integration

Update `Sidebar.jsx` to include Friends navigation:
```javascript
const navItems = [
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard' },
  { icon: BookOpen, label: 'Lessons', path: '/lessons' },
  { icon: Dumbbell, label: 'Practice', path: '/practice' },
  { icon: TrendingUp, label: 'Progress', path: '/progress' },
  { icon: History, label: 'History', path: '/history' },
  { icon: Users, label: 'Friends', path: '/friends', badge: pendingRequestCount },
  { icon: Settings, label: 'Settings', path: '/settings' },
]
```

## Call Bubble Implementation

The CallBubble component renders as a portal at the root level:
```javascript
ReactDOM.createPortal(
  <CallBubble 
    call={activeCall}
    duration={callDuration}
    isMuted={isMuted}
    onExpand={maximizeCall}
    onEnd={endCall}
    onToggleMute={toggleMute}
  />,
  document.body
)
```

Features:
- Draggable positioning with custom drag implementation
- Persists position in localStorage
- Shows mini video preview for video calls
- Displays call duration timer
- Quick access to mute toggle and end call


## Correctness Properties

### Property 1: Friend Request Symmetry
**Validates: Requirements 2.5, 2.6**
```
For all users A and B:
  IF A sends friend request to B AND B accepts
  THEN A is in B's friend list AND B is in A's friend list
```

### Property 2: No Self-Friendship
**Validates: Requirement 2.8**
```
For all users A:
  A cannot send friend request to A
  A is never in A's own friend list
```

### Property 3: No Duplicate Friend Requests
**Validates: Requirement 2.9**
```
For all users A and B:
  IF pending request exists from A to B
  THEN A cannot send another request to B
```

### Property 4: Message Ordering Preservation
**Validates: Requirement 3.4**
```
For all messages M1, M2 in chat C:
  IF M1.created_at < M2.created_at
  THEN M1 appears before M2 in message list
```

### Property 5: Bidirectional Friend Removal
**Validates: Requirement 2.7**
```
For all users A and B who are friends:
  IF A removes B as friend
  THEN B is not in A's friend list AND A is not in B's friend list
```

### Property 6: Call State Consistency
**Validates: Requirements 5.6, 6.4, 6.5**
```
For all calls C:
  IF C.status == 'active'
  THEN at least one participant has status 'joined'
  
  IF all participants have status 'left' or 'declined'
  THEN C.status == 'ended'
```

### Property 7: Group Membership Integrity
**Validates: Requirements 4.3, 4.7**
```
For all groups G:
  G.creator is always a member of G (unless G is deleted)
  
  IF user U leaves group G
  THEN U is not in G's participant list
```

### Property 8: Presence Consistency
**Validates: Requirements 8.1, 8.2**
```
For all users U:
  IF U has active WebSocket connection
  THEN U.is_online == true
  
  IF U disconnects
  THEN U.is_online == false within heartbeat timeout
```

### Property 9: Message Delivery Guarantee
**Validates: Requirement 3.3**
```
For all messages M sent in chat C:
  M is persisted to database
  M is delivered to all online participants of C
```

### Property 10: Call Timeout Behavior
**Validates: Requirement 5.7**
```
For all calls C where recipient does not respond:
  IF 30 seconds elapse without accept/decline
  THEN C.status == 'ended' AND caller is notified
```

## Testing Strategy

### Unit Tests
- Service layer methods for friend management
- Message persistence and retrieval
- Call state transitions
- Presence tracking logic

### Property-Based Tests
- Friend relationship symmetry
- Message ordering
- Call state machine transitions
- Group membership invariants

### Integration Tests
- WebSocket event handling
- WebRTC signaling flow
- End-to-end chat delivery
- Call establishment and teardown

## Dependencies

### Backend
```
flask-socketio>=5.3.0
python-socketio>=5.8.0
eventlet>=0.33.0
```

### Frontend
```
socket.io-client@^4.6.0
simple-peer@^9.11.0
react-draggable@^4.4.5
```

## Security Considerations

1. **Authentication**: All WebSocket connections require valid session token
2. **Authorization**: Users can only access chats/calls they're participants of
3. **Rate Limiting**: Limit friend requests and messages per minute
4. **Input Validation**: Sanitize all message content
5. **Media Permissions**: Request camera/mic only when needed

## Performance Considerations

1. **Message Pagination**: Load 50 messages initially, lazy load on scroll
2. **Presence Batching**: Batch presence updates to reduce WebSocket traffic
3. **Video Quality Adaptation**: Reduce quality based on participant count
4. **Connection Pooling**: Reuse WebSocket connections across features
