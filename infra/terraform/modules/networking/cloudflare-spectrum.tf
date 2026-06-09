variable "environment" {
  description = "Environment name"
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

variable "origin_ip" {
  description = "Origin server IP address"
  type        = string
}

variable "protocol" {
  description = "Protocol to tunnel"
  type        = string
  default     = "tcp"
}

locals {
  spectrum_apps = {
    "ssh" = {
      port           = 22
      protocol       = "tcp/22"
      origin_dns     = "ssh-origin.${var.domain_name}"
      origin_port    = 22
      connect_timeout = 10000
    }
    "game-tcp" = {
      port           = 7777
      protocol       = "tcp/7777"
      origin_dns     = "game-origin.${var.domain_name}"
      origin_port    = 7777
      connect_timeout = 10000
    }
    "game-udp" = {
      port           = 7778
      protocol       = "udp/7778"
      origin_dns     = "game-origin.${var.domain_name}"
      origin_port    = 7778
      connect_timeout = 10000
    }
    "mqtt" = {
      port           = 8883
      protocol       = "tcp/8883"
      origin_dns     = "mqtt-origin.${var.domain_name}"
      origin_port    = 8883
      connect_timeout = 10000
    }
  }
}

resource "cloudflare_spectrum_application" "apps" {
  for_each = local.spectrum_apps

  zone_id          = var.cloudflare_zone_id
  protocol         = each.value.protocol
  dns              = each.value.dns
  origin_direct    = ["${var.origin_ip}:${each.value.origin_port}"]
  origin_dns       = each.value.origin_dns
  origin_port      = each.value.origin_port
  ip_firewall_enabled = true

  edge_ips {
    type        = contains(each.value.protocol, "udp") ? "udp" : "dynamic"
    connectivity = "all"
  }

  tls = "1.2"

  connect_timeout = each.value.connect_timeout
}

resource "cloudflare_spectrum_application" "custom" {
  count = var.origin_ip != "" ? 1 : 0

  zone_id       = var.cloudflare_zone_id
  protocol      = "${var.protocol}/${var.port}"
  dns           = "${var.protocol}-facezero.${var.domain_name}"
  origin_direct = ["${var.origin_ip}:${var.port}"]
  origin_port   = var.port

  edge_ips {
    type        = "dynamic"
    connectivity = "all"
  }

  tls = "1.2"
}

variable "port" {
  description = "Port for custom Spectrum app"
  type        = number
  default     = 443
}

resource "cloudflare_spectrum_application" "dns_tcp" {
  zone_id          = var.cloudflare_zone_id
  protocol         = "tcp/53"
  dns              = "dns-facezero.${var.domain_name}"
  origin_direct    = ["${var.origin_ip}:53"]
  origin_port      = 53
  ip_firewall_enabled = true

  edge_ips {
    type        = "ipv4"
    connectivity = "all"
  }

  tls = "off"
}

resource "cloudflare_dns_record" "spectrum" {
  for_each = local.spectrum_apps

  zone_id = var.cloudflare_zone_id
  name    = "${each.key}-facezero.${var.domain_name}"
  content = var.origin_ip
  type    = "A"
  proxied = false
}

output "app_ids" {
  value = { for k, v in cloudflare_spectrum_application.apps : k => v.id }
}

output "app_id" {
  value = try(cloudflare_spectrum_application.apps["ssh"].id, "")
}
