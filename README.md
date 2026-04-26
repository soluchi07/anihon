# AniHon: Anime Recommendation Engine

A cloud-based anime recommendation system built on AWS serverless architecture. Users authenticate, provide preferences during onboarding, and receive personalized anime recommendations powered by content-based filtering.

## Overview

AniHon is a full-stack web application that demonstrates modern cloud architecture principles by leveraging AWS serverless services. The system delivers a smooth user experience from authentication through personalized recommendations, all while maintaining scalability and cost-effectiveness.

## Features

### Core Functionality
- **User Authentication**: Secure sign-up and login via Amazon Cognito
- **Onboarding Flow**: Collect user preferences for genres, studios, and content types
- **Recommendation Engine**: Content-based filtering using cosine similarity on anime metadata
- **Anime Library**: Browse and search anime with rich metadata (genres, studios, scores, descriptions)
- **Interaction Tracking**: Like/rate anime and create custom lists
- **User Ratings**: Community-driven rating system (1-10 scale) that factors into recommendations
- **Similar Anime**: Discover related anime based on content similarity

### MVP Scope (Week 10 Deliverable)
- Authenticated user accounts with persistent data
- Complete onboarding experience
- Working recommendation engine (content-based)
- Responsive single-page React frontend
- Fully deployed serverless backend
- CloudWatch logging and monitoring

## Tech Stack

### Backend
- **Compute**: AWS Lambda (Python runtime)
- **API**: API Gateway (RESTful endpoints)
- **Database**: DynamoDB (serverless NoSQL)
- **Authentication**: Amazon Cognito
- **Storage**: S3 (dataset and assets)

### Frontend
- **Framework**: React.js
- **Hosting**: S3 + CloudFront (CDN)
- **HTTP Client**: Custom API client with polling hooks

### Infrastructure
- **IaC**: Terraform
- **Deployment**: Automated via scripts
- **Monitoring**: CloudWatch

### Data
- **Anime Metadata**: Jikan API (pre-parsed JSON)
- **Data Processing**: Python scripts for cleaning and normalization

## Project Structure

```
anihon/
├── backend/
│   └── lambdas/              # Lambda function handlers
│       ├── anime_getter/      # Anime metadata retrieval
│       ├── data_ingest/       # S3 data upload and processing
│       ├── interactions/      # Like, rate, list management
│       ├── onboarding/        # User preference collection
│       ├── recommendation/    # Recommendation algorithm
│       └── recommendation_worker/  # Batch recommendation processing
├── frontend/
│   ├── src/
│   │   ├── components/        # React components
│   │   ├── pages/            # Page views (Landing, Onboarding, Recommendations)
│   │   ├── api/              # API client
│   │   └── styles/           # Component styles
│   └── public/               # Static assets
├── infrastructure/
│   └── terraform/            # Infrastructure as Code
│       ├── modules/          # Reusable Terraform modules
│       │   ├── cognito/      # Auth configuration
│       │   ├── dynamodb/     # Database setup
│       │   ├── lambda/       # Lambda deployment
│       │   ├── s3_cloudfront/# Frontend hosting
│       │   └── budgets/      # Cost controls
│       └── envs/             # Environment-specific configs
├── data/
│   ├── anime_meta.json       # Raw anime metadata
│   ├── cleaned/              # Processed datasets
│   └── sample/               # Sample data for testing
└── scripts/
    ├── deploy_frontend.sh    # Frontend deployment
    ├── package_lambdas.ps1   # Lambda packaging
    └── remove_music_batch.py # Data cleaning script
```

## Course Deliverables

| Document | Description |
|---|---|
| [docs/architecture.puml](docs/architecture.puml) | UML component diagram — render with [PlantUML](https://plantuml.com/) |
| [docs/reflection.md](docs/reflection.md) | Project reflection (what was built, cloud concepts, challenges, lessons learned) |
| [docs/evidence.md](docs/evidence.md) | Evidence of implementation — screenshot guide, code snippets, sample output |

## Architecture

See [`docs/architecture.puml`](docs/architecture.puml) for the full UML component diagram (render with [PlantUML](https://plantuml.com/) or the [VS Code PlantUML extension](https://marketplace.visualstudio.com/items?itemName=jebbs.plantuml)).

## Architecture Highlights

### Serverless Design
- No servers to manage or scale manually
- Pay only for compute resources consumed
- Auto-scaling handled by AWS

### Recommendation Algorithm
- **Approach**: Content-based filtering with cosine similarity
- **Features**: Genre overlap, studio match, popularity range, score proximity
- **Fallback**: Non-personalized recommendations for new users or data gaps
- **Future Enhancement**: Collaborative filtering can be integrated post-MVP

### Data Pipeline
1. Raw anime data fetched from Jikan API
2. Cleaned and normalized (remove music videos, handle null scores)
3. Stored in S3 and indexed in DynamoDB
4. Used by Lambda functions for recommendations

### User Flow
```
Landing Page → Sign Up/Login → Onboarding → Recommendations → Interactions
```

## Development Timeline

The project follows a 10-week schedule with clear milestones:

| Week | Focus | Deliverables |
|------|-------|--------------|
| 1 | Planning & Setup | Architecture finalized, repo structure created |
| 2 | Data Preparation | Datasets cleaned, DynamoDB schemas designed |
| 3 | Database | Tables created, seeding scripts completed |
| 4 | Authentication | Cognito configured, user sync implemented |
| 5 | Backend APIs | Core endpoints for user, anime, and preferences |
| 6 | Onboarding | Preference collection endpoints |
| 7 | Recommendations | Algorithm implemented and tested |
| 8 | Frontend | React UI for all core flows |
| 9 | Interactions | Like, rate, and list management |
| 10 | Deployment & Testing | End-to-end testing, production deployment |

## Getting Started

### Prerequisites
- Python 3.x (for Lambda and data processing)
- Node.js & npm (for frontend)
- Terraform (for infrastructure)
- AWS CLI configured with appropriate credentials
- AWS account with relevant service access

### Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Contributor Setup

- Local setup runbook: [docs/CONTRIBUTOR_SETUP.md](docs/CONTRIBUTOR_SETUP.md)
- Production readiness checklist: [docs/PRODUCTION_READINESS_CHECKLIST.md](docs/PRODUCTION_READINESS_CHECKLIST.md)
- Environment templates:
   - Root template: [.env.example](.env.example)
   - Frontend template: [frontend/.env.example](frontend/.env.example)

### Development

1. **Data Setup**: Process anime metadata
   ```bash
   python data/prep_anime.py
   ```

2. **Backend**: Deploy Lambda functions and API Gateway via Terraform
   ```bash
   cd infrastructure/terraform
   terraform plan -var-file=envs/dev.tfvars
   terraform apply
   ```

3. **Frontend**: Build and deploy React app
   ```bash
   cd frontend
   npm install
   npm run build
   bash ../scripts/deploy_frontend.sh
   ```

## Key Design Decisions

1. **Serverless**: Chose AWS Lambda over EC2 for cost efficiency and auto-scaling
2. **NoSQL**: DynamoDB selected for flexible schema and pay-per-request pricing
3. **Content-Based Filtering**: Simple, deterministic algorithm suitable for MVP (no user-user correlation needed yet)
4. **Image URLs**: Store metadata links in DynamoDB; S3 storage deferred to post-MVP (balance speed vs. cost)
5. **Python Lambda**: Leverages data science libraries for recommendation algorithms

## Testing

- **Unit Tests**: Available for Lambda handlers and algorithms
- **Integration**: Live API integration chain test available at `backend/tests/integration/test_live_auth_flow.py`
- **Performance**: Target response time <2 seconds for recommendations

### Test Commands

```bash
# Backend tests
pytest -q backend

# Frontend unit tests
cd frontend && npm test -- --watch=false --passWithNoTests

# Frontend E2E tests (opt-in)
cd frontend && E2E_TESTS=1 E2E_BASE_URL=http://localhost:3001 npm run test:e2e

# Live integration chain (opt-in)
INTEGRATION_TESTS=1 API_BASE=<api-base-url> pytest -q backend/tests/integration/test_live_auth_flow.py
```

## Monitoring & Logging

- CloudWatch logs for all Lambda executions
- API Gateway request/response logging
- DynamoDB operation metrics
- Custom application logging in handlers

## Future Enhancements

- Collaborative filtering for improved recommendations
- User-to-user similarity recommendations
- Advanced filtering and search
- Social features (follow users, share lists)
- Custom domain name
- Image CDN optimization in S3
- Mobile app

## Constraints & Notes

- Solo development project
- MVP completed within semester (~10 weeks)
- No external recommendation APIs (custom algorithm only)
- AWS S3 website endpoint URL (no custom domain for MVP)
- Music videos excluded from dataset

## Contact & Support

For questions or issues, refer to the deployment guide in [DEPLOYMENT.md](DEPLOYMENT.md).

---

**Status**: Active maintenance and reliability hardening complete (Phases 1-2)  
**Last Updated**: April 2026
