import React from "react";

export default function Landing() {
  return (
    <div style={{ padding: "2rem" }}>
      <h1>AnimeRec</h1>
      <p>Discover anime you’ll love with personalized recommendations.</p>
      <div style={{ marginTop: "1rem" }}>
        <a href="/onboarding">Get Started</a>
        {" | "}
        <a href="/recommendations">View Recommendations</a>
      </div>
    </div>
  );
}
