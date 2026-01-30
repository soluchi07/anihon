# Terraform backend configuration
# Using local backend for development
# TODO: Migrate to S3 backend once AWS credentials are configured

terraform {
  required_version = ">= 1.3.0"
  
  # Local backend for now
  backend "local" {
    path = "terraform.tfstate"
  }
  
  # Uncomment and configure when ready for remote state:
  # backend "s3" {
  #   bucket         = "anime-rec-terraform-state"
  #   key            = "state/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "anime-rec-terraform-lock"
  # }
}
