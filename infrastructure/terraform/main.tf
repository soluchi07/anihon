// Cognito module for authentication
module "cognito" {
  source = "./modules/cognito"

  project_name   = var.project_name
  cognito_domain = var.cognito_domain
  callback_urls  = var.callback_urls
  logout_urls    = var.logout_urls
  tags           = local.common_tags
}

// DynamoDB module
module "dynamodb" {
  source = "./modules/dynamodb"

  project_name = var.project_name
  tags         = local.common_tags
}

// Onboarding Lambda
module "onboarding_lambda" {
  source = "./modules/lambda"

  project_name      = var.project_name
  function_name     = "onboarding"
  source_code_path  = "${path.module}/../../backend/lambdas/onboarding/handler.py"
  handler           = "handler.handler"
  runtime           = "python3.10"
  timeout           = 30
  memory_size       = 256
  tags              = local.common_tags

  environment_vars = {
    USERS_TABLE = module.dynamodb.users_table_name
  }
}

// Auth Lambda
module "auth_lambda" {
  source = "./modules/lambda"

  project_name      = var.project_name
  function_name     = "auth"
  source_code_path  = "${path.module}/../../backend/lambdas/auth/handler.py"
  handler           = "handler.handler"
  runtime           = "python3.10"
  timeout           = 30
  memory_size       = 256
  tags              = local.common_tags

  environment_vars = {
    COGNITO_USER_POOL_ID = module.cognito.user_pool_id
    COGNITO_CLIENT_ID    = module.cognito.user_pool_client_id
  }
}

resource "aws_iam_role_policy" "auth_policy" {
  name = "${var.project_name}-auth-policy"
  role = module.auth_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:SignUp",
          "cognito-idp:AdminConfirmSignUp",
          "cognito-idp:AdminInitiateAuth"
        ]
        Resource = module.cognito.user_pool_arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "onboarding_policy" {
  name = "${var.project_name}-onboarding-policy"
  role = module.onboarding_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = module.dynamodb.users_table_arn
      }
    ]
  })
}

// Recommendation API Lambda
module "recommendation_api_lambda" {
  source = "./modules/lambda"

  project_name      = var.project_name
  function_name     = "recommendation-api"
  source_code_path  = "${path.module}/../../backend/lambdas/recommendation/handler.py"
  handler           = "handler.handler"
  runtime           = "python3.10"
  timeout           = 30
  memory_size       = 256
  tags              = local.common_tags

  environment_vars = {
    RECOMMENDATION_CACHE_TABLE     = module.dynamodb.recommendation_cache_table_name
    RECOMMENDATION_WORKER_FUNCTION = module.recommendation_worker_lambda.lambda_name
    TOP_N                          = "20"
  }
}

resource "aws_iam_role_policy" "recommendation_api_policy" {
  name = "${var.project_name}-recommendation-api-policy"
  role = module.recommendation_api_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem"
        ]
        Resource = module.dynamodb.recommendation_cache_table_arn
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = module.recommendation_worker_lambda.lambda_arn
      }
    ]
  })
}

// Recommendation Worker Lambda
module "recommendation_worker_lambda" {
  source = "./modules/lambda"

  project_name      = var.project_name
  function_name     = "recommendation-worker"
  source_code_path  = "${path.module}/../../backend/lambdas/recommendation_worker/handler.py"
  handler           = "handler.handler"
  runtime           = "python3.10"
  timeout           = 60
  memory_size       = 512
  tags              = local.common_tags

  environment_vars = {
    USERS_TABLE               = module.dynamodb.users_table_name
    INTERACTIONS_TABLE        = module.dynamodb.interactions_table_name
    ANIME_TABLE               = module.dynamodb.anime_table_name
    RECOMMENDATION_CACHE_TABLE = module.dynamodb.recommendation_cache_table_name
    TOP_N                     = "20"
    CACHE_TTL_SECONDS         = "86400"
  }
}

resource "aws_iam_role_policy" "recommendation_worker_policy" {
  name = "${var.project_name}-recommendation-worker-policy"
  role = module.recommendation_worker_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          module.dynamodb.users_table_arn,
          module.dynamodb.interactions_table_arn,
          module.dynamodb.anime_table_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem"
        ]
        Resource = module.dynamodb.recommendation_cache_table_arn
      }
    ]
  })
}

// Data ingest Lambda configuration
// This module provisions the data_ingest Lambda with S3 and DynamoDB permissions

module "data_ingest_lambda" {
  source = "./modules/lambda"

  project_name      = var.project_name
  function_name     = "data-ingest"
  source_code_path  = "${path.module}/../../backend/lambdas/data_ingest/handler.py"
  handler           = "handler.handler"
  runtime           = "python3.10"
  timeout           = 600
  memory_size       = 512
  tags              = local.common_tags

  environment_vars = {
    ANIME_TABLE  = module.dynamodb.anime_table_name
    DATA_BUCKET  = aws_s3_bucket.data_bucket.id
    DATA_KEY     = "cleaned/anime_meta_cleaned.jsonl"
  }
}

// S3 bucket for cleaned data
resource "aws_s3_bucket" "data_bucket" {
  bucket = "${var.project_name}-data"
  tags   = local.common_tags
}

// IAM policy for data_ingest to read from S3 and write to DynamoDB
resource "aws_iam_role_policy" "data_ingest_policy" {
  name = "${var.project_name}-data-ingest-policy"
  role = module.data_ingest_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.data_bucket.arn,
          "${aws_s3_bucket.data_bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:BatchWriteItem",
          "dynamodb:GetItem",
          "dynamodb:Query"
        ]
        Resource = module.dynamodb.anime_table_arn
      }
    ]
  })
}

// API Gateway
resource "aws_api_gateway_rest_api" "api" {
  name = "${var.project_name}-api"
}

// Cognito Authorizer for API Gateway
resource "aws_api_gateway_authorizer" "cognito" {
  name          = "${var.project_name}-cognito-auth"
  rest_api_id   = aws_api_gateway_rest_api.api.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [module.cognito.user_pool_arn]
  identity_source = "method.request.header.Authorization"
}

// /onboarding
resource "aws_api_gateway_resource" "onboarding" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "onboarding"
}

// /auth
resource "aws_api_gateway_resource" "auth" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "auth"
}

resource "aws_api_gateway_resource" "auth_signup" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "signup"
}

resource "aws_api_gateway_resource" "auth_login" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "login"
}

resource "aws_api_gateway_method" "auth_signup_post" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.auth_signup.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "auth_login_post" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.auth_login.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "auth_signup_options" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.auth_signup.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "auth_login_options" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.auth_login.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_signup_post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.auth_signup.id
  http_method             = aws_api_gateway_method.auth_signup_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.auth_invoke_arn
}

resource "aws_api_gateway_integration" "auth_login_post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.auth_login.id
  http_method             = aws_api_gateway_method.auth_login_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.auth_invoke_arn
}

resource "aws_api_gateway_integration" "auth_signup_options" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.auth_signup.id
  http_method             = aws_api_gateway_method.auth_signup_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_integration" "auth_login_options" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.auth_login.id
  http_method             = aws_api_gateway_method.auth_login_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "auth_signup_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.auth_signup.id
  http_method = aws_api_gateway_method.auth_signup_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_method_response" "auth_login_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.auth_login.id
  http_method = aws_api_gateway_method.auth_login_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "auth_signup_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.auth_signup.id
  http_method = aws_api_gateway_method.auth_signup_options.http_method
  status_code = aws_api_gateway_method_response.auth_signup_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
}

resource "aws_api_gateway_integration_response" "auth_login_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.auth_login.id
  http_method = aws_api_gateway_method.auth_login_options.http_method
  status_code = aws_api_gateway_method_response.auth_login_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
}

resource "aws_api_gateway_resource" "onboarding_user" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.onboarding.id
  path_part   = "{userId}"
}

resource "aws_api_gateway_method" "onboarding_post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.onboarding_user.id
  http_method             = "POST"
  authorization           = "COGNITO_USER_POOLS"
  authorizer_id           = aws_api_gateway_authorizer.cognito.id
  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_method" "onboarding_options" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.onboarding_user.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "onboarding_post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.onboarding_user.id
  http_method             = aws_api_gateway_method.onboarding_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.onboarding_invoke_arn
}

resource "aws_api_gateway_integration" "onboarding_options" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.onboarding_user.id
  http_method             = aws_api_gateway_method.onboarding_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "onboarding_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.onboarding_user.id
  http_method = aws_api_gateway_method.onboarding_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "onboarding_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.onboarding_user.id
  http_method = aws_api_gateway_method.onboarding_options.http_method
  status_code = aws_api_gateway_method_response.onboarding_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
}

// /recommendations
resource "aws_api_gateway_resource" "recommendations" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "recommendations"
}

resource "aws_api_gateway_resource" "recommendations_user" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.recommendations.id
  path_part   = "{userId}"
}

resource "aws_api_gateway_method" "recommendations_get" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.recommendations_user.id
  http_method             = "GET"
  authorization           = "COGNITO_USER_POOLS"
  authorizer_id           = aws_api_gateway_authorizer.cognito.id
  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_method" "recommendations_post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.recommendations_user.id
  http_method             = "POST"
  authorization           = "COGNITO_USER_POOLS"
  authorizer_id           = aws_api_gateway_authorizer.cognito.id
  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_method" "recommendations_options" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.recommendations_user.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "recommendations_get" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.recommendations_user.id
  http_method             = aws_api_gateway_method.recommendations_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.recommendations_invoke_arn
}

resource "aws_api_gateway_integration" "recommendations_post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.recommendations_user.id
  http_method             = aws_api_gateway_method.recommendations_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.recommendations_invoke_arn
}

resource "aws_api_gateway_integration" "recommendations_options" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.recommendations_user.id
  http_method             = aws_api_gateway_method.recommendations_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "recommendations_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.recommendations_user.id
  http_method = aws_api_gateway_method.recommendations_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "recommendations_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.recommendations_user.id
  http_method = aws_api_gateway_method.recommendations_options.http_method
  status_code = aws_api_gateway_method_response.recommendations_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
}

// Lambda permissions for API Gateway
resource "aws_lambda_permission" "onboarding_api" {
  statement_id  = "AllowAPIGatewayInvokeOnboarding"
  action        = "lambda:InvokeFunction"
  function_name = module.onboarding_lambda.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/POST/onboarding/*"
}

resource "aws_lambda_permission" "auth_signup_api" {
  statement_id  = "AllowAPIGatewayInvokeAuthSignup"
  action        = "lambda:InvokeFunction"
  function_name = module.auth_lambda.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/POST/auth/signup"
}

resource "aws_lambda_permission" "auth_login_api" {
  statement_id  = "AllowAPIGatewayInvokeAuthLogin"
  action        = "lambda:InvokeFunction"
  function_name = module.auth_lambda.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/POST/auth/login"
}

resource "aws_lambda_permission" "recommendations_api_get" {
  statement_id  = "AllowAPIGatewayInvokeRecommendationsGet"
  action        = "lambda:InvokeFunction"
  function_name = module.recommendation_api_lambda.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/GET/recommendations/*"
}

resource "aws_lambda_permission" "recommendations_api_post" {
  statement_id  = "AllowAPIGatewayInvokeRecommendationsPost"
  action        = "lambda:InvokeFunction"
  function_name = module.recommendation_api_lambda.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/POST/recommendations/*"
}

// API Deployment
resource "aws_api_gateway_deployment" "api_deployment" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = timestamp()
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.onboarding_post,
    aws_api_gateway_integration.onboarding_options,
    aws_api_gateway_integration.auth_signup_post,
    aws_api_gateway_integration.auth_login_post,
    aws_api_gateway_integration.auth_signup_options,
    aws_api_gateway_integration.auth_login_options,
    aws_api_gateway_integration.recommendations_get,
    aws_api_gateway_integration.recommendations_post,
    aws_api_gateway_integration.recommendations_options,
    aws_api_gateway_integration.anime_getter_get,
    aws_api_gateway_integration.anime_getter_options,
    aws_api_gateway_integration.anime_getter_id_get,
    aws_api_gateway_integration.anime_getter_id_options,
    aws_api_gateway_integration.interactions_get,
    aws_api_gateway_integration.interactions_post,
    aws_api_gateway_integration.interactions_options,
  ]
}

resource "aws_api_gateway_stage" "dev" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  deployment_id = aws_api_gateway_deployment.api_deployment.id
  stage_name    = "dev"
}


locals {
  common_tags = merge(var.tags, {
    Environment = var.environment
    Project     = var.project_name
  })

  onboarding_invoke_arn = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${module.onboarding_lambda.lambda_arn}/invocations"
  auth_invoke_arn = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${module.auth_lambda.lambda_arn}/invocations"
  recommendations_invoke_arn = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${module.recommendation_api_lambda.lambda_arn}/invocations"
  
  # CORS origin: wrap in single quotes for API Gateway mapping expression
  # Use '*' to allow all origins for development (change to specific domain for production)
  cors_origin = var.frontend_domain != "" ? "'${var.frontend_domain}'" : "'*'"

  anime_getter_invoke_arn = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${module.anime_getter_lambda.lambda_arn}/invocations"
  interactions_invoke_arn = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${module.interactions_lambda.lambda_arn}/invocations"
}

// ── Anime Getter Lambda ────────────────────────────────────────────────────

module "anime_getter_lambda" {
  source = "./modules/lambda"

  project_name     = var.project_name
  function_name    = "anime-getter"
  source_code_path = "${path.module}/../../backend/lambdas/anime_getter/handler.py"
  handler          = "handler.handler"
  runtime          = "python3.10"
  timeout          = 30
  memory_size      = 256
  tags             = local.common_tags

  environment_vars = {
    ANIME_TABLE = module.dynamodb.anime_table_name
  }
}

resource "aws_iam_role_policy" "anime_getter_policy" {
  name = "${var.project_name}-anime-getter-policy"
  role = module.anime_getter_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:BatchGetItem"
        ]
        Resource = [
          module.dynamodb.anime_table_arn,
          "${module.dynamodb.anime_table_arn}/index/*"
        ]
      }
    ]
  })
}

// /anime (parent resource — handles GET?genre=X)
resource "aws_api_gateway_resource" "anime" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "anime"
}

// /anime/{animeId}
resource "aws_api_gateway_resource" "anime_id" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.anime.id
  path_part   = "{animeId}"
}

resource "aws_api_gateway_method" "anime_getter_get" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.anime.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_method" "anime_getter_options" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.anime.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "anime_getter_id_get" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.anime_id.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_method" "anime_getter_id_options" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.anime_id.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "anime_getter_get" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.anime.id
  http_method             = aws_api_gateway_method.anime_getter_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.anime_getter_invoke_arn
}

resource "aws_api_gateway_integration" "anime_getter_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.anime.id
  http_method = aws_api_gateway_method.anime_getter_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "anime_getter_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.anime.id
  http_method = aws_api_gateway_method.anime_getter_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "anime_getter_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.anime.id
  http_method = aws_api_gateway_method.anime_getter_options.http_method
  status_code = aws_api_gateway_method_response.anime_getter_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
}

resource "aws_api_gateway_integration" "anime_getter_id_get" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.anime_id.id
  http_method             = aws_api_gateway_method.anime_getter_id_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.anime_getter_invoke_arn
}

resource "aws_api_gateway_integration" "anime_getter_id_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.anime_id.id
  http_method = aws_api_gateway_method.anime_getter_id_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "anime_getter_id_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.anime_id.id
  http_method = aws_api_gateway_method.anime_getter_id_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "anime_getter_id_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.anime_id.id
  http_method = aws_api_gateway_method.anime_getter_id_options.http_method
  status_code = aws_api_gateway_method_response.anime_getter_id_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
}

resource "aws_lambda_permission" "anime_getter_api" {
  statement_id  = "AllowAPIGatewayInvokeAnimeGetter"
  action        = "lambda:InvokeFunction"
  function_name = module.anime_getter_lambda.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/GET/anime*"
}

// ── Interactions Lambda ────────────────────────────────────────────────────

module "interactions_lambda" {
  source = "./modules/lambda"

  project_name     = var.project_name
  function_name    = "interactions"
  source_code_path = "${path.module}/../../backend/lambdas/interactions/handler.py"
  handler          = "handler.handler"
  runtime          = "python3.10"
  timeout          = 30
  memory_size      = 256
  tags             = local.common_tags

  environment_vars = {
    INTERACTIONS_TABLE = module.dynamodb.interactions_table_name
  }
}

resource "aws_iam_role_policy" "interactions_policy" {
  name = "${var.project_name}-interactions-policy"
  role = module.interactions_lambda.role_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:Query"
        ]
        Resource = module.dynamodb.interactions_table_arn
      }
    ]
  })
}

// /interactions
resource "aws_api_gateway_resource" "interactions" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "interactions"
}

// /interactions/{userId}
resource "aws_api_gateway_resource" "interactions_user" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_resource.interactions.id
  path_part   = "{userId}"
}

resource "aws_api_gateway_method" "interactions_get" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.interactions_user.id
  http_method   = "GET"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_method" "interactions_post" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.interactions_user.id
  http_method   = "POST"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id
  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_method" "interactions_options" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.interactions_user.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "interactions_get" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.interactions_user.id
  http_method             = aws_api_gateway_method.interactions_get.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.interactions_invoke_arn
}

resource "aws_api_gateway_integration" "interactions_post" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.interactions_user.id
  http_method             = aws_api_gateway_method.interactions_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = local.interactions_invoke_arn
}

resource "aws_api_gateway_integration" "interactions_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.interactions_user.id
  http_method = aws_api_gateway_method.interactions_options.http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "interactions_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.interactions_user.id
  http_method = aws_api_gateway_method.interactions_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "interactions_options" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.interactions_user.id
  http_method = aws_api_gateway_method.interactions_options.http_method
  status_code = aws_api_gateway_method_response.interactions_options.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,Authorization'"
    "method.response.header.Access-Control-Allow-Methods" = "'OPTIONS,GET,POST'"
    "method.response.header.Access-Control-Allow-Origin"  = local.cors_origin
  }
}

resource "aws_lambda_permission" "interactions_api_get" {
  statement_id  = "AllowAPIGatewayInvokeInteractionsGet"
  action        = "lambda:InvokeFunction"
  function_name = module.interactions_lambda.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/GET/interactions/*"
}

resource "aws_lambda_permission" "interactions_api_post" {
  statement_id  = "AllowAPIGatewayInvokeInteractionsPost"
  action        = "lambda:InvokeFunction"
  function_name = module.interactions_lambda.lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/POST/interactions/*"
}
