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
