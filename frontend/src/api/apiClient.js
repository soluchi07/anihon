const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000";

// Helper function to get authorization headers with JWT
function getAuthHeaders() {
  const token = localStorage.getItem("authToken");
  const headers = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  return headers;
}

export async function startRecommendationJob(userId, payload) {
  const res = await fetch(`${API_BASE}/recommendations/${userId}`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to start recommendations");
  return res.json();
}

export async function fetchRecommendations(userId) {
  const res = await fetch(`${API_BASE}/recommendations/${userId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch recommendations");
  return res.json();
}

export async function submitOnboarding(userId, prefs) {
  const res = await fetch(`${API_BASE}/onboarding/${userId}`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(prefs),
  });
  if (!res.ok) throw new Error("Failed to submit onboarding");
  return res.json();
}

export async function likeAnime(userId, animeId) {
  const res = await fetch(`${API_BASE}/interactions/${userId}`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ anime_id: animeId, liked: true }),
  });
  if (!res.ok) throw new Error("Failed to record interaction");
  return res.json();
}

// Fetch single anime details (authenticated route)
export async function fetchAnimeDetails(animeId) {
  const res = await fetch(`${API_BASE}/anime/${animeId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch anime details");
  return res.json();
}

// Fetch similar anime (authenticated route)
export async function fetchSimilarAnime(animeId) {
  const res = await fetch(`${API_BASE}/anime/${animeId}/similar`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch similar anime");
  return res.json();
}

// Fetch all user interactions (ratings, likes)
export async function fetchUserInteractions(userId) {
  const res = await fetch(`${API_BASE}/interactions/${userId}`, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch user interactions");
  return res.json();
}

// Rate an anime (1-10 scale)
export async function rateAnime(userId, animeId, rating) {
  const res = await fetch(`${API_BASE}/interactions/${userId}`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ anime_id: animeId, rating: rating }),
  });
  if (!res.ok) throw new Error("Failed to rate anime");
  return res.json();
}

// Add anime to a list
export async function addToList(userId, animeId, listType) {
  const res = await fetch(`${API_BASE}/lists/${userId}`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify({ anime_id: animeId, list_type: listType }),
  });
  if (!res.ok) throw new Error("Failed to add to list");
  return res.json();
}

// Remove anime from a list
export async function removeFromList(userId, animeId, listType) {
  const compositeKey = `${listType}%23${animeId}`;
  const res = await fetch(`${API_BASE}/lists/${userId}/${compositeKey}`, {
    method: "DELETE",
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to remove from list");
  return res.json();
}

// Fetch user lists (all or filtered by type)
export async function fetchUserLists(userId, listType = null) {
  const url = listType 
    ? `${API_BASE}/lists/${userId}?list_type=${listType}`
    : `${API_BASE}/lists/${userId}`;
  const res = await fetch(url, {
    headers: getAuthHeaders(),
  });
  if (!res.ok) throw new Error("Failed to fetch user lists");
  return res.json();
}
