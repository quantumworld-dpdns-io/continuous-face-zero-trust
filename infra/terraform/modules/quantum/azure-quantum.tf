variable "enabled" {
  description = "Enable Azure Quantum"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "East US"
}

variable "resource_group_name" {
  description = "Resource group name"
  type        = string
  default     = "rg-quantum"
}

variable "storage_account_name" {
  description = "Storage account for Quantum workspace"
  type        = string
  default     = ""
}

resource "azurerm_resource_group" "quantum" {
  count    = var.enabled ? 1 : 0
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_storage_account" "quantum" {
  count                    = var.enabled ? 1 : 0
  name                     = var.storage_account_name != "" ? var.storage_account_name : "stquantum${var.environment}"
  resource_group_name      = azurerm_resource_group.quantum[0].name
  location                 = azurerm_resource_group.quantum[0].location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"

  tags = {
    Environment = var.environment
  }
}

resource "azurerm_quantum_workspace" "main" {
  count               = var.enabled ? 1 : 0
  name                = "qw-${var.environment}"
  location            = azurerm_resource_group.quantum[0].location
  resource_group_name = azurerm_resource_group.quantum[0].name
  sku_name            = "A"

  storage_account_id = azurerm_storage_account.quantum[0].id

  providers {
    azurerm = azurerm
  }

  tags = {
    Environment = var.environment
  }
}

output "workspace_id" {
  value = var.enabled ? azurerm_quantum_workspace.main[0].id : ""
}

output "endpoint_uri" {
  value = var.enabled ? azurerm_quantum_workspace.main[0].endpoint_uri : ""
}
