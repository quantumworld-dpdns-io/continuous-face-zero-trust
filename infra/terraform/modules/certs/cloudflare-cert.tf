variable "domain_name" {
  description = "Domain name for the certificate"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "cloudflare_zone_id" {
  description = "Cloudflare zone ID"
  type        = string
}

variable "request_validity" {
  description = "Certificate validity in months"
  type        = number
  default     = 12
}

resource "tls_private_key" "main" {
  algorithm = "ECDSA"
  ecdsa_curve = "P384"
}

resource "tls_cert_request" "main" {
  private_key_pem = tls_private_key.main.private_key_pem

  subject {
    common_name  = "*.${var.domain_name}"
    organization = "Face Zero Trust"
  }

  dns_names = [
    var.domain_name,
    "*.${var.domain_name}",
    "*.*.${var.domain_name}",
  ]
}

resource "cloudflare_origin_ca_certificate" "main" {
  request                = tls_cert_request.main.cert_request_pem
  requested_validity     = var.request_validity
  request_type           = "origin-rsa"
  csr                    = tls_cert_request.main.cert_request_pem
}

resource "aws_secretsmanager_secret" "tls_cert" {
  name                    = "face-zero-trust/${var.environment}/tls-cert"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "tls_cert" {
  secret_id = aws_secretsmanager_secret.tls_cert.id
  secret_string = jsonencode({
    certificate = tls_cert_request.main.cert_request_pem
    private_key = tls_private_key.main.private_key_pem
    ca_cert     = cloudflare_origin_ca_certificate.main.certificate
  })
}

output "certificate_id" {
  value = cloudflare_origin_ca_certificate.main.id
}

output "certificate" {
  value     = cloudflare_origin_ca_certificate.main.certificate
  sensitive = true
}
