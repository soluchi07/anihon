provider "aws" {
  region = "us-east-1"
  # profile can be set via TF_VAR_aws_profile or environment variables in CI
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}
