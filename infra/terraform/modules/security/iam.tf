variable "cluster_name" {
  description = "Cluster name"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "oidc_provider_url" {
  description = "OIDC provider URL for IRSA"
  type        = string
  default     = ""
}

variable "oidc_provider_arn" {
  description = "OIDC provider ARN for IRSA"
  type        = string
  default     = ""
}

data "aws_caller_identity" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
}

data "aws_iam_policy_document" "api_server_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }
    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "${replace(var.oidc_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.cluster_name}:api-server"]
    }

    condition {
      test     = "StringEquals"
      variable = "${replace(var.oidc_provider_url, "https://", "")}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

data "aws_iam_policy_document" "worker_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Federated"
      identifiers = [var.oidc_provider_arn]
    }
    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "${replace(var.oidc_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.cluster_name}:worker"]
    }
  }
}

resource "aws_iam_role" "api_server" {
  name               = "${var.cluster_name}-api-server"
  assume_role_policy = data.aws_iam_policy_document.api_server_assume_role.json
}

resource "aws_iam_role" "worker" {
  name               = "${var.cluster_name}-worker"
  assume_role_policy = data.aws_iam_policy_document.worker_assume_role.json
}

resource "aws_iam_policy" "api_server_s3" {
  name = "${var.cluster_name}-api-server-s3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
        ]
        Resource = [
          "arn:aws:s3:::${var.cluster_name}-*",
          "arn:aws:s3:::${var.cluster_name}-*/*",
        ]
      }
    ]
  })
}

resource "aws_iam_policy" "api_server_secrets" {
  name = "${var.cluster_name}-api-server-secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret",
        ]
        Resource = "arn:aws:secretsmanager:*:${local.account_id}:secret:face-zero-trust/${var.environment}/*"
      }
    ]
  })
}

resource "aws_iam_policy" "api_server_dynamodb" {
  name = "${var.cluster_name}-api-server-dynamodb"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
        ]
        Resource = "arn:aws:dynamodb:*:${local.account_id}:table/${var.cluster_name}-*"
      }
    ]
  })
}

resource "aws_iam_policy" "worker_sqs" {
  name = "${var.cluster_name}-worker-sqs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility",
        ]
        Resource = "arn:aws:sqs:*:${local.account_id}:${var.cluster_name}-*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "api_server_s3" {
  role       = aws_iam_role.api_server.name
  policy_arn = aws_iam_policy.api_server_s3.arn
}

resource "aws_iam_role_policy_attachment" "api_server_secrets" {
  role       = aws_iam_role.api_server.name
  policy_arn = aws_iam_policy.api_server_secrets.arn
}

resource "aws_iam_role_policy_attachment" "api_server_dynamodb" {
  role       = aws_iam_role.api_server.name
  policy_arn = aws_iam_policy.api_server_dynamodb.arn
}

resource "aws_iam_role_policy_attachment" "worker_sqs" {
  role       = aws_iam_role.worker.name
  policy_arn = aws_iam_policy.worker_sqs.arn
}

output "role_arns" {
  value = {
    api_server = aws_iam_role.api_server.arn
    worker     = aws_iam_role.worker.arn
  }
}

output "api_server_role_arn" {
  value = aws_iam_role.api_server.arn
}

output "worker_role_arn" {
  value = aws_iam_role.worker.arn
}
