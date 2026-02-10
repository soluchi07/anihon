variable "project_name" {
  description = "Project name"
  type        = string
}

variable "cognito_domain" {
  description = "Cognito domain name (must be globally unique)"
  type        = string
}

variable "callback_urls" {
  description = "Callback URLs for OAuth redirect (frontend)"
  type        = list(string)
  default = [
    "http://localhost:3001/callback",
    "http://localhost:3000/callback"
  ]
}

variable "logout_urls" {
  description = "Logout URLs for OAuth"
  type        = list(string)
  default = [
    "http://localhost:3001/logout",
    "http://localhost:3000/logout"
  ]
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
