variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "cloudflare_api_token" {
  description = "Cloudflare API token"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "quantum_enabled" {
  description = "Enable quantum services"
  type        = bool
  default     = false
}

variable "cluster_name" {
  description = "Kubernetes cluster name"
  type        = string
  default     = "cfzt-cluster"
}
