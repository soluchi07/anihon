# Terraform backend configuration (stub)
# This file should be filled with your remote S3 backend and DynamoDB lock table configuration.

terraform {
  required_version = ">= 1.3.0"
  backend "s3" {
    bucket = "anime-rec-terraform-state"
    key    = "state/terraform.tfstate"
    region = "na-east"
    dynamodb_table = "anime-rec-terraform-lock"
  }
}
