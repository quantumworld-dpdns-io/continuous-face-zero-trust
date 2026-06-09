variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name"
  type        = string
}

locals {
  network_name = "face-zero-trust-${var.environment}"
  subnets = [
    {
      name   = "gke-subnet"
      cidr   = "10.1.0.0/20"
      region = var.gcp_region
    },
    {
      name   = "app-subnet"
      cidr   = "10.2.0.0/20"
      region = var.gcp_region
    },
    {
      name   = "db-subnet"
      cidr   = "10.3.0.0/20"
      region = var.gcp_region
    },
  ]
}

resource "google_compute_network" "vpc" {
  name                    = local.network_name
  auto_create_subnetworks = false
  routing_mode            = "REGIONAL"
}

resource "google_compute_subnetwork" "subnets" {
  for_each = { for s in local.subnets : s.name => s }

  name          = each.value.name
  ip_cidr_range = each.value.cidr
  region        = each.value.region
  network       = google_compute_network.vpc.id

  secondary_ip_range {
    range_name    = "gke-pods"
    ip_cidr_range = "10.100.0.0/16"
  }

  secondary_ip_range {
    range_name    = "gke-services"
    ip_cidr_range = "10.101.0.0/20"
  }
}

resource "google_compute_router" "router" {
  name    = "${local.network_name}-router"
  region  = var.gcp_region
  network = google_compute_network.vpc.id
}

resource "google_compute_router_nat" "nat" {
  name                               = "${local.network_name}-nat"
  router                             = google_compute_router.router.name
  region                             = var.gcp_region
  nat_ip_allocate_option             = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}

resource "google_compute_firewall" "allow_internal" {
  name    = "${local.network_name}-allow-internal"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
  }
  allow {
    protocol = "udp"
  }
  allow {
    protocol = "icmp"
  }

  source_ranges = ["10.0.0.0/8"]
}

output "vpc_id" {
  value = google_compute_network.vpc.id
}

output "subnet_ids" {
  value = { for k, v in google_compute_subnetwork.subnets : k => v.id }
}
