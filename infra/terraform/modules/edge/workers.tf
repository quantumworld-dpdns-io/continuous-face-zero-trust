variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
}

variable "domain_name" {
  description = "Domain name"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID"
  type        = string
}

variable "kv_namespace_id" {
  description = "KV namespace ID for Workers"
  type        = string
  default     = ""
}

variable "r2_bucket_name" {
  description = "R2 bucket name"
  type        = string
  default     = ""
}

variable "durable_object_namespace_id" {
  description = "Durable Objects namespace ID"
  type        = string
  default     = ""
}

resource "cloudflare_worker_script" "api" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-api-${var.environment}"
  content    = file("${path.module}/scripts/api-worker.js")

  kv_namespace_binding {
    name         = "SESSION_STORE"
    namespace_id = var.kv_namespace_id
  }

  r2_bucket_binding {
    name        = "UPLOADS"
    bucket_name = var.r2_bucket_name
  }

  analytics_engine_binding {
    dataset = "api-analytics-${var.environment}"
  }

  webassembly_binding {
    name       = "WASM_MODULE"
    module     = "${path.module}/wasm/worker.wasm"
  }

  tags = ["face-zero-trust", var.environment]

  placement {
    mode = "smart"
  }
}

resource "cloudflare_worker_script" "auth" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-auth-${var.environment}"
  content    = file("${path.module}/scripts/auth-worker.js")

  kv_namespace_binding {
    name         = "AUTH_STORE"
    namespace_id = var.kv_namespace_id
  }

  webassembly_binding {
    name       = "WASM_AUTH"
    module     = "${path.module}/wasm/auth.wasm"
  }

  tags = ["face-zero-trust", "auth", var.environment]
}

resource "cloudflare_worker_script" "edge_router" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-edge-${var.environment}"
  content    = file("${path.module}/scripts/edge-router.js")

  kv_namespace_binding {
    name         = "ROUTING_RULES"
    namespace_id = var.kv_namespace_id
  }

  analytics_engine_binding {
    dataset = "edge-analytics-${var.environment}"
  }

  tags = ["face-zero-trust", "edge", var.environment]

  placement {
    mode = "smart"
  }
}

resource "cloudflare_worker_script" "static" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-static-${var.environment}"
  content    = file("${path.module}/scripts/static-worker.js")

  r2_bucket_binding {
    name        = "STATIC_ASSETS"
    bucket_name = var.r2_bucket_name
  }

  tags = ["face-zero-trust", "static", var.environment]
}

resource "cloudflare_worker_domain" "api" {
  account_id = var.cloudflare_account_id
  zone_id    = var.cloudflare_zone_id
  hostname   = "api.${var.domain_name}"
  service    = cloudflare_worker_script.api.name
}

resource "cloudflare_worker_domain" "auth" {
  account_id = var.cloudflare_account_id
  zone_id    = var.cloudflare_zone_id
  hostname   = "auth.${var.domain_name}"
  service    = cloudflare_worker_script.auth.name
}

resource "cloudflare_worker_domain" "edge" {
  account_id = var.cloudflare_account_id
  zone_id    = var.cloudflare_zone_id
  hostname   = "edge.${var.domain_name}"
  service    = cloudflare_worker_script.edge_router.name
}

resource "cloudflare_worker_cron_trigger" "scheduler" {
  account_id  = var.cloudflare_account_id
  script_name = cloudflare_worker_script.edge_router.name
  schedules   = ["0 */6 * * *"]
}

output "worker_urls" {
  value = {
    api     = "https://api.${var.domain_name}"
    auth    = "https://auth.${var.domain_name}"
    edge    = "https://edge.${var.domain_name}"
    static  = "https://${var.domain_name}"
  }
}
