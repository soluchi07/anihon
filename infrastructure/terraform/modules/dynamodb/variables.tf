variable "project_name" {
  description = "Project name prefix for DynamoDB tables"
  type        = string
  default     = "animerec"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
