# ──────────────────────────────────────────────
# Dev Environment
# ──────────────────────────────────────────────

environment = "dev"
aws_region  = "us-east-1"
gcp_region  = "us-central1"
location    = "East US"

# ─── VPC / Networking ────────────────────────
cluster_name = "face-zero-trust-dev"
domain_name  = "facezero.trust"

# ─── Kubernetes ──────────────────────────────
eks_node_instance_types = ["m6i.large"]
eks_desired_size        = 2
eks_min_size            = 1
eks_max_size            = 4

gke_machine_type = "e2-standard-2"
gke_min_node     = 1
gke_max_node     = 3

# ─── Redis ───────────────────────────────────
redis_node_type    = "cache.t3.medium"
redis_num_nodes    = 1
redis_memory_gb    = 1

# ─── Monitoring ──────────────────────────────
enable_monitoring   = true
enable_tracing      = true
log_retention_days  = 7

# ─── Quantum ─────────────────────────────────
enable_quantum      = false
braket_instance     = "ml.t3.medium"

# ─── Security ────────────────────────────────
enable_waf              = true
enable_secret_rotation  = false
waf_rate_limit          = 5000

# ─── CDN / Edge ─────────────────────────────
enable_cdn          = true
enable_spectrum     = false
enable_workers      = true

# ─── Backups ─────────────────────────────────
backup_retention_days = 3
enable_cross_region   = false

# ─── Tags ────────────────────────────────────
tags = {
  Environment = "dev"
  ManagedBy   = "terraform"
  Project     = "face-zero-trust"
  CostCenter  = "engineering"
}
