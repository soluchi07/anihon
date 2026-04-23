# Project Reflection: AnimeRec

## What I Built

For this project, I built AnimeRec — a fully serverless anime recommendation web application deployed on AWS. The system allows users to create an account, go through an onboarding flow where they select their preferred genres and studios, and then receive personalized anime recommendations powered by a custom content-based filtering algorithm.

The application consists of three main layers. The backend is made up of eight AWS Lambda functions, each responsible for a distinct concern: authentication, onboarding, recommendation retrieval, asynchronous recommendation computation, anime metadata lookup, user interactions (likes and ratings), list management, and data ingestion. These are exposed through a single API Gateway REST API that validates JWT tokens on every request. The frontend is a React single-page application hosted on S3 and served globally through CloudFront. All infrastructure — Lambda functions, DynamoDB tables, Cognito user pools, S3 buckets, and CloudFront distributions — is defined and managed with Terraform.

The recommendation engine is the technical centerpiece of the project. It builds a feature vector for each anime from its genres, studios, release year, score, and popularity, then computes cosine similarity between a user's preference vector and each anime in the catalog. Users who opt in to popularity blending receive a final score composed of 70% content similarity and 30% normalized popularity, which helps surface well-regarded anime alongside niche ones that closely match their tastes. Results are cached in DynamoDB with a TTL, and the frontend polls for completion since the worker runs asynchronously.

## Key Cloud Concepts Demonstrated

**Serverless compute.** By using AWS Lambda instead of provisioned EC2 instances, the application scales to zero when idle and only incurs cost during actual request processing. Each Lambda function is independently deployable and scoped to a single responsibility, which mirrors microservices architecture without the operational overhead of managing containers or servers.

**Managed authentication.** Amazon Cognito handles user registration, credential validation, and JWT issuance. This offloads the most security-sensitive part of any web application — credential storage and token signing — to a managed service, rather than implementing it from scratch.

**Event-driven and asynchronous processing.** The recommendation pipeline separates the API response from the heavy computation. The `recommendation-api` Lambda responds immediately with a cache-miss status and asynchronously invokes the `recommendation_worker`. The frontend polls until results are ready. This pattern prevents Lambda timeouts and keeps the API responsive even when computation takes several seconds.

**NoSQL data modeling.** DynamoDB stores all application data across five tables. Each table's partition key and sort key design was chosen to support the application's specific access patterns — for example, the Interactions table uses `user_id` as the partition key and `anime_id#interaction_type` as the sort key, which makes querying all of a user's likes or ratings a single query rather than a scan.

**Infrastructure as Code.** Terraform manages every AWS resource in the project. This means the entire environment can be torn down and rebuilt deterministically, environment-specific configuration (dev vs. prod) is version-controlled, and infrastructure changes go through the same review process as application code.

**CDN and static hosting.** The React frontend is compiled to static files, stored in S3, and distributed through CloudFront. This eliminates the need for a web server entirely and serves the frontend from edge locations closest to the user.

## Challenges

The most significant challenge was designing the asynchronous recommendation pipeline. Initially I assumed a single synchronous Lambda call would be sufficient, but recommendation computation over a large anime catalog easily exceeded the API Gateway's 29-second integration timeout. Splitting the flow into a trigger Lambda and a worker Lambda, then implementing polling on the frontend, required rethinking the data contract and introducing a cache table specifically to communicate status between the two functions.

DynamoDB schema design was harder than expected coming from a relational background. DynamoDB requires you to know your access patterns up front and model your tables around them, rather than querying flexibly after the fact. Getting the sort key design right for the Interactions and Lists tables — so that a single query could retrieve all interactions of a given type for a user — took several iterations.

Terraform state management introduced friction early on. When resources were manually modified in the AWS Console during debugging (instead of through Terraform), the state file drifted out of sync. I learned to always make infrastructure changes through code, and to use `terraform plan` as a sanity check before applying.

Cold starts were a noticeable latency problem during development, especially for Python Lambdas with larger dependencies. Minimizing package size through careful dependency selection and separating the heavy recommendation worker from the latency-sensitive API Lambda reduced cold-start impact.

## What I Learned

This project gave me hands-on experience with how production serverless systems are actually structured. I learned that the value of Lambda is not just eliminating servers — it is the discipline of decomposing an application into small, single-purpose functions that can be deployed, scaled, and reasoned about independently.

I developed a much deeper understanding of IAM. Every Lambda function needs a role with exactly the permissions it requires, nothing more. Debugging IAM permission errors — especially understanding the difference between resource-based policies and identity-based policies for services like Cognito and DynamoDB — forced me to read AWS documentation carefully rather than defaulting to overly permissive policies.

Working with Terraform taught me what Infrastructure as Code really means in practice: not just writing resource definitions, but managing state, handling dependencies between resources, and structuring modules so that the same code can target different environments. The discipline of "if it's not in Terraform, it doesn't exist" made the project dramatically easier to reason about and reproduce.

Finally, implementing the recommendation algorithm from scratch — rather than using a pre-built ML service — gave me insight into the tradeoffs of content-based filtering. It is transparent, deterministic, and works without any user interaction history, which made it ideal for an MVP. Its limitation is that it cannot discover surprising recommendations outside a user's stated preferences, which would require collaborative filtering to address.
