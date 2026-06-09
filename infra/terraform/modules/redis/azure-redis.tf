variable "cluster_id" {
  description = "Azure Cache for Redis name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "sku_name" {
  description = "Redis SKU name"
  type        = string
  default     = "Premium"
}

variable "family" {
  description = "Redis SKU family"
  type        = string
  default     = "P"
}

variable "capacity" {
  description = "Redis capacity"
  type        = number
  default     = 3
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "rg-redis"
}

variable "subnet_id" {
  description = "Subnet ID for VNet injection"
  type        = string
  default     = ""
}

resource "azurerm_redis_cache" "main" {
  name                = var.cluster_id
  resource_group_name = var.resource_group_name
  location            = var.location
  capacity            = var.capacity
  family              = var.family
  sku_name            = var.sku_name
  minimum_tls_version = "1.2"
  enable_non_ssl_port = false

  redis_version = "7"

  dynamic "redis_configuration" {
    for_each = var.sku_name == "Premium" ? [1] : []
    content {
      maxmemory_policy = "allkeys-lru"
    }
  }

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_redis_cache" "replica" {
  count               = var.sku_name == "Premium" ? 1 : 0
  name                = "${var.cluster_id}-replica"
  resource_group_name = var.resource_group_name
  location            = var.location
  capacity            = var.capacity
  family              = var.family
  sku_name            = var.sku_name
  minimum_tls_version = "1.2"
  enable_non_ssl_port = false
  replicas_per_master = 1

  redis_version = "7"

  tags = {
    Environment = var.environment
  }
}

output "hostname" {
  value = azurerm_redis_cache.main.hostname
}

output "ssl_port" {
  value = azurerm_redis_cache.main.ssl_port
}
