output "api_invoke_url" {
  value = "${aws_api_gateway_rest_api.api.execution_arn}/dev"
}

output "api_base_url" {
  value = "https://${aws_api_gateway_rest_api.api.id}.execute-api.${var.aws_region}.amazonaws.com/dev"
}