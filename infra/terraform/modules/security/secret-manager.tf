variable "environment" {
  description = "Environment name"
  type        = string
}

variable "secret_names" {
  description = "List of secret names to create"
  type        = list(string)
  default = [
    "database-url",
    "redis-url",
    "qdrant-api-key",
    "jwt-signing-key",
    "smtp-credentials",
    "cloudflare-api-token",
  ]
}

variable "recovery_window_in_days" {
  description = "Recovery window in days"
  type        = number
  default     = 7
}

variable "enable_rotation" {
  description = "Enable automatic rotation"
  type        = bool
  default     = true
}

resource "aws_secretsmanager_secret" "main" {
  for_each = toset(var.secret_names)

  name                    = "face-zero-trust/${var.environment}/${each.value}"
  description             = "Secret for ${each.value} in ${var.environment}"
  recovery_window_in_days = var.recovery_window_in_days

  tags = {
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

resource "random_password" "jwt_key" {
  length  = 64
  special = false
}

resource "aws_secretsmanager_secret_version" "jwt_key" {
  secret_id = aws_secretsmanager_secret.main["jwt-signing-key"].id
  secret_string = jsonencode({
    key     = random_password.jwt_key.result
    algo    = "HS512"
    created = timestamp()
  })
}

data "aws_iam_policy_document" "secrets_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "rotation" {
  count              = var.enable_rotation ? 1 : 0
  name               = "secret-rotation-${var.environment}"
  assume_role_policy = data.aws_iam_policy_document.secrets_assume_role.json
}

resource "aws_iam_role_policy_attachment" "rotation_lambda" {
  count      = var.enable_rotation ? 1 : 0
  role       = aws_iam_role.rotation[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_secretsmanager_secret_rotation" "main" {
  for_each = var.enable_rotation ? toset(var.secret_names) : toset([])

  secret_id           = aws_secretsmanager_secret.main[each.value].id
  rotation_lambda_arn = aws_lambda_function.rotation[0].arn

  rotation_rules {
    automatically_after_days = 30
  }
}

data "archive_file" "rotation_lambda" {
  type        = "zip"
  output_path = "${path.module}/rotation_lambda.zip"

  source {
    content  = <<-EOF
      import json
      import boto3
      import secrets
      import string

      def lambda_handler(event, context):
          client = boto3.client('secretsmanager')
          secret_id = event['SecretId']
          token = event['ClientRequestToken']
          step = event['Step']

          if step == "createSecret":
              password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
              client.put_secret_value(
                  SecretId=secret_id,
                  ClientRequestToken=token,
                  SecretString=json.dumps({"key": password}),
                  VersionStages=['AWSPENDING']
              )
          elif step == "setSecret":
              pass
          elif step == "testSecret":
              secret = client.get_secret_value(
                  SecretId=secret_id,
                  VersionStage='AWSPENDING'
              )
              assert 'key' in json.loads(secret['SecretString'])
          elif step == "finishSecret":
              metadata = client.describe_secret(SecretId=secret_id)
              for version, stages in metadata['VersionIdsToStages'].items():
                  if 'AWSCURRENT' in stages:
                      if version != token:
                          client.update_secret_version_stage(
                              SecretId=secret_id,
                              VersionStage='AWSCURRENT',
                              MoveToVersionId=token,
                              RemoveFromVersionId=version
                          )
                      break
      EOF
    filename = "index.py"
  }
}

resource "aws_lambda_function" "rotation" {
  count            = var.enable_rotation ? 1 : 0
  filename         = data.archive_file.rotation_lambda.output_path
  function_name    = "secret-rotation-${var.environment}"
  role             = aws_iam_role.rotation[0].arn
  handler          = "index.lambda_handler"
  source_code_hash = data.archive_file.rotation_lambda.output_base64sha256
  runtime          = "python3.12"
  timeout          = 30

  environment {
    variables = {
      ENVIRONMENT = var.environment
    }
  }
}

output "secret_arns" {
  value = { for k, v in aws_secretsmanager_secret.main : k => v.arn }
}

output "secret_arn" {
  value = aws_secretsmanager_secret.main["database-url"].arn
}
