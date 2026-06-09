variable "cluster_id" {
  description = "ElastiCache cluster ID"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.r6g.large"
}

variable "num_cache_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 3
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
  default     = ""
}

variable "subnet_ids" {
  description = "Subnet IDs"
  type        = list(string)
  default     = []
}

resource "aws_security_group" "redis" {
  name_prefix = "redis-${var.cluster_id}-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  tags = {
    Name        = "redis-${var.cluster_id}"
    Environment = var.environment
  }
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "${var.cluster_id}-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = var.cluster_id
  description          = "Redis cluster for ${var.environment}"

  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_nodes
  port                 = 6379

  engine               = "redis"
  engine_version       = "7.1"
  parameter_group_name = "default.redis7"

  automatic_failover_enabled = true
  multi_az_enabled           = true
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  snapshot_retention_limit = 7
  snapshot_window          = "03:00-04:00"
  maintenance_window       = "sun:04:00-sun:05:00"

  tags = {
    Environment = var.environment
  }
}

output "endpoint" {
  value = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "reader_endpoint" {
  value = aws_elasticache_replication_group.main.reader_endpoint_address
}
