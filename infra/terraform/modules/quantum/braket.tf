variable "enabled" {
  description = "Enable AWS Braket"
  type        = bool
  default     = false
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "instance_type" {
  description = "SageMaker instance type for Braket notebook"
  type        = string
  default     = "ml.t3.medium"
}

variable "s3_bucket_name" {
  description = "S3 bucket for Braket results"
  type        = string
  default     = "face-zero-trust-braket"
}

resource "aws_s3_bucket" "braket" {
  count  = var.enabled ? 1 : 0
  bucket = "${var.s3_bucket_name}-${var.environment}"

  tags = {
    Environment = var.environment
    Purpose     = "braket-results"
  }
}

resource "aws_s3_bucket_versioning" "braket" {
  count  = var.enabled ? 1 : 0
  bucket = aws_s3_bucket.braket[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_iam_role" "braket" {
  count = var.enabled ? 1 : 0
  name  = "braket-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "braket_sagemaker" {
  count      = var.enabled ? 1 : 0
  role       = aws_iam_role.braket[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
}

resource "aws_iam_role_policy_attachment" "braket_s3" {
  count      = var.enabled ? 1 : 0
  role       = aws_iam_role.braket[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy" "braket_access" {
  count = var.enabled ? 1 : 0
  name  = "braket-access"
  role  = aws_iam_role.braket[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "braket:CreateQuantumTask",
          "braket:GetQuantumTask",
          "braket:SearchDevices",
          "braket:GetDevice",
          "braket:CancelQuantumTask",
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_sagemaker_notebook_instance" "braket" {
  count                  = var.enabled ? 1 : 0
  name                   = "braket-${var.environment}"
  instance_type          = var.instance_type
  role_arn               = aws_iam_role.braket[0].arn
  default_code_repository = ""
  direct_internet_access = "Enabled"

  tags = {
    Environment = var.environment
    Purpose     = "quantum-computing"
  }
}

output "notebook_instance_arn" {
  value = var.enabled ? aws_sagemaker_notebook_instance.braket[0].arn : ""
}

output "braket_role_arn" {
  value = var.enabled ? aws_iam_role.braket[0].arn : ""
}
