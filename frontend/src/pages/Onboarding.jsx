import React, { useState } from "react";
import { submitOnboarding, startRecommendationJob } from "../api/apiClient";

const GENRES = [
  "Action",
  "Adventure",
  "Drama",
  "Comedy",
  "Romance",
  "Sci-Fi",
  "Fantasy",
  "Slice of Life",
  "Thriller",
  "Mystery",
];

const STUDIOS = [
  "Studio A",
  "Studio B",
  "Studio C",
  "MAPPA",
  "Bones",
  "A-1 Pictures",
];

export default function Onboarding() {
  const [userId, setUserId] = useState("demo-user");
  const [genres, setGenres] = useState([]);
  const [studios, setStudios] = useState([]);
  const [preferPopular, setPreferPopular] = useState(true);
  const [status, setStatus] = useState("");

  const toggleSelection = (value, current, setCurrent) => {
    if (current.includes(value)) {
      setCurrent(current.filter((v) => v !== value));
    } else {
      setCurrent([...current, value]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("Submitting onboarding...");
    try {
      const prefs = {
        genres,
        studios,
        opt_in_popularity: preferPopular,
      };
      await submitOnboarding(userId, prefs);
      await startRecommendationJob(userId, {
        opt_in_popularity: preferPopular,
        top_n: 20,
      });
      setStatus("Onboarding submitted. Recommendation job started.");
    } catch (err) {
      setStatus("Error: " + err.message);
    }
  };

  return (
    <div style={{ padding: "1rem" }}>
      <h2>Onboarding</h2>
      <p>Select your favorite genres and studios, then start recommendations.</p>

      <form onSubmit={handleSubmit}>
        <label>User ID</label>
        <input
          type="text"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
        />

        <h4>Genres</h4>
        {GENRES.map((g) => (
          <label key={g} style={{ display: "block" }}>
            <input
              type="checkbox"
              checked={genres.includes(g)}
              onChange={() => toggleSelection(g, genres, setGenres)}
            />
            {g}
          </label>
        ))}

        <h4>Studios</h4>
        {STUDIOS.map((s) => (
          <label key={s} style={{ display: "block" }}>
            <input
              type="checkbox"
              checked={studios.includes(s)}
              onChange={() => toggleSelection(s, studios, setStudios)}
            />
            {s}
          </label>
        ))}

        <label style={{ display: "block", marginTop: "1rem" }}>
          <input
            type="checkbox"
            checked={preferPopular}
            onChange={(e) => setPreferPopular(e.target.checked)}
          />
          Include popular anime in recommendations
        </label>

        <button type="submit" style={{ marginTop: "1rem" }}>
          Start Recommendations
        </button>
      </form>

      {status && <p>{status}</p>}
    </div>
  );
}
