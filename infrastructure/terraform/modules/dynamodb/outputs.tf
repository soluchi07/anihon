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

output "lists_table_name" {
  value = aws_dynamodb_table.lists.name
}

output "anime_table_arn" {
  value = aws_dynamodb_table.anime.arn
}

output "users_table_arn" {
  value = aws_dynamodb_table.users.arn
}

output "interactions_table_arn" {
  value = aws_dynamodb_table.interactions.arn
}

output "recommendation_cache_table_arn" {
  value = aws_dynamodb_table.recommendation_cache.arn
}

output "lists_table_arn" {
  value = aws_dynamodb_table.lists.arn
}
