import { useState, useEffect } from 'react';
import { useAuth } from '../../context/AuthContext';
import { ParticipantList } from './ParticipantList';
import { GroupInvite } from './GroupInvite';
import { GroupChat } from './GroupChat';

const API_BASE = 'http://localhost:5000/api';

export function GroupDetail({ group, onBack, onUpdate }) {
  const { user, token } = useAuth();
  const [activeTab, setActiveTab] = useState('chat');
  const [showInvite, setShowInvite] = useState(false);
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMembers();
  }, [group.id, token]);

  const fetchMembers = async () => {
    if (!token) return;
    try {
      const response = await fetch(`${API_BASE}/groups/${group.id}/members`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMembers(data.members || []);
      }
    } catch (error) {
      console.error('Failed to fetch members:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveMember = async (memberId) => {
    if (!confirm('Remove this member from the group?')) return;
    try {
      const response = await fetch(`${API_BASE}/groups/${group.id}/members/${memberId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        setMembers(prev => prev.filter(m => m.id !== memberId));
        onUpdate();
      }
    } catch (error) {
      console.error('Failed to remove member:', error);
    }
  };


  const handleLeaveGroup = async () => {
    if (!confirm('Are you sure you want to leave this group?')) return;
    try {
      const response = await fetch(`${API_BASE}/groups/${group.id}/leave`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        onUpdate();
        onBack();
      }
    } catch (error) {
      console.error('Failed to leave group:', error);
    }
  };

  const isCreator = group.creatorId === user?.id;

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-3">
          <button onClick={onBack} className="md:hidden p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="flex-1">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{group.name}</h2>
            <p className="text-sm text-gray-500 dark:text-gray-400">{group.memberCount} members • {group.topic || 'General'}</p>
          </div>
          <button onClick={() => setShowInvite(true)} className="p-2 text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg" title="Invite friends">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z" />
            </svg>
          </button>
        </div>
        <div className="flex gap-1 mt-4">
          <button onClick={() => setActiveTab('chat')} className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'chat' ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}>Chat</button>
          <button onClick={() => setActiveTab('members')} className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${activeTab === 'members' ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'}`}>Members ({members.length})</button>
        </div>
      </div>
      <div className="flex-1 overflow-hidden">
        {activeTab === 'chat' ? <GroupChat groupId={group.id} /> : (
          <div className="p-4 overflow-y-auto h-full">
            {loading ? <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600" /></div> : (
              <>
                <ParticipantList participants={members} currentUserId={user?.id} creatorId={group.creatorId} onRemove={handleRemoveMember} />
                {!isCreator && <button onClick={handleLeaveGroup} className="mt-4 w-full px-4 py-2 text-red-600 border border-red-300 dark:border-red-700 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20">Leave Group</button>}
              </>
            )}
          </div>
        )}
      </div>
      {showInvite && <GroupInvite groupId={group.id} onClose={() => setShowInvite(false)} onInvited={() => { fetchMembers(); onUpdate(); }} />}
    </div>
  );
}
