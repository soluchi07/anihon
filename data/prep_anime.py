"""
data/prep_anime.py

Streaming JSON cleaner & uploader for Jikan-format anime metadata.

Behavior:
- Remove records where "type" == "Music".
- Set null `score` → 5.0.
- Two-pass approach: first pass discovers max popularity rank, second pass writes cleaned JSONL with normalized `popularity_score`.
- Extract useful fields: `anime_id` (mal_id), `title`, `alternate_titles`, `genres`, `studios`, `synopsis`, `episodes`, `year`, `type`, `rating`, `score`, `popularity`, `popularity_score`, `favorites`, `image_url` (images.jpg.large_image_url preferred).
- Optional upload to S3; uses boto3 if available.

Usage examples:
  python data/prep_anime.py --input data/anime_meta.json --out data/cleaned/anime_meta_cleaned.jsonl --upload --s3-bucket animerec-data --profile default

Flags:
  --input, --out, --upload, --s3-bucket, --s3-key, --dry-run, --profile, --sample-only

Notes:
- Uses ijson for streaming if installed, falls back to json.load with a memory warning.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from datetime import datetime

logger = logging.getLogger("prep_anime")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

SAMPLE_OUTPUT = "data/cleaned/anime_meta_cleaned-sample.jsonl"


def parse_args():
    p = argparse.ArgumentParser(description="Clean Jikan anime metadata and upload to S3")
    p.add_argument("--input", default="data/anime_meta.json", help="Path to raw JSON array file")
    p.add_argument("--out", default=SAMPLE_OUTPUT, help="Output JSONL file path")
    p.add_argument("--upload", action="store_true", help="Upload cleaned file to S3")
    p.add_argument("--s3-bucket", default="", help="S3 bucket name for upload")
    p.add_argument("--s3-key", default="cleaned/anime_meta_cleaned.jsonl", help="S3 key for upload")
    p.add_argument("--dry-run", action="store_true", help="Perform a dry-run without writing output")
    p.add_argument("--profile", default="default", help="AWS profile name for upload")
    p.add_argument("--sample-only", action="store_true", help="Write a small sample output only")
    return p.parse_args()


def stream_items(path):
    """Yield top-level items from a JSON array in file.

    Tries to use ijson for low-memory streaming; falls back to json.load.
    """
    try:
        import ijson
        logger.info("Using ijson for streaming parsing")
        with open(path, "rb") as f:
            for item in ijson.items(f, "item"):
                yield item
    except Exception:
        logger.warning("ijson not available or failed, falling back to json.load (may use more memory)")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, list):
                logger.error("Expected top-level JSON array in input file")
                return
            for item in data:
                yield item


def extract_alternate_titles(item):
    titles = set()
    if item.get("title"):
        titles.add(item.get("title"))
    if item.get("title_english"):
        titles.add(item.get("title_english"))
    if item.get("title_japanese"):
        titles.add(item.get("title_japanese"))
    for t in item.get("title_synonyms", []) or []:
        if t:
            titles.add(t)
    for entry in item.get("titles", []) or []:
        if isinstance(entry, dict) and entry.get("title"):
            titles.add(entry.get("title"))
    # remove empty and return list
    return [t for t in titles if t]


def pick_image_url(item):
    imgs = item.get("images") or {}
    jpg = imgs.get("jpg") if isinstance(imgs.get("jpg"), dict) else None
    webp = imgs.get("webp") if isinstance(imgs.get("webp"), dict) else None
    # prefer large_image_url in jpg then webp then fallbacks
    for candidate in (jpg, webp):
        if candidate:
            for key in ("large_image_url", "image_url", "small_image_url"):
                url = candidate.get(key)
                if url:
                    return url
    return None


def normalize_popularity_score(rank, max_rank):
    try:
        rank = int(rank)
    except Exception:
        rank = max_rank
    if max_rank <= 0:
        return 0.0
    score = (max_rank - rank) / max_rank * 100.0
    if score < 0:
        score = 0.0
    return float(score)


def upload_to_s3(local_path, bucket, key, profile):
    try:
        import boto3
    except ImportError:
        logger.error("boto3 is required for S3 upload. Install boto3 or skip --upload flag.")
        return False
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    s3 = session.client("s3")
    logger.info("Uploading %s to s3://%s/%s", local_path, bucket, key)
    s3.upload_file(str(local_path), bucket, key)
    return True


def run_clean(input_path, out_path, dry_run=False, sample_only=False, upload=False, s3_bucket=None, s3_key=None, profile="default"):
    # First pass: determine max popularity rank and counts
    total = 0
    removed_music = 0
    max_rank = 0
    items_with_popularity = 0

    logger.info("Pass 1: scanning for popularity ranks and counts")
    for item in stream_items(input_path):
        total += 1
        if item.get("type") == "Music":
            removed_music += 1
            continue
        pop = item.get("popularity")
        if pop is not None:
            try:
                p = int(pop)
                if p > max_rank:
                    max_rank = p
                items_with_popularity += 1
            except Exception:
                pass
    if items_with_popularity == 0:
        # fallback: use total as max_rank to avoid division by zero
        max_rank = total
    logger.info("Scanned %d items: removed Music=%d, max_rank=%d", total, removed_music, max_rank)

    if sample_only:
        logger.info("Sample only requested; producing sample output and exiting")

    # Second pass: process and write cleaned JSONL
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    processed = 0
    skipped = 0
    written = 0

    if not dry_run:
        out_file = open(out_path, "w", encoding="utf-8")

    logger.info("Pass 2: writing cleaned records to %s", out_path if not dry_run else "(dry-run)")
    for item in stream_items(input_path):
        if item.get("type") == "Music":
            skipped += 1
            continue
        mal_id = item.get("mal_id")
        if mal_id is None:
            logger.warning("Skipping record with no mal_id: %s", (item.get("title") or "<no title>"))
            skipped += 1
            continue
        title = item.get("title") or item.get("title_english") or item.get("title_japanese") or ""
        if not title:
            logger.warning("Skipping record mal_id=%s with no title", mal_id)
            skipped += 1
            continue

        # alternate titles
        alt_titles = extract_alternate_titles(item)

        # genres
        genres = [g.get("name") for g in (item.get("genres") or []) if isinstance(g, dict) and g.get("name")]

        # studios
        studios = [s.get("name") for s in (item.get("studios") or []) if isinstance(s, dict) and s.get("name")]

        # images
        image_url = pick_image_url(item)

        # score handling
        score = item.get("score")
        if score is None:
            score = 5.0
        else:
            try:
                score = float(score)
            except Exception:
                score = 5.0

        # popularity and normalized score
        pop_rank = item.get("popularity")
        try:
            current_rank = int(pop_rank) if pop_rank is not None else max_rank
        except Exception:
            current_rank = max_rank
        popularity_score = normalize_popularity_score(current_rank, max_rank)

        cleaned = {
            "anime_id": int(mal_id),
            "title": title,
            "alternate_titles": alt_titles,
            "genres": genres,
            "studios": studios,
            "synopsis": item.get("synopsis"),
            "episodes": item.get("episodes"),
            "year": item.get("year"),
            "type": item.get("type"),
            "rating": item.get("rating"),
            "score": score,
            "popularity": item.get("popularity"),
            "popularity_score": round(popularity_score, 4),
            "favorites": item.get("favorites", 0),
            "image_url": image_url,
        }

        processed += 1
        if dry_run:
            # just count
            continue

        # write to JSONL
        out_file.write(json.dumps(cleaned, ensure_ascii=False) + "\n")
        written += 1

        # optionally short-circuit if sample_only
        if sample_only and written >= 50:
            logger.info("Sample-only mode: wrote %d records", written)
            break

    if not dry_run:
        out_file.close()

    logger.info("Finished: total=%d processed=%d skipped=%d written=%d", total, processed, skipped, written)

    # Optionally upload to S3
    if upload and not dry_run and s3_bucket:
        success = upload_to_s3(out_path, s3_bucket, s3_key, profile)
        if success:
            logger.info("Upload succeeded: s3://%s/%s", s3_bucket, s3_key)
        else:
            logger.error("Upload failed or boto3 missing")

    return {
        "total": total,
        "removed_music": removed_music,
        "processed": processed,
        "skipped": skipped,
        "written": written,
        "out_path": str(out_path) if not dry_run else None,
    }


def main():
    args = parse_args()
    logger.info("Starting data prep: input=%s out=%s", args.input, args.out)

    result = run_clean(
        args.input,
        args.out,
        dry_run=args.dry_run,
        sample_only=args.sample_only,
        upload=args.upload,
        s3_bucket=args.s3_bucket,
        s3_key=args.s3_key,
        profile=args.profile,
    )

    if args.dry_run:
        logger.info("Dry-run complete. Would have processed: total=%d, removed_music=%d", result["total"], result["removed_music"])
    else:
        logger.info("Data prep complete. Wrote %d records to %s", result["written"], result["out_path"])

    return 0


if __name__ == "__main__":
    sys.exit(main())
