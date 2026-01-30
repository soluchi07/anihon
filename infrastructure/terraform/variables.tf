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

variable "tags" {
  description = "Global tags"
  type        = map(string)
  default     = {}
}
