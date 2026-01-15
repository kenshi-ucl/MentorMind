# Implementation Tasks: Friends & Communication System

## Task 1: Backend Data Models
- [ ] 1.1 Create Friend model in `backend/app/models/friend.py` with user_id, friend_id, created_at fields and unique constraint
- [ ] 1.2 Create FriendRequest model in `backend/app/models/friend_request.py` with sender_id, recipient_id, status fields
- [ ] 1.3 Create DirectChat model in `backend/app/models/direct_chat.py` with user1_id, user2_id, last_message_at fields
- [ ] 1.4 Create Message model in `backend/app/models/message.py` with chat_id, chat_type, sender_id, content, read_by fields
- [ ] 1.5 Create GroupLearning model in `backend/app/models/group_learning.py` with name, creator_id, last_activity_at fields
- [ ] 1.6 Create GroupMember model in `backend/app/models/group_member.py` with group_id, user_id, role, status fields
- [ ] 1.7 Create Call and CallParticipant models in `backend/app/models/call.py` with call_type, context_type, status fields
- [ ] 1.8 Create UserPresence model in `backend/app/models/user_presence.py` with is_online, last_seen, socket_id fields
- [ ] 1.9 Update `backend/app/models/__init__.py` to export all new models

## Task 2: Backend Friend Service
- [ ] 2.1 Create FriendService class in `backend/app/services/friend_service.py` with get_friends method
- [ ] 2.2 Add search_users method to FriendService for searching users by name or email
- [ ] 2.3 Add send_friend_request method with self-request and duplicate validation
- [ ] 2.4 Add get_pending_requests method to retrieve incoming friend requests
- [ ] 2.5 Add accept_request method that creates bidirectional friendship
- [ ] 2.6 Add decline_request method that removes the pending request
- [ ] 2.7 Add remove_friend method that removes friendship from both users

## Task 3: Backend Chat Service
- [ ] 3.1 Create ChatService class in `backend/app/services/chat_service.py` with get_or_create_direct_chat method
- [ ] 3.2 Add get_messages method with pagination support (limit 50, offset-based)
- [ ] 3.3 Add send_message method that persists message and updates last_message_at
- [ ] 3.4 Add mark_as_read method that updates read_by array for messages

## Task 4: Backend Group Service
- [ ] 4.1 Create GroupService class in `backend/app/services/group_service.py` with create_group method
- [ ] 4.2 Add get_user_groups method to retrieve all groups user is member of
- [ ] 4.3 Add invite_to_group method that creates pending GroupMember entries
- [ ] 4.4 Add join_group method that updates member status to active
- [ ] 4.5 Add leave_group method that updates member status to left
- [ ] 4.6 Add remove_member method with creator-only authorization check

## Task 5: Backend Call Service
- [ ] 5.1 Create CallService class in `backend/app/services/call_service.py` with initiate_call method
- [ ] 5.2 Add join_call method that updates participant status to joined
- [ ] 5.3 Add leave_call method that updates participant status and checks if call should end
- [ ] 5.4 Add end_call method that sets call status to ended
- [ ] 5.5 Add update_media_state method for mute/video toggle

## Task 6: Backend Presence Service
- [ ] 6.1 Create PresenceService class in `backend/app/services/presence_service.py` with set_online method
- [ ] 6.2 Add set_offline method that updates is_online and last_seen
- [ ] 6.3 Add get_friends_presence method to get online status of all friends

## Task 7: Backend Friends API Routes
- [ ] 7.1 Create friends blueprint in `backend/app/routes/friends.py` with GET /api/friends endpoint
- [ ] 7.2 Add GET /api/friends/search endpoint with query parameter
- [ ] 7.3 Add POST /api/friends/request endpoint for sending friend requests
- [ ] 7.4 Add GET /api/friends/requests endpoint for pending requests
- [ ] 7.5 Add POST /api/friends/requests/<id>/accept endpoint
- [ ] 7.6 Add POST /api/friends/requests/<id>/decline endpoint
- [ ] 7.7 Add DELETE /api/friends/<friend_id> endpoint for removing friends

## Task 8: Backend Chat API Routes
- [ ] 8.1 Add GET /api/chat/direct/<friend_id> endpoint to get or create direct chat
- [ ] 8.2 Add GET /api/chat/<chat_id>/messages endpoint with pagination
- [ ] 8.3 Add POST /api/chat/<chat_id>/messages endpoint for sending messages
- [ ] 8.4 Add POST /api/chat/<chat_id>/read endpoint for marking messages read

## Task 9: Backend Groups API Routes
- [ ] 9.1 Create groups blueprint in `backend/app/routes/groups.py` with POST /api/groups endpoint
- [ ] 9.2 Add GET /api/groups endpoint to list user's groups
- [ ] 9.3 Add GET /api/groups/<id> endpoint for group details
- [ ] 9.4 Add POST /api/groups/<id>/invite endpoint for inviting friends
- [ ] 9.5 Add POST /api/groups/<id>/join endpoint for accepting invitations
- [ ] 9.6 Add POST /api/groups/<id>/leave endpoint for leaving groups
- [ ] 9.7 Add DELETE /api/groups/<id>/members/<user_id> endpoint for removing members

## Task 10: Backend Calls API Routes
- [ ] 10.1 Create calls blueprint in `backend/app/routes/calls.py` with POST /api/calls/initiate endpoint
- [ ] 10.2 Add POST /api/calls/<id>/join endpoint
- [ ] 10.3 Add POST /api/calls/<id>/leave endpoint
- [ ] 10.4 Add POST /api/calls/<id>/end endpoint
- [ ] 10.5 Add PATCH /api/calls/<id>/media endpoint for mute/video toggle
- [ ] 10.6 Register all new blueprints in `backend/app/__init__.py`

## Task 11: Backend WebSocket Setup
- [ ] 11.1 Add flask-socketio and eventlet to `backend/requirements.txt`
- [ ] 11.2 Initialize SocketIO in `backend/app/__init__.py`
- [ ] 11.3 Create socket events handler in `backend/app/sockets/__init__.py`
- [ ] 11.4 Implement connect/disconnect handlers with presence updates
- [ ] 11.5 Implement chat:message, chat:typing, chat:read event handlers
- [ ] 11.6 Implement call signaling events (initiate, ring, accept, decline, offer, answer, ice-candidate, end)
- [ ] 11.7 Implement presence:online and presence:offline broadcast events

## Task 12: Frontend Context Providers
- [ ] 12.1 Create FriendsContext in `frontend/src/context/FriendsContext.jsx` with friends state and methods
- [ ] 12.2 Create ChatContext in `frontend/src/context/ChatContext.jsx` with messages state and methods
- [ ] 12.3 Create CallContext in `frontend/src/context/CallContext.jsx` with call state and WebRTC methods
- [ ] 12.4 Update `frontend/src/context/index.js` to export new contexts
- [ ] 12.5 Wrap App with new context providers in appropriate order

## Task 13: Frontend WebSocket Service
- [ ] 13.1 Add socket.io-client to `frontend/package.json`
- [ ] 13.2 Create WebSocketService in `frontend/src/lib/websocket.js` with connection management
- [ ] 13.3 Implement chat event listeners and emitters
- [ ] 13.4 Implement call signaling event listeners and emitters
- [ ] 13.5 Implement presence event handling

## Task 14: Frontend WebRTC Service
- [ ] 14.1 Create WebRTCService in `frontend/src/lib/webrtc.js` with peer connection setup
- [ ] 14.2 Implement ICE configuration with STUN servers
- [ ] 14.3 Implement offer/answer creation and handling
- [ ] 14.4 Implement ICE candidate exchange
- [ ] 14.5 Implement media stream management for audio/video
- [ ] 14.6 Implement screen sharing functionality
- [ ] 14.7 Implement reconnection logic with 3 retry attempts

## Task 15: Sidebar Integration
- [ ] 15.1 Add Users icon import and Friends nav item with badge to `frontend/src/components/layout/Sidebar.jsx`
- [ ] 15.2 Connect pending request count from FriendsContext to badge
- [ ] 15.3 Add /friends route to MainLayout.jsx routing

## Task 16: Friends Components
- [ ] 16.1 Create FriendsView.jsx main page with tabs for friends list and requests
- [ ] 16.2 Create FriendsList.jsx with online status indicators (green/gray)
- [ ] 16.3 Create FriendSearch.jsx with search input and results display
- [ ] 16.4 Create FriendRequests.jsx with accept/decline buttons
- [ ] 16.5 Create FriendCard.jsx for individual friend display with chat button
- [ ] 16.6 Create `frontend/src/components/friends/index.js` exports

## Task 17: Direct Chat Components
- [ ] 17.1 Create DirectChatView.jsx with message list and input
- [ ] 17.2 Create MessageList.jsx with infinite scroll for loading history
- [ ] 17.3 Create MessageInput.jsx with typing indicator emission
- [ ] 17.4 Create TypingIndicator.jsx component
- [ ] 17.5 Add voice and video call buttons to DirectChatView header

## Task 18: Group Learning Components
- [ ] 18.1 Create GroupLearningView.jsx main component with chat and participants
- [ ] 18.2 Create GroupList.jsx component showing user's groups
- [ ] 18.3 Create GroupCreate.jsx modal with name input and friend selection
- [ ] 18.4 Create GroupInvite.jsx modal for inviting additional friends
- [ ] 18.5 Create ParticipantList.jsx with online/call status indicators
- [ ] 18.6 Create `frontend/src/components/groups/index.js` exports

## Task 19: Call Interface Components
- [ ] 19.1 Create CallInterface.jsx full-screen view with video grid and controls
- [ ] 19.2 Create VideoGrid.jsx responsive grid for participant videos
- [ ] 19.3 Create CallControls.jsx with mute, video, screen share, end buttons
- [ ] 19.4 Create IncomingCall.jsx modal with ringtone, accept and decline buttons
- [ ] 19.5 Create `frontend/src/components/calls/index.js` exports

## Task 20: Call Bubble Component
- [ ] 20.1 Create CallBubble.jsx floating component rendered as portal
- [ ] 20.2 Implement draggable functionality with mouse/touch events
- [ ] 20.3 Implement position persistence in localStorage
- [ ] 20.4 Add mini video preview for video calls
- [ ] 20.5 Add call duration timer, mute toggle, and end call button
- [ ] 20.6 Add muted indicator visual feedback

## Task 21: UI Components
- [ ] 21.1 Create Badge.jsx notification badge component in `frontend/src/components/ui/`
- [ ] 21.2 Create Avatar.jsx with online status indicator dot
- [ ] 21.3 Update `frontend/src/components/ui/index.js` exports

## Task 22: Property-Based Tests - Friend Management
- [ ] 22.1 Create `backend/tests/properties/test_friend_properties.py` with Hypothesis setup
- [ ] 22.2 Implement Property 1 test: Friend Request Symmetry (accepted request creates bidirectional friendship)
- [ ] 22.3 Implement Property 2 test: No Self-Friendship (cannot send request to self)
- [ ] 22.4 Implement Property 3 test: No Duplicate Friend Requests
- [ ] 22.5 Implement Property 5 test: Bidirectional Friend Removal

## Task 23: Property-Based Tests - Messaging and Calls
- [ ] 23.1 Create `backend/tests/properties/test_message_properties.py`
- [ ] 23.2 Implement Property 4 test: Message Ordering Preservation
- [ ] 23.3 Create `backend/tests/properties/test_call_properties.py`
- [ ] 23.4 Implement Property 6 test: Call State Consistency
- [ ] 23.5 Implement Property 10 test: Call Timeout Behavior (30 second timeout)

## Task 24: Property-Based Tests - Groups and Presence
- [ ] 24.1 Create `backend/tests/properties/test_group_properties.py`
- [ ] 24.2 Implement Property 7 test: Group Membership Integrity
- [ ] 24.3 Create `backend/tests/properties/test_presence_properties.py`
- [ ] 24.4 Implement Property 8 test: Presence Consistency

## Task 25: Integration and Polish
- [ ] 25.1 Add notification sounds for incoming calls in CallContext
- [ ] 25.2 Implement browser notification permission request on app load
- [ ] 25.3 Add browser notifications for messages when app is in background
- [ ] 25.4 Implement 30-second call timeout with automatic cancellation
- [ ] 25.5 End-to-end testing of friend request, chat, and call flows
