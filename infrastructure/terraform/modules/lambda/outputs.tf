output "lambda_arn" {
  value = aws_lambda_function.function.arn
}

output "lambda_name" {
  value = aws_lambda_function.function.function_name
}

output "role_arn" {
  value = aws_iam_role.lambda_exec_role.arn
}

output "role_id" {
  value = aws_iam_role.lambda_exec_role.id
}
