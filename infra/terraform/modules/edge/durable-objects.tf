variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
}

variable "worker_script_name" {
  description = "Worker script name to bind Durable Objects to"
  type        = string
  default     = ""
}

resource "cloudflare_workers_durable_object_namespace" "main" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-do-${var.environment}"
}

resource "cloudflare_workers_durable_object_namespace" "sessions" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-sessions-${var.environment}"
}

resource "cloudflare_workers_durable_object_namespace" "rate_limiter" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-rate-limit-${var.environment}"
}

resource "cloudflare_workers_durable_object_namespace" "analytics" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-analytics-${var.environment}"
}

resource "cloudflare_workers_durable_object_namespace" "game_state" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-game-state-${var.environment}"
}

resource "cloudflare_workers_durable_object_namespace" "notification" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-notification-${var.environment}"
}

resource "cloudflare_workers_durable_object_namespace" "ai_cache" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-ai-cache-${var.environment}"
}

output "namespace_id" {
  value = cloudflare_workers_durable_object_namespace.main.id
}

output "namespace_ids" {
  value = {
    main         = cloudflare_workers_durable_object_namespace.main.id
    sessions     = cloudflare_workers_durable_object_namespace.sessions.id
    rate_limiter = cloudflare_workers_durable_object_namespace.rate_limiter.id
    analytics    = cloudflare_workers_durable_object_namespace.analytics.id
    game_state   = cloudflare_workers_durable_object_namespace.game_state.id
    notification = cloudflare_workers_durable_object_namespace.notification.id
    ai_cache     = cloudflare_workers_durable_object_namespace.ai_cache.id
  }
}
