variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN to associate with WAF"
  type        = string
  default     = ""
}

variable "rate_limit" {
  description = "Rate limit for requests per 5 minutes"
  type        = number
  default     = 1000
}

resource "aws_wafv2_web_acl" "main" {
  name        = "waf-${var.environment}"
  description = "WAF rules for Face Zero Trust ${var.environment}"
  scope       = "CLOUDFRONT"

  default_action {
    allow {}
  }

  rule {
    name     = "rate-limit"
    priority = 1

    override_action {
      none {}
    }

    statement {
      rate_based_statement {
        limit              = var.rate_limit
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit-${var.environment}"
    }
  }

  rule {
    name     = "aws-managed-common"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSet-${var.environment}"
    }
  }

  rule {
    name     = "aws-managed-sqli"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "SQLiRuleSet-${var.environment}"
    }
  }

  rule {
    name     = "aws-managed-bad-inputs"
    priority = 4

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "BadInputs-${var.environment}"
    }
  }

  rule {
    name     = "aws-managed-bot-control"
    priority = 5

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesBotControlRuleSet"
        vendor_name = "AWS"

        managed_rule_group_configs {
          aws_managed_rules_bot_control_rule_set {
            inspection_level = "COMMON"
          }
        }
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "BotControl-${var.environment}"
    }
  }

  rule {
    name     = "block-bad-user-agents"
    priority = 6

    override_action {
      none {}
    }

    statement {
      byte_match_statement {
        field_to_match {
          single_header {
            name = "user-agent"
          }
        }
        search_string         = "sqlmap"
        positional_constraint = "CONTAINS"
        text_transformation {
          priority = 0
          type     = "LOWERCASE"
        }
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "BlockBadUA-${var.environment}"
    }
  }

  rule {
    name     = "geo-restrict"
    priority = 7

    override_action {
      none {}
    }

    statement {
      not_statement {
        statement {
          geo_match_statement {
            country_codes = ["US", "CA", "GB", "DE", "FR", "JP", "AU"]
          }
        }
      }
    }

    visibility_config {
      sampled_requests_enabled   = true
      cloudwatch_metrics_enabled = true
      metric_name                = "GeoRestrict-${var.environment}"
    }
  }

  visibility_config {
    sampled_requests_enabled   = true
    cloudwatch_metrics_enabled = true
    metric_name                = "WAF-${var.environment}"
  }

  tags = {
    Environment = var.environment
  }
}

resource "aws_wafv2_web_acl_association" "main" {
  count        = var.cloudfront_distribution_arn != "" ? 1 : 0
  resource_arn = var.cloudfront_distribution_arn
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  log_destination_configs = [aws_cloudwatch_log_group.waf.arn]
  resource_arn           = aws_wafv2_web_acl.main.arn

  logging_filter {
    default_behavior = "KEEP"

    filter {
      behavior    = "KEEP"

      condition {
        action_condition {
          action = "BLOCK"
        }
      }

      requirement = "MEETS_ANY"
    }
  }
}

resource "aws_cloudwatch_log_group" "waf" {
  name              = "aws-waf-logs-${var.environment}"
  retention_in_days = 30
}

output "web_acl_arn" {
  value = aws_wafv2_web_acl.main.arn
}

output "web_acl_id" {
  value = aws_wafv2_web_acl.main.id
}
