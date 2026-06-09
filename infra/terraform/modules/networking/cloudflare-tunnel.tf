variable "environment" {
  description = "Environment name"
  type        = string
}

variable "tunnel_name" {
  description = "Tunnel name"
  type        = string
  default     = ""
}

variable "cloudflare_account_id" {
  description = "Cloudflare account ID"
  type        = string
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID"
  type        = string
}

variable "domain_name" {
  description = "Domain name"
  type        = string
}

variable "origin_services" {
  description = "Map of service name to origin URL"
  type = map(object({
    origin_url  = string
    host_header = string
    noTLSVerify = bool
  }))
  default = {
    api = {
      origin_url  = "https://api.internal.facezero.trust:443"
      host_header = "api.facezero.trust"
      noTLSVerify = false
    }
    web = {
      origin_url  = "https://web.internal.facezero.trust:443"
      host_header = "facezero.trust"
      noTLSVerify = false
    }
  }
}

locals {
  tunnel_name = var.tunnel_name != "" ? var.tunnel_name : "face-zero-trust-${var.environment}"
}

resource "cloudflare_tunnel" "main" {
  account_id = var.cloudflare_account_id
  name       = local.tunnel_name
  secret     = base64encode(random_password.tunnel_secret.result)
}

resource "random_password" "tunnel_secret" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret" "tunnel_secret" {
  name                    = "face-zero-trust/${var.environment}/cloudflare-tunnel-secret"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "tunnel_secret" {
  secret_id     = aws_secretsmanager_secret.tunnel_secret.id
  secret_string = random_password.tunnel_secret.result
}

resource "cloudflare_tunnel_config" "main" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_tunnel.main.id

  config {
    dynamic "ingress" {
      for_each = var.origin_services
      content {
        hostname = "${ingress.key}.${var.domain_name}"
        service  = ingress.value.origin_url

        origin_request {
          noTLSVerify    = ingress.value.noTLSVerify
          http_host_header = ingress.value.host_header
          connect_timeout = "10s"

          tls {
            tls_verify        = !ingress.value.noTLSVerify
            sni               = ingress.value.host_header
          }
        }
      }
    }

    ingress {
      service = "http_status:404"
    }
  }
}

resource "cloudflare_dns_record" "tunnel" {
  for_each = var.origin_services

  zone_id = var.cloudflare_zone_id
  name    = "${each.key}.${var.domain_name}"
  content = "${cloudflare_tunnel.main.id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_dns_record" "catch_all" {
  zone_id = var.cloudflare_zone_id
  name    = "*.${var.domain_name}"
  content = "${cloudflare_tunnel.main.id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
}

resource "cloudflare_tunnel_route" "private" {
  account_id = var.cloudflare_account_id
  tunnel_id  = cloudflare_tunnel.main.id
  network    = "10.0.0.0/8"
  virtual_network_id = cloudflare_virtual_network.main.id
}

resource "cloudflare_virtual_network" "main" {
  account_id = var.cloudflare_account_id
  name       = "face-zero-trust-${var.environment}"
  description = "Virtual network for ${var.environment}"
}

output "tunnel_id" {
  value = cloudflare_tunnel.main.id
}

output "tunnel_name" {
  value = cloudflare_tunnel.main.name
}

output "tunnel_secret_arn" {
  value = aws_secretsmanager_secret.tunnel_secret.arn
}
