import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { fetchUserLists, removeFromList, fetchAnimeDetails, rateAnime, addToList } from '../api/apiClient';
import AnimeCard from '../components/AnimeCard';
import '../styles/MyLists.css';

const LIST_TABS = [
  { value: 'watching', label: '👁️ Watching', color: '#667eea' },
  { value: 'completed', label: '✅ Completed', color: '#28a745' },
  { value: 'plan_to_watch', label: '📅 Plan to Watch', color: '#ffc107' },
  { value: 'on_hold', label: '⏸️ On Hold', color: '#6c757d' },
];

export default function MyLists() {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [lists, setLists] = useState({
    watching: [],
    completed: [],
    plan_to_watch: [],
    on_hold: []
  });
  const [animeDetails, setAnimeDetails] = useState({}); // Map anime_id -> anime object
  const [activeTab, setActiveTab] = useState('watching');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!isAuthenticated || !user) {
      navigate('/login');
      return;
    }

    async function loadLists() {
      try {
        setLoading(true);
        setError(null);

        const data = await fetchUserLists(user.userId);
        if (data.status === 'ok' && data.lists) {
          setLists(data.lists);

          // Fetch anime details for all anime in lists
          const allAnimeIds = new Set();
          Object.values(data.lists).forEach(listItems => {
            listItems.forEach(item => allAnimeIds.add(item.anime_id));
          });

          // Fetch details for each anime
          const detailsPromises = Array.from(allAnimeIds).map(async (animeId) => {
            try {
              const animeData = await fetchAnimeDetails(animeId);
              if (animeData.status === 'ok' && animeData.anime) {
                return { id: animeId, data: animeData.anime };
              }
            } catch (err) {
              console.error(`Failed to load anime ${animeId}:`, err);
            }
            return null;
          });

          const results = await Promise.all(detailsPromises);
          const detailsMap = {};
          results.forEach(result => {
            if (result) {
              detailsMap[result.id] = result.data;
            }
          });

          setAnimeDetails(detailsMap);
        }
      } catch (err) {
        console.error('Error loading lists:', err);
        setError('Failed to load your lists');
      } finally {
        setLoading(false);
      }
    }

    loadLists();
  }, [user, isAuthenticated, navigate]);

  const handleRemove = async (animeId, listType) => {
    try {
      await removeFromList(user.userId, animeId, listType);
      
      // Update local state
      setLists(prev => ({
        ...prev,
        [listType]: prev[listType].filter(item => item.anime_id !== animeId)
      }));
    } catch (err) {
      console.error('Error removing from list:', err);
    }
  };

  const handleRate = async (animeId, rating) => {
    try {
      await rateAnime(user.userId, animeId, rating);
    } catch (err) {
      console.error('Error rating anime:', err);
    }
  };

  const handleListChange = async (animeId, currentList, newList) => {
    try {
      // Remove from old list if exists
      if (currentList) {
        await removeFromList(user.userId, animeId, currentList);
        setLists(prev => ({
          ...prev,
          [currentList]: prev[currentList].filter(item => item.anime_id !== animeId)
        }));
      }

      // Add to new list
      if (newList) {
        await addToList(user.userId, animeId, newList);
        const animeData = animeDetails[animeId];
        if (animeData) {
          setLists(prev => ({
            ...prev,
            [newList]: [...prev[newList], { anime_id: animeId, list_type: newList, timestamp: Date.now() }]
          }));
        }
      }
    } catch (err) {
      console.error('Error updating list:', err);
    }
  };

  if (loading) {
    return (
      <div className="my-lists-container">
        <div className="loading-state">Loading your lists...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="my-lists-container">
        <div className="error-state">
          <h2>{error}</h2>
          <button onClick={() => navigate('/recommendations')} className="back-button">
            Back to Recommendations
          </button>
        </div>
      </div>
    );
  }

  const activeList = lists[activeTab] || [];
  const activeListTab = LIST_TABS.find(tab => tab.value === activeTab);

  return (
    <div className="my-lists-container">
      <div className="my-lists-header">
        <h1 className="my-lists-title">My Anime Lists</h1>
        <p className="my-lists-subtitle">Organize and track your anime journey</p>
      </div>

      {/* Tabs */}
      <div className="list-tabs">
        {LIST_TABS.map(tab => {
          const count = lists[tab.value]?.length || 0;
          return (
            <button
              key={tab.value}
              className={`list-tab ${activeTab === tab.value ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.value)}
              style={activeTab === tab.value ? { borderBottomColor: tab.color } : {}}
            >
              <span style={{ color: tab.color }}>{tab.label}</span>
              <span className="tab-count">{count}</span>
            </button>
          );
        })}
      </div>

      {/* Content */}
      <div className="list-content">
        {activeList.length === 0 ? (
          <div className="empty-list">
            <div className="empty-list-icon">📭</div>
            <h3>No anime in {activeListTab?.label || 'this list'}</h3>
            <p>Start adding anime from your recommendations!</p>
            <button 
              className="goto-recommendations-button"
              onClick={() => navigate('/recommendations')}
            >
              Browse Recommendations
            </button>
          </div>
        ) : (
          <div className="list-grid">
            {activeList.map(item => {
              const anime = animeDetails[item.anime_id];
              if (!anime) return null;

              const currentList = Object.keys(lists).find(listType =>
                lists[listType].some(i => i.anime_id === item.anime_id)
              );

              return (
                <div key={item.anime_id} className="list-item">
                  <AnimeCard 
                    anime={anime}
                    onRate={(rating) => handleRate(item.anime_id, rating)}
                    onListChange={(newList) => handleListChange(item.anime_id, currentList, newList)}
                    currentList={currentList}
                  />
                  <button
                    className="remove-button"
                    onClick={() => handleRemove(item.anime_id, activeTab)}
                    title="Remove from list"
                  >
                    ❌ Remove
                  </button>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
