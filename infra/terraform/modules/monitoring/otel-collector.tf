variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cluster_name" {
  description = "Cluster name"
  type        = string
  default     = ""
}

variable "collector_image" {
  description = "OTel collector Docker image"
  type        = string
  default     = "otel/opentelemetry-collector-contrib:0.96.0"
}

variable "prometheus_endpoint" {
  description = "Prometheus remote write endpoint"
  type        = string
  default     = ""
}

variable "jaeger_endpoint" {
  description = "Jaeger endpoint for traces"
  type        = string
  default     = ""
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "monitoring"
}

resource "helm_release" "otel_collector" {
  name       = "otel-collector"
  repository = "https://open-telemetry.github.io/opentelemetry-helm-charts"
  chart      = "opentelemetry-collector"
  version    = "0.86.0"
  namespace  = var.namespace

  set {
    name  = "mode"
    value = "deployment"
  }

  set {
    name  = "image.repository"
    value = split(":", var.collector_image)[0]
  }

  set {
    name  = "image.tag"
    value = split(":", var.collector_image)[1]
  }

  set {
    name  = "resources.limits.cpu"
    value = "500m"
  }

  set {
    name  = "resources.limits.memory"
    value = "512Mi"
  }

  set {
    name  = "service.type"
    value = "ClusterIP"
  }

  values = [yamlencode({
    config = {
      receivers = {
        otlp = {
          protocols = {
            grpc = {
              endpoint = "0.0.0.0:4317"
            }
            http = {
              endpoint = "0.0.0.0:4318"
            }
          }
        }
        prometheus = {
          config = {
            scrape_configs = [
              {
                job_name     = "otel-collector"
                scrape_interval = "15s"
                static_configs = [
                  {
                    targets = ["localhost:8888"]
                  }
                ]
              }
            ]
          }
        }
      }
      processors = {
        batch = {
          timeout         = "10s"
          send_batch_size = 1024
        }
        memory_limiter = {
          check_interval   = "5s"
          limit_percentage = 80
        }
        attributes = {
          actions = [
            {
              key    = "environment"
              action = "upsert"
              value  = var.environment
            }
          ]
        }
      }
      exporters = {
        debug = {
          verbosity = "detailed"
        }
        prometheusremotewrite = var.prometheus_endpoint != "" ? {
          endpoint = var.prometheus_endpoint
        } : null
        otlp = var.jaeger_endpoint != "" ? {
          endpoint = var.jaeger_endpoint
          tls = {
            insecure = true
          }
        } : null
      }
      service = {
        pipelines = {
          traces = {
            receivers  = ["otlp"]
            processors = ["memory_limiter", "batch", "attributes"]
            exporters  = concat(["debug"], var.jaeger_endpoint != "" ? ["otlp"] : [])
          }
          metrics = {
            receivers  = ["otlp", "prometheus"]
            processors = ["memory_limiter", "batch", "attributes"]
            exporters  = concat(["debug"], var.prometheus_endpoint != "" ? ["prometheusremotewrite"] : [])
          }
          logs = {
            receivers  = ["otlp"]
            processors = ["memory_limiter", "batch", "attributes"]
            exporters  = ["debug"]
          }
        }
        telemetry = {
          metrics = {
            address = "0.0.0.0:8888"
          }
        }
      }
    }
  }])
}

output "endpoint" {
  value = "otel-collector-collector.${var.namespace}.svc.cluster.local:4317"
}

output "http_endpoint" {
  value = "otel-collector-collector.${var.namespace}.svc.cluster.local:4318"
}
