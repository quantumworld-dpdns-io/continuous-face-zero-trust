variable "cluster_name" {
  description = "AKS cluster name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "resource_group_name" {
  description = "Azure resource group name"
  type        = string
  default     = "rg-aks"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

resource "azurerm_kubernetes_cluster" "main" {
  name                = var.cluster_name
  location            = var.location
  resource_group_name = var.resource_group_name
  dns_prefix          = var.cluster_name
  kubernetes_version  = "1.29"

  default_node_pool {
    name                = "default"
    node_count          = 3
    vm_size             = "Standard_D4s_v3"
    os_disk_size_gb     = 128
    os_disk_type        = "Managed"
    enable_auto_scaling = true
    min_count           = 2
    max_count           = 10

    node_labels = {
      environment = var.environment
    }
  }

  identity {
    type = "SystemAssigned"
  }

  network_profile {
    network_plugin    = "azure"
    load_balancer_sku = "standard"
    network_policy    = "calico"
  }

  oms_agent {
    log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
  }
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${var.cluster_name}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

output "cluster_endpoint" {
  value = azurerm_kubernetes_cluster.main.kube_config[0].host
}

output "cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}
