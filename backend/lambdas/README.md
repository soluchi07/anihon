Backend Lambda functions

Overview
- Functions are placed under `backend/lambdas/<function_name>/`.
- Each function should have a `handler.py` with `handler(event, context)` entrypoint.
- Environment variables should be used for table names and S3 bucket keys.

Planned functions
- data_ingest: load cleaned JSONL from S3 into Anime table
- recommendation: exposes scoring functions and optionally a sync handler
- recommendation_worker: scheduled worker to compute and cache recommendations
- interactions: like/rate/list endpoints
- anime_getter: GET endpoints for anime metadata
- auth helpers: cognito integration helpers

Testing
- Put unit tests under `backend/lambdas/<fn>/tests/` and run `pytest` in CI.
