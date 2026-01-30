#!/bin/bash

# AnimeRec Frontend Deployment Script
# Deploys the React frontend to S3 with CloudFront

set -e

PROJECT_NAME="animerec"
AWS_REGION="us-east-1"

echo "🚀 AnimeRec Frontend Deployment"
echo "================================"

# Step 1: Deploy infrastructure
echo ""
echo "📦 Step 1: Deploying S3 and CloudFront infrastructure..."
cd infrastructure/terraform

# First apply with frontend_domain empty (CloudFront will be created)
terraform apply -auto-approve \
  -var="project_name=$PROJECT_NAME" \
  -var="aws_region=$AWS_REGION" \
  -var="environment=prod" \
  -var="frontend_domain="

# Get the CloudFront domain
CLOUDFRONT_DOMAIN=$(terraform output -raw cloudfront_domain_name)
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name)

echo "✅ CloudFront domain: $CLOUDFRONT_DOMAIN"
echo "✅ S3 bucket: $FRONTEND_BUCKET"

# Step 2: Build frontend
echo ""
echo "🔨 Step 2: Building React frontend..."
cd ../../frontend
npm run build

# Step 3: Sync to S3
echo ""
echo "📤 Step 3: Uploading to S3..."
aws s3 sync build/ s3://$FRONTEND_BUCKET/ \
  --region $AWS_REGION \
  --delete \
  --cache-control "public, max-age=3600"

# Cache index.html without long-term caching
aws s3 cp build/index.html s3://$FRONTEND_BUCKET/index.html \
  --region $AWS_REGION \
  --cache-control "no-cache, no-store, must-revalidate"

# Step 4: Invalidate CloudFront cache
echo ""
echo "🔄 Step 4: Invalidating CloudFront cache..."
DISTRIBUTION_ID=$(cd ../infrastructure/terraform && terraform output -raw cloudfront_distribution_id)

aws cloudfront create-invalidation \
  --distribution-id $DISTRIBUTION_ID \
  --paths "/*"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your app is live at: https://$CLOUDFRONT_DOMAIN"
echo ""
echo "📝 Next steps:"
echo "  1. Update your API CORS to use the CloudFront domain:"
echo "     terraform apply -var=\"frontend_domain=https://$CLOUDFRONT_DOMAIN\""
echo "  2. Add a custom domain (optional):"
echo "     https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https-alternate-domain-names.html"
