"""Unit tests for recommendation algorithm."""
import sys
from pathlib import Path

# Add parent directory to path so we can import algorithm
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from algorithm import (
    cosine_similarity,
    build_anime_vector,
    compose_recommendation_score,
    recommend_anime,
    normalize_vector,
)


class TestNormalizeVector:
    def test_normalize_unit_vector(self):
        """Test normalizing a unit vector."""
        vec = {"a": 1.0}
        result = normalize_vector(vec)
        assert result == {"a": 1.0}

    def test_normalize_multi_element(self):
        """Test normalizing a multi-element vector."""
        vec = {"a": 3.0, "b": 4.0}  # magnitude = 5
        result = normalize_vector(vec)
        assert abs(result["a"] - 0.6) < 1e-6
        assert abs(result["b"] - 0.8) < 1e-6

    def test_normalize_empty_vector(self):
        """Test normalizing an empty vector."""
        result = normalize_vector({})
        assert result == {}


class TestCosineSimilarity:
    def test_identical_vectors(self):
        """Test cosine similarity of identical vectors."""
        vec = {"a": 1.0, "b": 2.0}
        sim = cosine_similarity(vec, vec)
        assert abs(sim - 1.0) < 1e-6

    def test_orthogonal_vectors(self):
        """Test cosine similarity of orthogonal vectors."""
        vec_a = {"a": 1.0, "b": 0.0}
        vec_b = {"a": 0.0, "b": 1.0}
        sim = cosine_similarity(vec_a, vec_b)
        assert abs(sim - 0.0) < 1e-6

    def test_partial_overlap(self):
        """Test cosine similarity with partial overlap."""
        vec_a = {"genre:Action": 1.0}
        vec_b = {"genre:Action": 0.5, "genre:Drama": 0.5}
        sim = cosine_similarity(vec_a, vec_b)
        assert 0.0 <= sim <= 1.0
        assert sim > 0.5  # should be > 0.5 due to common feature

    def test_empty_vectors(self):
        """Test cosine similarity with empty vectors."""
        sim = cosine_similarity({}, {})
        assert sim == 0.0


class TestBuildAnimeVector:
    def test_simple_anime(self):
        """Test building a vector from simple anime."""
        anime = {
            "genres": ["Action"],
            "studios": ["Studio A"],
            "year": 2024,
            "score": 8.0,
            "popularity_score": 80.0,
        }
        vec = build_anime_vector(anime)
        assert "genre:Action" in vec
        assert "studio:Studio A" in vec
        assert "year" in vec
        assert "score" in vec
        assert "popularity" in vec

    def test_anime_with_null_score(self):
        """Test building vector with null score (should use default 5.0)."""
        anime = {
            "genres": ["Drama"],
            "studios": [],
            "year": 2020,
            "score": None,
            "popularity_score": 50.0,
        }
        vec = build_anime_vector(anime)
        assert "genre:Drama" in vec
        # Should not crash and should be buildable

    def test_anime_with_missing_fields(self):
        """Test building vector with missing optional fields."""
        anime = {
            "genres": ["Comedy"],
            "studios": [],
        }
        vec = build_anime_vector(anime)
        assert "genre:Comedy" in vec


class TestComposeRecommendationScore:
    def test_opt_in_popularity_blend(self):
        """Test score composition with popularity opt-in."""
        content_sim = 0.8
        popularity = 60.0
        score = compose_recommendation_score(content_sim, popularity, opt_in_popularity=True)
        # 0.7 * 0.8 + 0.3 * 0.6 = 0.56 + 0.18 = 0.74
        assert abs(score - 0.74) < 1e-6

    def test_opt_out_popularity(self):
        """Test score composition without popularity."""
        content_sim = 0.8
        popularity = 100.0
        score = compose_recommendation_score(content_sim, popularity, opt_in_popularity=False)
        assert abs(score - 0.8) < 1e-6

    def test_score_bounds(self):
        """Test that score is always in [0, 1]."""
        for content_sim in [0.0, 0.5, 1.0]:
            for popularity in [0.0, 50.0, 100.0]:
                for opt_in in [True, False]:
                    score = compose_recommendation_score(content_sim, popularity, opt_in)
                    assert 0.0 <= score <= 1.0


class TestRecommendAnime:
    @pytest.fixture
    def sample_anime_pool(self):
        """Sample anime for testing."""
        return [
            {
                "anime_id": 1,
                "title": "Action Hero",
                "genres": ["Action", "Adventure"],
                "studios": ["Studio A"],
                "year": 2024,
                "score": 8.5,
                "popularity_score": 85.0,
                "image_url": "http://example.com/1.jpg",
            },
            {
                "anime_id": 2,
                "title": "Drama Love",
                "genres": ["Drama", "Romance"],
                "studios": ["Studio B"],
                "year": 2023,
                "score": 7.5,
                "popularity_score": 60.0,
                "image_url": "http://example.com/2.jpg",
            },
            {
                "anime_id": 3,
                "title": "Action Sci-Fi",
                "genres": ["Action", "Sci-Fi"],
                "studios": ["Studio A"],
                "year": 2024,
                "score": 8.0,
                "popularity_score": 75.0,
                "image_url": "http://example.com/3.jpg",
            },
            {
                "anime_id": 4,
                "title": "Comedy Show",
                "genres": ["Comedy"],
                "studios": ["Studio C"],
                "year": 2022,
                "score": None,  # null score -> 5.0 default
                "popularity_score": 40.0,
                "image_url": "http://example.com/4.jpg",
            },
        ]

    def test_recommend_by_preference(self, sample_anime_pool):
        """Test recommendations based on user preferences."""
        user_prefs = {"genres": ["Action"], "studios": []}
        recs = recommend_anime(
            user_preferences=user_prefs,
            user_liked_anime=[],
            candidate_anime=sample_anime_pool,
            top_n=2,
            opt_in_popularity=False,
        )

        assert len(recs) <= 2
        # Action anime should rank higher
        assert recs[0]["anime_id"] in [1, 3]  # Both have Action genre
        for rec in recs:
            assert "score" in rec
            assert "content_similarity" in rec

    def test_recommend_with_liked_anime(self, sample_anime_pool):
        """Test recommendations blending preferences with liked anime."""
        user_prefs = {"genres": [], "studios": []}
        user_liked = [sample_anime_pool[0]]  # User liked "Action Hero"

        recs = recommend_anime(
            user_preferences=user_prefs,
            user_liked_anime=user_liked,
            candidate_anime=sample_anime_pool,
            top_n=3,
            opt_in_popularity=False,
        )

        assert len(recs) <= 3
        # Should exclude the liked anime and recommend similar ones
        liked_ids = {item["anime_id"] for item in user_liked}
        rec_ids = {rec["anime_id"] for rec in recs}
        assert not rec_ids.intersection(liked_ids)

    def test_recommend_exclude_liked(self, sample_anime_pool):
        """Test that already-liked anime are excluded from recommendations."""
        user_prefs = {"genres": ["Action"], "studios": []}
        exclude_ids = {1, 2}

        recs = recommend_anime(
            user_preferences=user_prefs,
            user_liked_anime=[],
            candidate_anime=sample_anime_pool,
            top_n=10,
            exclude_anime_ids=exclude_ids,
        )

        rec_ids = {rec["anime_id"] for rec in recs}
        assert not rec_ids.intersection(exclude_ids)

    def test_recommend_with_popularity_opt_in(self, sample_anime_pool):
        """Test recommendations with popularity blending."""
        user_prefs = {"genres": ["Drama"], "studios": []}

        recs_with_pop = recommend_anime(
            user_preferences=user_prefs,
            user_liked_anime=[],
            candidate_anime=sample_anime_pool,
            top_n=10,
            opt_in_popularity=True,
        )

        recs_no_pop = recommend_anime(
            user_preferences=user_prefs,
            user_liked_anime=[],
            candidate_anime=sample_anime_pool,
            top_n=10,
            opt_in_popularity=False,
        )

        # With popularity, scores should be different
        assert recs_with_pop[0]["score"] != recs_no_pop[0]["score"]

    def test_recommend_cold_start(self, sample_anime_pool):
        """Test cold-start recommendations (new user with no likes)."""
        user_prefs = {"genres": ["Comedy", "Action"], "studios": []}
        recs = recommend_anime(
            user_preferences=user_prefs,
            user_liked_anime=[],
            candidate_anime=sample_anime_pool,
            top_n=10,
        )

        assert len(recs) > 0
        assert all("score" in rec and rec["score"] >= 0.0 for rec in recs)

    def test_recommend_top_n_limit(self, sample_anime_pool):
        """Test that top-N is respected."""
        user_prefs = {"genres": ["Action"], "studios": []}
        for top_n in [1, 2, 5]:
            recs = recommend_anime(
                user_preferences=user_prefs,
                user_liked_anime=[],
                candidate_anime=sample_anime_pool,
                top_n=top_n,
            )
            assert len(recs) <= top_n

    def test_recommend_results_sorted_by_score(self, sample_anime_pool):
        """Test that recommendations are sorted by score descending."""
        user_prefs = {"genres": ["Action"], "studios": []}
        recs = recommend_anime(
            user_preferences=user_prefs,
            user_liked_anime=[],
            candidate_anime=sample_anime_pool,
            top_n=10,
        )

        scores = [rec["score"] for rec in recs]
        assert scores == sorted(scores, reverse=True)
