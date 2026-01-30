const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:5000";

export async function startRecommendationJob(userId, payload) {
  const res = await fetch(`${API_BASE}/recommendations/${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("Failed to start recommendations");
  return res.json();
}

export async function fetchRecommendations(userId) {
  const res = await fetch(`${API_BASE}/recommendations/${userId}`);
  if (!res.ok) throw new Error("Failed to fetch recommendations");
  return res.json();
}

export async function submitOnboarding(userId, prefs) {
  const res = await fetch(`${API_BASE}/onboarding/${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(prefs),
  });
  if (!res.ok) throw new Error("Failed to submit onboarding");
  return res.json();
}
