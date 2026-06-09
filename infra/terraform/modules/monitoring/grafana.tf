variable "environment" {
  description = "Environment name"
  type        = string
}

variable "grafana_api_key" {
  description = "Grafana Cloud API key"
  type        = string
  sensitive   = true
  default     = ""
}

variable "stack_id" {
  description = "Grafana Cloud stack ID"
  type        = string
  default     = ""
}

variable "prometheus_endpoint" {
  description = "Prometheus endpoint to connect"
  type        = string
  default     = ""
}

variable "prometheus_username" {
  description = "Prometheus basic auth username"
  type        = string
  default     = ""
}

resource "grafana_cloud_stack" "main" {
  name   = "face-zero-trust-${var.environment}"
  region = "us"
}

resource "grafana_cloud_api_key" "main" {
  cloud_stack_slug = grafana_cloud_stack.main.slug
  name             = "terraform-${var.environment}"
  role             = "Admin"
  expires_at       = ""
}

resource "grafana_data_source" "prometheus" {
  stack_id = grafana_cloud_stack.main.stack_id
  type     = "prometheus"
  name     = "Prometheus-${var.environment}"

  basic_auth_enabled  = true
  basic_auth_username = var.prometheus_username

  json_data_encoded = jsonencode({
    httpMethod         = "POST"
    url                = var.prometheus_endpoint
    sigV4Auth          = false
    sigV4AuthType      = "default"
    sigV4ExternalLabels = ""
    sigV4Name          = ""
    sigV4Region        = ""
    sigV4RoleArn       = ""
    tlsAuth            = false
    tlsAuthWithCACert  = false
  })
}

resource "grafana_dashboard" "main" {
  for_each = fileset("${path.module}/dashboards/", "*.json")

  config_json = file("${path.module}/dashboards/${each.value}")
  folder      = "face-zero-trust-${var.environment}"
}

resource "grafana_alert_policy" "main" {
  stack_id = grafana_cloud_stack.main.stack_id
  name     = "High Error Rate-${var.environment}"

  notification_policy {
    group_by      = ["grafana_folder", "alertname"]
    contact_points = []
  }
}

output "workspace_id" {
  value = grafana_cloud_stack.main.stack_id
}

output "grafana_url" {
  value = grafana_cloud_stack.main.url
}

output "api_key_id" {
  value = grafana_cloud_api_key.main.id
}
