import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { GroupList } from './GroupList';
import { GroupCreate } from './GroupCreate';
import { GroupDetail } from './GroupDetail';
import { GroupInvitations } from './GroupInvitations';

const API_BASE = 'http://localhost:5000/api';

export function GroupLearningView() {
  const { token } = useAuth();
  const [groups, setGroups] = useState([]);
  const [invitations, setInvitations] = useState([]);
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [showCreate, setShowCreate] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      fetchGroups();
      fetchInvitations();
    }
  }, [token]);

  const fetchGroups = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE}/groups`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setGroups(data.groups || []);
      }
    } catch (error) {
      console.error('Failed to fetch groups:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchInvitations = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE}/groups/invitations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setInvitations(data.invitations || []);
      }
    } catch (error) {
      console.error('Failed to fetch invitations:', error);
    }
  };

  const handleAcceptInvitation = async (groupId) => {
    try {
      const response = await fetch(`${API_BASE}/groups/${groupId}/join`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchGroups();
        fetchInvitations();
      }
    } catch (error) {
      console.error('Failed to accept invitation:', error);
    }
  };

  const handleDeclineInvitation = async (groupId) => {
    try {
      const response = await fetch(`${API_BASE}/groups/${groupId}/decline`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        fetchInvitations();
      }
    } catch (error) {
      console.error('Failed to decline invitation:', error);
    }
  };

  const handleGroupSelect = (group) => setSelectedGroup(group);
  
  const handleGroupCreated = (newGroup) => {
    setGroups(prev => [...prev, newGroup]);
    setShowCreate(false);
    handleGroupSelect(newGroup);
  };
  
  const handleBack = () => setSelectedGroup(null);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" />
      </div>
    );
  }

  return (
    <div className="h-full flex">
      <div className={`w-80 border-r border-gray-200 dark:border-gray-700 flex flex-col ${selectedGroup ? 'hidden md:flex' : 'flex'}`}>
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Study Groups</h2>
            <button onClick={() => setShowCreate(true)} className="p-2 text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        </div>
        {invitations.length > 0 && (
          <GroupInvitations 
            invitations={invitations} 
            onAccept={handleAcceptInvitation} 
            onDecline={handleDeclineInvitation} 
          />
        )}
        <GroupList groups={groups} selectedId={selectedGroup?.id} onSelect={handleGroupSelect} />
      </div>
      <div className={`flex-1 ${!selectedGroup ? 'hidden md:flex' : 'flex'} flex-col`}>
        {selectedGroup ? (
          <GroupDetail group={selectedGroup} onBack={handleBack} onUpdate={fetchGroups} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400">
            <div className="text-center">
              <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
              <p>Select a group to start learning together</p>
            </div>
          </div>
        )}
      </div>
      {showCreate && <GroupCreate onClose={() => setShowCreate(false)} onCreate={handleGroupCreated} />}
    </div>
  );
}
