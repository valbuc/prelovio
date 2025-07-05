variable "project_id" {
  description = "The Google Cloud project ID"
  type        = string
}

variable "region" {
  description = "The Google Cloud region"
  type        = string
  default     = "europe-west1"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}