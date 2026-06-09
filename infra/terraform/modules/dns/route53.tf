variable "domain_name" {
  description = "Domain name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

resource "aws_route53_zone" "main" {
  name = var.domain_name

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "aws_route53_record" "api" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "api.${var.domain_name}"
  type    = "A"

  alias {
    name                   = "dualstack.${var.environment}-api.facezero.trust"
    zone_id                = "Z1234567890ABC"
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "mx" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "MX"
  ttl     = 300

  records = [
    "10 mx1.emailprovider.com",
    "20 mx2.emailprovider.com",
  ]
}

resource "aws_route53_record" "txt" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.domain_name
  type    = "TXT"
  ttl     = 300

  records = [
    "v=spf1 include:_spf.emailprovider.com ~all",
  ]
}

resource "aws_route53_record" "cname_www" {
  zone_id = aws_route53_zone.main.zone_id
  name    = "www.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300

  records = [var.domain_name]
}

output "zone_id" {
  value = aws_route53_zone.main.zone_id
}

output "nameservers" {
  value = aws_route53_zone.main.name_servers
}
