// Root module variables
variable "project_name" {
  description = "Project name"
  type        = string
  default     = "animerec"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "frontend_domain" {
  description = "Frontend domain for CORS (CloudFront distribution domain or custom domain)"
  type        = string
  default     = "" # Will be set to CloudFront domain after deployment
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "tags" {
  description = "Global tags"
  type        = map(string)
  default     = {}
}

variable "cognito_domain" {
  description = "Cognito domain (must be globally unique)"
  type        = string
  default     = "animerec-auth"
}

variable "callback_urls" {
  description = "OAuth2 callback URLs for Cognito"
  type        = list(string)
  default = [
    "http://localhost:3001/callback",
    "http://localhost:3000/callback",
    "http://localhost:3001",
    "http://localhost:3000"
  ]
}

variable "logout_urls" {
  description = "OAuth2 logout URLs for Cognito"
  type        = list(string)
  default = [
    "http://localhost:3001/logout",
    "http://localhost:3000/logout",
    "http://localhost:3001",
    "http://localhost:3000"
  ]
}

