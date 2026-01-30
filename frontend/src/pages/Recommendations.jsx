import React, { useState } from "react";
import usePolling from "../components/PollingHook";
import AnimeCard from "../components/AnimeCard";
import { fetchRecommendations } from "../api/apiClient";

export default function Recommendations() {
  const [userId, setUserId] = useState("demo-user");

  const { data, loading } = usePolling(async () => {
    const res = await fetchRecommendations(userId);
    return res.recommendations || [];
  }, 3000);

  return (
    <div style={{ padding: "1rem" }}>
      <h2>Recommendations</h2>
      <label>User ID</label>
      <input
        type="text"
        value={userId}
        onChange={(e) => setUserId(e.target.value)}
      />

      {loading && <p>Loading recommendations...</p>}
      {!loading && data && data.length === 0 && <p>No recommendations yet.</p>}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "1rem" }}>
        {data && data.map((anime) => (
          <AnimeCard key={anime.anime_id} anime={anime} />
        ))}
      </div>
    </div>
  );
}
