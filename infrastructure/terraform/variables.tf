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
  default     = ""  # Will be set to CloudFront domain after deployment
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
