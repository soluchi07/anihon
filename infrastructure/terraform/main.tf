// DynamoDB module
module "dynamodb" {
  source = "./modules/dynamodb"

  project_name = var.project_name
  tags         = local.common_tags
}

// Data ingest Lambda configuration
// This module provisions the data_ingest Lambda with S3 and DynamoDB permissions

module "data_ingest_lambda" {
  source = "./modules/lambda"

  project_name      = var.project_name
  function_name     = "data-ingest"
  source_code_path  = "${path.module}/../../backend/lambdas/data_ingest/handler.py"
  handler           = "handler.handler"
  runtime           = "python3.10"
  timeout           = 600
  memory_size       = 512
  tags              = local.common_tags

  environment_vars = {
    ANIME_TABLE  = module.dynamodb.anime_table_name
    DATA_BUCKET  = aws_s3_bucket.data_bucket.id
    DATA_KEY     = "cleaned/anime_meta_cleaned.jsonl"
  }
}

// S3 bucket for cleaned data
resource "aws_s3_bucket" "data_bucket" {
  bucket = "${var.project_name}-data"
  tags   = local.common_tags
}

// IAM policy for data_ingest to read from S3 and write to DynamoDB
resource "aws_iam_role_policy" "data_ingest_policy" {
  name = "${var.project_name}-data-ingest-policy"
  role = module.data_ingest_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject"
        ]
        Resource = "${aws_s3_bucket.data_bucket.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:BatchWriteItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = module.dynamodb.anime_table_arn
      }
    ]
  })
}

locals {
  common_tags = merge(var.tags, {
    Environment = "dev"
    Project     = var.project_name
  })
}
