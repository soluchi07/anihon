"""Recommendation algorithm utilities (stub)

- cosine_similarity between genre/studio vectors
- score composition with popularity normalization
"""
import math


def cosine_similarity(vec_a, vec_b):
    # vec_* are dicts: token -> weight
    # stub implementation
    dot = sum(vec_a.get(k, 0) * vec_b.get(k, 0) for k in vec_a)
    mag_a = math.sqrt(sum(v * v for v in vec_a.values()))
    mag_b = math.sqrt(sum(v * v for v in vec_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def compose_score(content_sim, popularity_score, opt_in_popularity=True):
    if opt_in_popularity:
        return 0.7 * content_sim + 0.3 * (popularity_score / 100.0)
    return content_sim
