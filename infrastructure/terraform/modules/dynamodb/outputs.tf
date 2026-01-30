output "anime_table_name" {
  value = aws_dynamodb_table.anime.name
}

output "users_table_name" {
  value = aws_dynamodb_table.users.name
}

output "interactions_table_name" {
  value = aws_dynamodb_table.interactions.name
}

output "recommendation_cache_table_name" {
  value = aws_dynamodb_table.recommendation_cache.name
}

output "anime_table_arn" {
  value = aws_dynamodb_table.anime.arn
}

output "interactions_table_arn" {
  value = aws_dynamodb_table.interactions.arn
}

output "recommendation_cache_table_arn" {
  value = aws_dynamodb_table.recommendation_cache.arn
}
