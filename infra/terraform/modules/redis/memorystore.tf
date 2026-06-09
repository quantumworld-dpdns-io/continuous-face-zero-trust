variable "cluster_id" {
  description = "Memorystore instance ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "memory_size_gb" {
  description = "Memory size in GB"
  type        = number
  default     = 5
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "network_id" {
  description = "VPC network ID"
  type        = string
  default     = ""
}

variable "subnet_id" {
  description = "Subnet ID"
  type        = string
  default     = ""
}

resource "google_redis_instance" "main" {
  name           = var.cluster_id
  display_name   = "Redis ${var.environment}"
  memory_size_gb = var.memory_size_gb
  region         = var.gcp_region

  tier                   = "STANDARD_HA"
  redis_version          = "REDIS_7_0"
  redis_configs = {
    maxmemory-policy = "allkeys-lru"
  }

  network = var.network_id

  authorized_network = var.network_id

  labels = {
    environment = var.environment
    managed-by  = "terraform"
  }

  maintenance_policy {
    weekly_maintenance_window {
      day = "SUNDAY"
      start_time {
        hours   = 4
        minutes = 0
        seconds = 0
        nanos   = 0
      }
    }
  }
}

output "host" {
  value = google_redis_instance.main.host
}

output "port" {
  value = google_redis_instance.main.port
}
