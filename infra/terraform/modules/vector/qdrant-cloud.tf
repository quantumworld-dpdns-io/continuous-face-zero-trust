variable "environment" {
  description = "Environment name"
  type        = string
}

variable "qdrant_api_key" {
  description = "Qdrant Cloud API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "cluster_name" {
  description = "Qdrant cluster name"
  type        = string
  default     = ""
}

locals {
  cluster_name = var.cluster_name != "" ? var.cluster_name : "face-zero-trust-${var.environment}"
}

resource "qdrant_cloud_cluster" "main" {
  name               = local.cluster_name
  cloud_type         = "aws"
  cloud_region       = "us-east-1"
  cluster_id         = ""
  deletion_protection = var.environment == "prod" ? true : false

  disk = {
    disk_size  = 50
    disk_type  = "gp3"
  }

  node_config = {
    cpu           = 4
    memory        = 8
    replicas      = var.environment == "prod" ? 3 : 1
  }

  cluster_id = ""
}

resource "qdrant_cloud_api_key" "main" {
  cluster_id = qdrant_cloud_cluster.main.id
  name       = "terraform-${var.environment}"
  role       = "read-write"
}

output "cluster_url" {
  value = "https://${qdrant_cloud_cluster.main.id}.cloud.qdrant.io:6333"
}

output "api_key_id" {
  value = qdrant_cloud_api_key.main.id
}
