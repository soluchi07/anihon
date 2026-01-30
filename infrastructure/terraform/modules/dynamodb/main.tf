// DynamoDB tables for AnimeRec

// Anime table
resource "aws_dynamodb_table" "anime" {
  name           = "${var.project_name}-anime"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "anime_id"

  attribute {
    name = "anime_id"
    type = "N"
  }

  attribute {
    name = "genre"
    type = "S"
  }

  attribute {
    name = "year"
    type = "N"
  }

  // GSI: query by genre (single-valued)
  global_secondary_index {
    name            = "genre-index"
    hash_key        = "genre"
    projection_type = "KEYS_ONLY"
  }

  // GSI: query by year
  global_secondary_index {
    name            = "year-index"
    hash_key        = "year"
    projection_type = "ALL"
  }

  tags = var.tags
}

// Users table
resource "aws_dynamodb_table" "users" {
  name           = "${var.project_name}-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  tags = var.tags
}

// UserAnimeInteractions table
resource "aws_dynamodb_table" "interactions" {
  name           = "${var.project_name}-interactions"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"
  range_key      = "anime_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "anime_id"
    type = "N"
  }

  tags = var.tags
}

// RecommendationCache table with TTL
resource "aws_dynamodb_table" "recommendation_cache" {
  name           = "${var.project_name}-recommendation-cache"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  tags = var.tags
}
