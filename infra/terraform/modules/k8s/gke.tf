variable "cluster_name" {
  description = "GKE cluster name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "gcp_project" {
  description = "GCP project ID"
  type        = string
  default     = ""
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

resource "google_container_cluster" "main" {
  name     = var.cluster_name
  location = var.gcp_region

  remove_default_node_pool = true
  initial_node_count       = 1

  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = "172.16.0.0/28"
  }

  release_channel {
    channel = "REGULAR"
  }

  workload_identity_config {
    workload_pool = "${var.gcp_project}.svc.id.goog"
  }
}

resource "google_container_node_pool" "primary" {
  name       = "${var.cluster_name}-pool"
  location   = var.gcp_region
  cluster    = google_container_cluster.main.name
  node_count = 3

  node_config {
    machine_type = "e2-standard-4"
    disk_size_gb = 100
    disk_type    = "pd-ssd"

    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    labels = {
      environment = var.environment
      cluster     = var.cluster_name
    }

    workload_metadata_config {
      mode = "GKE_METADATA"
    }
  }

  autoscaling {
    min_node_count = 1
    max_node_count = 10
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }
}

output "cluster_endpoint" {
  value = google_container_cluster.main.endpoint
}

output "cluster_name" {
  value = google_container_cluster.main.name
}
