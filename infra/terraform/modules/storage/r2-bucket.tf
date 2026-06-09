variable "environment" {
  description = "Environment name"
  type        = string
}

variable "bucket_prefix" {
  description = "Bucket name prefix"
  type        = string
  default     = "face-zero-trust"
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
  default     = ""
}

resource "cloudflare_r2_bucket" "main" {
  account_id = var.cloudflare_account_id
  name       = "${var.bucket_prefix}-${var.environment}"
  location   = "auto"

  storage_class = "Standard"

  lifecycle_rule {
    enabled = true

    transition {
      days          = 30
      storage_class = "InfrequentAccess"
    }

    transition {
      days          = 90
      storage_class = "Glacier"
    }
  }
}

resource "cloudflare_r2_bucket" "backups" {
  account_id = var.cloudflare_account_id
  name       = "${var.bucket_prefix}-${var.environment}-backups"
  location   = "auto"

  storage_class = "Standard"
}

resource "cloudflare_r2_bucket_cors" "main" {
  bucket_name = cloudflare_r2_bucket.main.name

  cors_rule {
    allowed_origins = ["https://${var.environment}.facezero.trust"]
    allowed_methods = ["GET", "PUT", "HEAD"]
    allowed_headers = ["*"]
    max_age_seconds = 3600
  }
}

output "bucket_name" {
  value = cloudflare_r2_bucket.main.name
}

output "bucket_arn" {
  value = "arn:aws:s3:::${cloudflare_r2_bucket.main.name}"
}
