# Requirements Document

## Introduction

This document specifies the requirements for a comprehensive Friends & Communication system in MentorMind. The feature enables users to connect with other learners, engage in 1-on-1 and group chats, conduct voice/video calls, and participate in collaborative group learning sessions similar to Google Meet or Zoom. The system includes a persistent call bubble that allows users to navigate the app while maintaining active calls.

## Glossary

- **User**: A registered or anonymous user of the MentorMind application
- **Friend**: Another user who has been added to a user's friend list through mutual acceptance
- **Friend_Request**: A pending invitation from one user to another to become friends
- **Direct_Chat**: A private 1-on-1 conversation between two friends
- **Group_Learning**: A collaborative session with multiple friends for shared learning
- **Voice_Call**: An audio-only real-time communication session
- **Video_Call**: A real-time communication session with both audio and video
- **Call_Bubble**: A floating UI element that persists when navigating away from an active call
- **WebRTC**: Web Real-Time Communication protocol for peer-to-peer audio/video
- **Signaling_Server**: Backend service that coordinates WebRTC connection establishment
- **Participant**: A user who has joined a call or group learning session

## Requirements

### Requirement 1: Friends Section in Sidebar

**User Story:** As a user, I want to see a Friends section in the sidebar navigation, so that I can easily access my social features alongside other app sections.

#### Acceptance Criteria

1. THE Sidebar SHALL display a "Friends" navigation item with an icon below the existing navigation items (Dashboard, Lessons, Practice, Progress, History, Settings)
2. WHEN a user clicks the Friends navigation item, THE System SHALL navigate to the Friends view
3. THE Friends navigation item SHALL display a badge showing the count of pending friend requests when greater than zero
4. WHILE the user is on the Friends view, THE Sidebar SHALL highlight the Friends navigation item as active

### Requirement 2: Friend Management

**User Story:** As a user, I want to add, view, and manage my friends, so that I can build a network of learning partners.

#### Acceptance Criteria

1. WHEN a user accesses the Friends view, THE System SHALL display a list of current friends with their name, avatar, and online status
2. THE System SHALL provide a search interface to find other users by name or email
3. WHEN a user sends a friend request, THE System SHALL create a pending Friend_Request and notify the recipient
4. WHEN a user receives a friend request, THE System SHALL display it in a "Pending Requests" section with Accept and Decline options
5. WHEN a user accepts a friend request, THE System SHALL add both users to each other's friend lists and remove the pending request
6. WHEN a user declines a friend request, THE System SHALL remove the pending request without adding the friendship
7. WHEN a user removes a friend, THE System SHALL remove the friendship from both users' friend lists
8. IF a user attempts to send a friend request to themselves, THEN THE System SHALL reject the request with an appropriate error message
9. IF a user attempts to send a duplicate friend request, THEN THE System SHALL reject the request and inform the user

### Requirement 3: Direct Chat with Friends

**User Story:** As a user, I want to chat with my friends in private 1-on-1 conversations, so that I can communicate and collaborate on learning.

#### Acceptance Criteria

1. WHEN a user selects a friend from their friend list, THE System SHALL open a Direct_Chat interface
2. THE Direct_Chat interface SHALL display the conversation history between the two users
3. WHEN a user sends a message in Direct_Chat, THE System SHALL deliver the message to the recipient in real-time
4. THE System SHALL persist all Direct_Chat messages so they are available when users return to the conversation
5. WHEN a new message arrives in a Direct_Chat, THE System SHALL display a notification indicator if the chat is not currently active
6. THE Direct_Chat interface SHALL display message timestamps and read receipts
7. WHEN a user is typing in Direct_Chat, THE System SHALL show a typing indicator to the other participant

### Requirement 4: Group Learning Sessions

**User Story:** As a user, I want to create and join group learning sessions with multiple friends, so that we can study together collaboratively.

#### Acceptance Criteria

1. THE System SHALL allow users to create a Group_Learning session with a name and invite friends
2. WHEN a user creates a Group_Learning session, THE System SHALL generate a unique session identifier
3. THE System SHALL allow the creator to add or remove participants from the Group_Learning session
4. WHEN a user is invited to a Group_Learning session, THE System SHALL notify them and allow them to accept or decline
5. THE Group_Learning session SHALL support group chat messaging visible to all participants
6. THE System SHALL display a participant list showing all members of the Group_Learning session with their online/call status
7. WHEN a participant leaves a Group_Learning session, THE System SHALL notify remaining participants
8. THE System SHALL persist Group_Learning session history including messages and participant changes

### Requirement 5: Voice Calling

**User Story:** As a user, I want to make voice calls with friends or in group learning sessions, so that I can have real-time audio conversations.

#### Acceptance Criteria

1. THE Direct_Chat interface SHALL provide a button to initiate a Voice_Call with the friend
2. WHEN a user initiates a Voice_Call, THE System SHALL send a call notification to the recipient(s)
3. WHEN a recipient accepts a Voice_Call, THE System SHALL establish a WebRTC audio connection between participants
4. THE Voice_Call interface SHALL provide controls to mute/unmute microphone
5. THE Voice_Call interface SHALL display the call duration
6. WHEN a participant ends the Voice_Call, THE System SHALL terminate their connection and notify other participants
7. IF a Voice_Call recipient declines or does not answer within 30 seconds, THEN THE System SHALL cancel the call and notify the caller
8. THE Group_Learning session SHALL support Voice_Call with multiple participants simultaneously

### Requirement 6: Video Calling

**User Story:** As a user, I want to make video calls with friends or in group learning sessions, so that I can have face-to-face learning interactions like Google Meet or Zoom.

#### Acceptance Criteria

1. THE Direct_Chat interface SHALL provide a button to initiate a Video_Call with the friend
2. WHEN a user initiates a Video_Call, THE System SHALL request camera and microphone permissions
3. WHEN a Video_Call is established, THE System SHALL display video streams from all participants in a grid layout
4. THE Video_Call interface SHALL provide controls to toggle camera on/off
5. THE Video_Call interface SHALL provide controls to mute/unmute microphone
6. THE Video_Call interface SHALL provide a screen sharing option
7. THE Group_Learning session SHALL support Video_Call with multiple participants displaying in a responsive grid
8. WHEN a participant's video is disabled, THE System SHALL display their avatar or initials instead
9. THE Video_Call interface SHALL display participant names below their video feed
10. THE System SHALL optimize video quality based on available bandwidth and number of participants

### Requirement 7: Call Bubble for Active Calls

**User Story:** As a user, I want to continue navigating the app while on a call, so that I can access lessons or other features without ending my conversation.

#### Acceptance Criteria

1. WHEN a user navigates away from an active Voice_Call or Video_Call, THE System SHALL display a floating Call_Bubble
2. THE Call_Bubble SHALL show the call type (voice/video), duration, and participant information
3. THE Call_Bubble SHALL be draggable to any position on the screen
4. WHEN a user clicks the Call_Bubble, THE System SHALL navigate back to the full call interface
5. THE Call_Bubble SHALL provide a button to end the call without returning to the call interface
6. THE Call_Bubble SHALL provide a button to toggle mute status
7. WHILE a Video_Call is minimized to Call_Bubble, THE System SHALL continue transmitting the user's video (if enabled)
8. THE Call_Bubble SHALL display a visual indicator when the user is muted
9. IF the call ends while minimized, THEN THE System SHALL remove the Call_Bubble and show a notification

### Requirement 8: Real-time Presence and Notifications

**User Story:** As a user, I want to see when my friends are online and receive notifications for messages and calls, so that I know when they are available to interact.

#### Acceptance Criteria

1. THE System SHALL track and display online/offline status for all friends
2. WHEN a friend comes online or goes offline, THE System SHALL update their status indicator in real-time
3. THE System SHALL display a green indicator for online friends and gray for offline friends
4. WHEN a user receives a new message while not viewing that chat, THE System SHALL display a notification badge
5. WHEN a user receives an incoming call, THE System SHALL display a full-screen incoming call notification with Accept and Decline buttons
6. THE incoming call notification SHALL play a ringtone sound
7. THE System SHALL support browser notifications for messages and calls when the app is in the background (with user permission)

### Requirement 9: WebRTC Signaling and Connection Management

**User Story:** As a system architect, I want robust WebRTC signaling infrastructure, so that voice and video calls are reliable and performant.

#### Acceptance Criteria

1. THE Signaling_Server SHALL handle WebRTC offer/answer exchange between peers
2. THE Signaling_Server SHALL manage ICE candidate exchange for NAT traversal
3. WHEN a WebRTC connection fails, THE System SHALL attempt reconnection up to 3 times before notifying the user
4. THE System SHALL use STUN servers for NAT traversal
5. THE System SHALL support TURN servers as fallback for restrictive network environments
6. WHEN network conditions change during a call, THE System SHALL adapt video quality accordingly
7. THE System SHALL handle participant join/leave events gracefully without disrupting other participants

### Requirement 10: Data Persistence and Synchronization

**User Story:** As a user, I want my friend list, chat history, and group sessions to persist across sessions, so that I don't lose my social connections and conversations.

#### Acceptance Criteria

1. THE System SHALL persist friend relationships in the database
2. THE System SHALL persist all chat messages with timestamps and sender information
3. THE System SHALL persist Group_Learning session metadata and membership
4. WHEN a user logs in on a new device, THE System SHALL synchronize their friend list and chat history
5. THE System SHALL implement pagination for loading chat history to optimize performance
6. WHEN loading a chat, THE System SHALL initially load the most recent 50 messages and support loading older messages on scroll
