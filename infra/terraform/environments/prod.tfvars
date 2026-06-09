# ──────────────────────────────────────────────
# Production Environment
# ──────────────────────────────────────────────

environment = "prod"
aws_region  = "us-east-1"
gcp_region  = "us-central1"
location    = "East US"

# ─── VPC / Networking ────────────────────────
cluster_name = "face-zero-trust-prod"
domain_name  = "facezero.trust"

# ─── Kubernetes ──────────────────────────────
eks_node_instance_types = ["m6i.xlarge"]
eks_desired_size        = 5
eks_min_size            = 3
eks_max_size            = 20

gke_machine_type = "e2-standard-4"
gke_min_node     = 3
gke_max_node     = 15

# ─── Redis ───────────────────────────────────
redis_node_type    = "cache.r6g.large"
redis_num_nodes    = 3
redis_memory_gb    = 13

# ─── Monitoring ──────────────────────────────
enable_monitoring   = true
enable_tracing      = true
log_retention_days  = 90

# ─── Quantum ─────────────────────────────────
enable_quantum      = true
braket_instance     = "ml.m5.large"

# ─── Security ────────────────────────────────
enable_waf              = true
enable_secret_rotation  = true
waf_rate_limit          = 1000

# ─── CDN / Edge ─────────────────────────────
enable_cdn          = true
enable_spectrum     = true
enable_workers      = true

# ─── Backups ─────────────────────────────────
backup_retention_days = 30
enable_cross_region   = true

# ─── High Availability ──────────────────────
multi_az           = true
deletion_protection = true

# ─── Tags ────────────────────────────────────
tags = {
  Environment = "prod"
  ManagedBy   = "terraform"
  Project     = "face-zero-trust"
  CostCenter  = "production"
  Compliance  = "soc2"
}
