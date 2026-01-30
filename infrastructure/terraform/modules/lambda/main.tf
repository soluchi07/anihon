// Lambda execution role with minimal permissions
resource "aws_iam_role" "lambda_exec_role" {
  name = "${var.project_name}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

// CloudWatch Logs policy for Lambda
resource "aws_iam_role_policy" "lambda_logs" {
  name = "${var.project_name}-lambda-logs"
  role = aws_iam_role.lambda_exec_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

// Archive the Lambda source code as a zip file
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = var.source_code_path
  output_path = "${path.module}/.terraform/lambda_${var.function_name}.zip"
}

// Generic Lambda function resource
resource "aws_lambda_function" "function" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "${var.project_name}-${var.function_name}"
  role            = aws_iam_role.lambda_exec_role.arn
  handler         = var.handler
  runtime         = var.runtime
  timeout         = var.timeout
  memory_size     = var.memory_size
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = var.environment_vars
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.function.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}
