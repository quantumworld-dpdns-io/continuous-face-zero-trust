variable "domain_name" {
  description = "Domain name"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
  default     = ""
}

resource "cloudflare_zone" "main" {
  account_id = var.cloudflare_account_id
  zone       = var.domain_name
  plan       = "business"
  type       = "full"
}

resource "cloudflare_zone_settings_override" "main" {
  zone_id = cloudflare_zone.main.id

  settings {
    always_use_https         = "on"
    automatic_https_rewrites = "on"
    brotli                   = "on"
    early_hints              = "on"
    min_tls_version          = "1.2"
    ssl                      = "strict"
    tls_1_3                  = "on"

    security_level {
      value = "high"
    }

    browser_check {
      value = "on"
    }

    challenge_ttl {
      value = 1800
    }

    privacy_pass {
      value = "on"
    }

    waf {
      value = "on"
    }

    rocket_loader {
      value = "on"
    }
  }
}

resource "cloudflare_record" "api" {
  zone_id = cloudflare_zone.main.id
  name    = "api.${var.domain_name}"
  content = "api.facezero.trust"
  type    = "CNAME"
  ttl     = 1
  proxied = true
}

resource "cloudflare_record" "www" {
  zone_id = cloudflare_zone.main.id
  name    = "www.${var.domain_name}"
  content = "facezero.trust"
  type    = "CNAME"
  ttl     = 1
  proxied = true
}

output "zone_id" {
  value = cloudflare_zone.main.id
}

output "name_servers" {
  value = cloudflare_zone.main.name_servers
}
