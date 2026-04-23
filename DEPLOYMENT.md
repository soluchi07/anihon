# AnimeRec Deployment Guide

## Production Deployment ✅

Your AnimeRec application is now deployed to production with the following architecture:

### Frontend
- **Hosting**: AWS S3 + CloudFront CDN
- **URL**: https://d9h4mfcv2arh5.cloudfront.net
- **Features**:
  - Global content delivery via CloudFront
  - Automatic caching of static assets
  - SPA routing (404 errors redirect to index.html)
  - HTTPS encryption

### Backend
- **API Gateway**: REST API at https://pchmrf7nr6.execute-api.us-east-1.amazonaws.com/dev
- **Compute**: AWS Lambda (Python 3.10)
- **Database**: DynamoDB
- **Functions**:
  - `/auth/signup` and `/auth/login` - User authentication
  - `/onboarding/{userId}` - User onboarding
  - `/recommendations/{userId}` - Get/trigger recommendations
  - `/anime/{animeId}` - Fetch anime details
  - `/anime/{animeId}/similar` - Fetch similar anime
  - `/interactions/{userId}` - Like/rate interactions
  - `/lists/{userId}` and `/lists/{userId}/{listKey}` - User list management

### Data
- **Storage**: S3 buckets for anime data
- **Database**: DynamoDB with 5 tables (anime, users, interactions, recommendation_cache, lists)
- **Dataset**: 25,344+ anime from MyAnimeList

---

## Environment Configuration

### Development
- Frontend: http://localhost:3001 (dev server)
- API: https://pchmrf7nr6.execute-api.us-east-1.amazonaws.com/dev
- CORS: Allowed for localhost:3000 and localhost:3001

### Production
- Frontend: https://d9h4mfcv2arh5.cloudfront.net
- API: https://pchmrf7nr6.execute-api.us-east-1.amazonaws.com/dev
- CORS: Locked to CloudFront domain (can be updated in Terraform)

---

## Deployment Instructions

### Prerequisites
- AWS Account with credentials configured
- Terraform installed
- Node.js 18+ and npm
- Python 3.10 (for Lambda development)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd animerec
   ```

2. **Install dependencies**
   ```bash
   # Backend (optional for local testing)
   pip install -r backend/requirements.txt
   
   # Frontend
   cd frontend
   npm install
   ```

3. **Deploy infrastructure**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform apply
   ```

### Frontend Deployment

To deploy or update the frontend:

```bash
cd frontend

# Build production bundle
npm run build

# Deploy to S3
aws s3 sync build/ s3://animerec-frontend-425720187450/ \
  --region us-east-1 \
  --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E3I11PDJJ4K43T \
  --paths "/*" \
  --region us-east-1
```

Or use the provided script:
```bash
./scripts/deploy_frontend.sh
```

### Backend Deployment

To update Lambda functions:

```bash
cd infrastructure/terraform

# Build and package Lambdas
../../scripts/package_lambdas.ps1

# Deploy
terraform apply
```

---

## Environment Variables

### Frontend (.env.production)
```
REACT_APP_API_BASE=https://pchmrf7nr6.execute-api.us-east-1.amazonaws.com/dev
```

### Terraform (terraform.tfvars)
```hcl
project_name      = "animerec"
aws_region         = "us-east-1"
environment        = "prod"
frontend_domain    = "https://d9h4mfcv2arh5.cloudfront.net"  # Optional: for CORS lockdown
```

---

## CORS Configuration

Currently CORS is set to allow:
- `http://localhost:3000` (dev)
- `http://localhost:3001` (dev)

To lock down to production domain:

```bash
cd infrastructure/terraform
terraform apply -var="frontend_domain=https://d9h4mfcv2arh5.cloudfront.net"
```

Or set a custom domain after ACM certificate setup.

---

## Monitoring & Logs

### CloudWatch Logs
```bash
# Onboarding Lambda
aws logs tail /aws/lambda/animerec-onboarding --follow

# Recommendation API
aws logs tail /aws/lambda/animerec-recommendation-api --follow

# Recommendation Worker
aws logs tail /aws/lambda/animerec-recommendation-worker --follow
```

### CloudFront Monitoring
- Distribution ID: `E3I11PDJJ4K43T`
- Check invalidation status:
  ```bash
  aws cloudfront get-invalidation \
    --distribution-id E3I11PDJJ4K43T \
    --id <invalidation-id>
  ```

---

## Cost Optimization

- **CloudFront**: Use distribution ID `E3I11PDJJ4K43T`
- **S3**: Bucket versioning enabled for rollbacks
- **Lambda**: 256MB for API, 512MB for worker
- **DynamoDB**: Pay-per-request billing

To estimate monthly costs:
```bash
# Frontend hosting: ~$1-5/month (varies by traffic)
# API requests: ~$0.35 per 1M requests
# DynamoDB: ~$1-10/month depending on usage
```

---

## Custom Domain Setup (Optional)

To use a custom domain instead of CloudFront default:

1. **Get ACM Certificate**
   ```bash
   aws acm request-certificate \
     --domain-name yourdomain.com \
     --validation-method DNS \
     --region us-east-1
   ```

2. **Update CloudFront Distribution**
   - Add certificate to distribution
   - Add domain as alternate CNAME
   - Update DNS with CNAME record

3. **Update CORS**
   ```bash
   terraform apply -var="frontend_domain=https://yourdomain.com"
   ```

---

## Troubleshooting

### Frontend not loading
- Check CloudFront distribution status
- Verify S3 bucket has objects
- Clear browser cache or wait for invalidation

### API returning 403
- Check CORS headers in API Gateway
- Verify frontend domain in cors_origin variable
- Test with curl: `curl -H "Origin: https://your-domain" <api-url>`

### Lambda timeout
- Check CloudWatch logs
- Increase timeout in Terraform
- Check DynamoDB capacity

### High costs
- Review CloudFront traffic
- Consider Reserved Capacity for DynamoDB
- Use CloudFront caching headers properly

---

## Security Best Practices

- [ ] Enable WAF on CloudFront
- [ ] Rotate AWS credentials regularly
- [ ] Use IAM roles instead of access keys
- [ ] Enable API Gateway logging
- [ ] Monitor Lambda for suspicious activity
- [ ] Keep dependencies updated
- [ ] Use VPC endpoints for private data access

---

## Next Steps

1. **Custom Domain**: Set up ACM certificate + custom domain
2. **Observability Expansion**: Add dashboards and alerting for Lambda/API errors
3. **Recommendation Quality**: Improve ranking quality and caching strategy
4. **Coverage Expansion**: Increase integration and E2E test depth
5. **Security Automation**: Add automated checklist gates to CI

---

## Support

For issues or questions:
1. Check CloudWatch logs
2. Review Terraform state: `terraform show`
3. Test API directly with curl
4. Check frontend browser console

---

**Deployment Date**: 2026-01-30  
**CloudFront Domain**: d9h4mfcv2arh5.cloudfront.net  
**API Endpoint**: https://pchmrf7nr6.execute-api.us-east-1.amazonaws.com/dev

For contributor onboarding and release gates, see:
- [docs/CONTRIBUTOR_SETUP.md](docs/CONTRIBUTOR_SETUP.md)
- [docs/PRODUCTION_READINESS_CHECKLIST.md](docs/PRODUCTION_READINESS_CHECKLIST.md)
