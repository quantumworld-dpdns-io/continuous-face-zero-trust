variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cluster_name" {
  description = "Cluster name"
  type        = string
}

variable "alert_manager_email" {
  description = "Email for alert manager"
  type        = string
  default     = "ops@facezero.trust"
}

resource "aws_prometheus_workspace" "main" {
  alias = "amp-${var.environment}"

  tags = {
    Environment = var.environment
    Cluster     = var.cluster_name
  }
}

resource "aws_prometheus_alert_manager_definition" "main" {
  workspace_id = aws_prometheus_workspace.main.id

  definition = yamlencode({
    global = {
      resolve_timeout = "5m"
    }
    route = {
      receiver        = "default"
      group_wait      = "30s"
      group_interval  = "5m"
      repeat_interval = "4h"
      routes = [
        {
          receiver = "critical"
          match = {
            severity = "critical"
          }
          continue = true
        }
      ]
    }
    receivers = [
      {
        name = "default"
        email_configs = [
          {
            to            = var.alert_manager_email
            send_resolved = true
          }
        ]
      },
      {
        name = "critical"
        email_configs = [
          {
            to            = var.alert_manager_email
            send_resolved = true
          }
        ]
      }
    ]
  })
}

resource "aws_prometheus_rule_group_namespace" "main" {
  workspace_id = aws_prometheus_workspace.main.id
  name         = "face-zero-trust-${var.environment}"
  data         = file("${path.module}/rules.yaml")
}

resource "aws_prometheus_query_alias" "main" {
  workspace_id = aws_prometheus_workspace.main.id
  alias        = "prom"
}

output "workspace_id" {
  value = aws_prometheus_workspace.main.id
}

output "workspace_endpoint" {
  value = aws_prometheus_workspace.main.prometheus_endpoint
}

output "workspace_arn" {
  value = aws_prometheus_workspace.main.arn
}
