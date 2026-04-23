# Evidence of Implementation

## Screenshots to Capture (AWS Console)

Take the following screenshots from the AWS Console and add them to this document or a `docs/screenshots/` folder.

| # | Where to go | What to capture |
|---|---|---|
| 1 | Lambda → Functions | Full list of 8 Lambda functions (auth, onboarding, recommendation-api, recommendation_worker, anime_getter, interactions, lists, data_ingest) |
| 2 | Lambda → Any function → Monitor tab | CloudWatch invocation metrics graph showing the function has been called |
| 3 | DynamoDB → Tables | List of all 5 tables (Users, Anime, Interactions, RecommendationCache, Lists) |
| 4 | DynamoDB → Anime table → Explore items | A few sample items showing anime metadata and feature vectors |
| 5 | API Gateway → animerec API → Resources | The resource tree showing all routes (GET/POST /recommendations, /auth/*, /anime/{id}, etc.) |
| 6 | Cognito → User pools | The AnimeRec user pool with at least one confirmed test user |
| 7 | S3 → Buckets | The frontend bucket and dataset bucket |
| 8 | CloudFront → Distributions | The distribution serving the React SPA, with the S3 origin visible |
| 9 | CloudWatch → Log groups | Log groups for at least 2-3 Lambda functions showing recent log streams |
| 10 | Browser | The live application — landing page, onboarding page, and recommendations page |

---

## Code Snippets

### 1. Recommendation Algorithm — Cosine Similarity (`backend/lambdas/recommendation/algorithm.py`)

The core of the recommendation engine. Each anime is represented as a weighted feature vector; cosine similarity measures how aligned two vectors are regardless of their magnitude.

```python
def normalize_vector(vec: Dict[str, float]) -> Dict[str, float]:
    """Normalize a vector so its magnitude is 1."""
    magnitude = math.sqrt(sum(v * v for v in vec.values()))
    if magnitude == 0:
        return vec
    return {k: v / magnitude for k, v in vec.items()}


def cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Compute cosine similarity between two vectors.

    Returns value in [0, 1] where 1 is perfect match.
    """
    if not vec_a or not vec_b:
        return 0.0
    vec_a_norm = normalize_vector(vec_a)
    vec_b_norm = normalize_vector(vec_b)
    dot = sum(vec_a_norm.get(k, 0.0) * vec_b_norm.get(k, 0.0) for k in vec_a_norm)
    return max(0.0, min(1.0, dot))
```

### 2. Feature Vector Construction (`backend/lambdas/recommendation/algorithm.py`)

Anime metadata (genres, studios, year, score, popularity) is encoded into a numeric vector. Each feature is independently weighted so genres matter more than release year.

```python
def build_anime_vector(anime: Dict, weight_genres: float = 1.0,
                       weight_studios: float = 0.5, weight_year: float = 0.3,
                       weight_score: float = 0.2, weight_popularity: float = 0.2
                       ) -> Dict[str, float]:
    vec = {}
    for genre in (anime.get("genres") or []):
        if isinstance(genre, str) and genre.strip():
            vec[f"genre:{genre}"] = vec.get(f"genre:{genre}", 0.0) + weight_genres

    for studio in (anime.get("studios") or []):
        if isinstance(studio, str) and studio.strip():
            vec[f"studio:{studio}"] = vec.get(f"studio:{studio}", 0.0) + weight_studios

    year = anime.get("year")
    if year is not None:
        year_norm = (int(year) - 1960) / (2030 - 1960)
        vec["year"] = max(0.0, min(1.0, year_norm)) * weight_year

    score = anime.get("score")
    if score is not None:
        vec["score"] = max(0.0, min(1.0, float(score) / 10.0)) * weight_score

    return vec
```

### 3. Popularity Blending (`backend/lambdas/recommendation/algorithm.py`)

Users can opt in to a popularity blend that weighs content similarity at 70% and normalized popularity at 30%, balancing personalization with discovery of well-regarded titles.

```python
def compose_recommendation_score(
    content_similarity: float,
    popularity_score: float,
    opt_in_popularity: bool = True
) -> float:
    content_sim = max(0.0, min(1.0, content_similarity))
    if opt_in_popularity:
        pop_norm = max(0.0, min(1.0, popularity_score / 100.0))
        return 0.7 * content_sim + 0.3 * pop_norm
    else:
        return content_sim
```

### 4. Authentication Lambda — Lambda Handler Response Format (`backend/lambdas/auth/handler.py`)

All Lambda functions return a consistent API Gateway proxy response with CORS headers. The auth Lambda calls Cognito's `initiateAuth` action and returns the JWT ID token to the frontend.

```python
def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
```

### 5. Infrastructure — Lambda Module (Terraform)

Each Lambda function is declared as a Terraform resource with its IAM role, environment variables, and zip package. Running `terraform apply` deploys all 8 functions consistently across environments.

```hcl
# infrastructure/terraform/modules/lambda/main.tf (representative excerpt)
resource "aws_lambda_function" "this" {
  function_name    = var.function_name
  filename         = var.zip_path
  source_code_hash = filebase64sha256(var.zip_path)
  handler          = var.handler
  runtime          = "python3.11"
  role             = aws_iam_role.lambda_exec.arn

  environment {
    variables = var.env_vars
  }
}
```

### 6. CI Pipeline — Lambda Zip Validation (`.github/workflows/ci.yml`)

The CI pipeline packages all 8 Lambdas and asserts exactly 8 zip files are produced, catching any missing or extra packages before deployment.

```yaml
- name: Package Lambdas
  run: bash scripts/package_lambdas.sh

- name: Validate zip count
  run: |
    count=$(find dist/lambdas -name '*.zip' | wc -l)
    [ "$count" -eq 8 ] || (echo "Expected 8 zips, got $count" && exit 1)
```

---

## Sample Output

### Recommendation API Response (example)

```json
{
  "status": "ready",
  "recommendations": [
    {
      "anime_id": "1535",
      "title": "Death Note",
      "score": 8.62,
      "genres": ["Mystery", "Psychological", "Supernatural", "Thriller"],
      "studios": ["Madhouse"],
      "similarity_score": 0.91,
      "final_score": 0.847
    },
    {
      "anime_id": "5114",
      "title": "Fullmetal Alchemist: Brotherhood",
      "score": 9.11,
      "genres": ["Action", "Adventure", "Drama", "Fantasy"],
      "studios": ["Bones"],
      "similarity_score": 0.83,
      "final_score": 0.793
    }
  ],
  "cached_at": "2026-04-22T18:30:00Z",
  "ttl": 86400
}
```

### Backend Test Results

```
pytest -q backend

...........................................................
57 passed in 3.42s
```
