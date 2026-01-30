# Product Requirements Document (PRD)

## Product Name: AnimeRec

**Version:** 1.0
**Author:** Soluchi Fidel-Ibeabuchi
**Date:** January 2026
**Status:** Draft

---

## 1. Overview

### 1.1 Product Description

AnimeRec is a cloud-native anime recommendation platform that helps users discover anime they are likely to enjoy based on their stated interests and interactions with the platform. The system initially uses **content-based filtering**, and progressively incorporates **collaborative filtering** as more users join and generate interaction data.

The product is deployed on **AWS**, using managed services for authentication, storage, data persistence, and automation.

---

### 1.2 Goals

* Allow users to create accounts and persist preferences
* Collect explicit user interests during onboarding
* Recommend anime using content-based filtering
* Improve recommendations using collaborative filtering as user data grows
* Persist user-anime interactions (likes, ratings, lists)
* Provide detailed anime profile pages similar to Letterboxd

---

### 1.3 Non-Goals

* No social features (comments, follows, reviews)
* No streaming or external anime APIs
* No admin dashboard in v1
* No assumption of real-time recommendation updates

---

## 2. Target Users

### 2.1 Primary Users

* Anime fans seeking recommendations
* New anime viewers unsure where to start
* Users interested in organizing anime into personal lists

---

## 3. Assumptions & Constraints

### 3.1 Explicit Constraints

* **Only anime metadata is available**, including:

  * Name
  * Alternative names
  * Popularity
  * Rank
  * Score
  * Rating (e.g., PG, PG-13)
  * Synopsis
  * Genres
  * Studio
* No external enrichment APIs
* System must be built entirely from scratch
* AWS must be used for:

  * Authentication
  * Storage
  * Compute
  * Future automation

---

## 4. High-Level Architecture (AWS)

### 4.1 AWS Services

| Category            | AWS Service                 | Purpose                      |
| ------------------- | --------------------------- | ---------------------------- |
| Authentication      | Amazon Cognito              | User signup, login, identity |
| API Layer           | AWS Lambda + API Gateway    | Backend business logic       |
| Database            | Amazon DynamoDB             | Users, anime, interactions   |
| Object Storage      | Amazon S3                   | Anime datasets, images       |
| Frontend Hosting    | S3 + CloudFront             | Static landing page          |
| Automation (Future) | EventBridge, Step Functions | Scheduled jobs, retraining   |
| Monitoring          | CloudWatch                  | Logs and metrics             |
| CI/CD (Future)      | GitHub Actions              | Deployment automation        |

---

## 5. Functional Requirements

---

## 5.1 Authentication & User Creation

### Description

Users must be able to sign up and log in.

### Requirements

* Users can:

  * Sign up with email and password
  * Log in using existing credentials
* On successful signup:

  * A new user record is created in the `Users` table
  * User ID from Cognito is used as the primary key

### Data Stored

* User ID
* Email
* Account creation timestamp

---

## 5.2 Landing Page (Frontend)

### Description

The frontend consists of a **single landing page**.

### Requirements

* Displays:

  * Product description
  * Call-to-action buttons:

    * “Sign Up”
    * “Log In”
* Redirects authenticated users to onboarding or recommendations

---

## 5.3 User Onboarding & Interest Collection

### Description

New users are guided through an onboarding flow to capture preferences.

### Questions Collected

* Preferred genres
* Preferred studios
* Preference for:

  * Newer vs older anime
  * Popular vs niche anime

### Requirements

* Users must complete onboarding before recommendations
* Preferences are stored in the user profile
* Preferences must be editable later

---

## 5.4 Initial Anime Suggestions

### Description

After onboarding, users are shown anime based on stated interests.

### Requirements

* System selects anime using **content-based filtering**
* Anime are displayed as **title cards**
* Each card includes:

  * Title
  * Cover image (if available)
  * Genres
  * Score

---

## 5.5 User Selection of Anime

### Description

Users must select anime they are interested in.

### Requirements

* Users must select **at least 5 anime**
* Selected anime are stored as:

  * “Liked anime”
* Selection is required to proceed

---

## 5.6 Recommendation Engine

### 5.6.1 Content-Based Filtering

#### Inputs

* Anime metadata
* User preferences
* Liked anime

#### Behavior

* Recommend anime similar by:

  * Genre overlap
  * Studio
  * Popularity range
  * Score proximity

---

### 5.6.2 Collaborative Filtering

#### Conditions

* Only used when:

  * Other users exist
  * Overlapping interaction data exists

#### Inputs

* User-anime ratings
* User-anime likes

#### Fallback Logic

1. Attempt collaborative filtering
2. If no results:

   * Use content-based filtering

---

## 5.7 Anime Profiles

### Description

Each anime has a dedicated profile page.

### Requirements

Each profile includes:

* Title
* Alternative names
* Synopsis
* Genres
* Studio
* Average user score
* Popularity
* Rating (PG, etc.)
* Title card / image
* Similar anime section

---

## 5.8 Liking Anime

### Description

Users can like anime.

### Requirements

* Liked anime are stored per user
* Likes are used for:

  * Recommendations
  * Collaborative filtering

---

## 5.9 User Lists / Buckets

### Description

Users can organize anime into custom lists.

### Requirements

* Users can:

  * Create multiple lists
  * Add/remove anime from lists
* Lists persist across sessions
* Lists are tied to user accounts

---

## 5.10 Rating System

### Description

Users can rate anime similar to Letterboxd.

### Requirements

* Ratings are:

  * Numeric (e.g., 0.5–5.0 or 1–5)
* Stored per user-anime pair
* Ratings are used for:

  * Collaborative filtering
  * Computing average anime score

---

## 6. Data Model (High Level)

### 6.1 Users Table

* user_id (PK)
* email
* preferences
* created_at

### 6.2 Anime Table

* anime_id (PK)
* title
* alternative_titles
* synopsis
* genres
* studio
* score
* popularity
* rating_category

### 6.3 UserAnimeInteractions

* user_id (PK)
* anime_id (SK)
* liked (boolean)
* rating
* lists[]

---

## 7. Non-Functional Requirements

### Performance

* Recommendation response < 2 seconds
* Support concurrent users without degradation

### Scalability

* Stateless backend (Lambda)
* Horizontally scalable storage (DynamoDB)

### Security

* Authentication handled via Cognito
* No unauthenticated access to user data
* HTTPS enforced

### Reliability

* Graceful fallback between recommendation strategies
* No single point of failure

---

## 8. Success Metrics

### MVP Success

* Users can sign up and log in
* Onboarding completed by >80% of users
* Recommendations generated successfully
* Likes and ratings persist across sessions

### Long-Term

* Improved recommendation accuracy
* Increased user engagement (likes, ratings, list creation)

---

## 9. Future Enhancements (Out of Scope for v1)

* Scheduled retraining using AWS Step Functions
* Social features
* Advanced recommendation explanations
* Admin analytics dashboard

---

## 10. Open Questions (Explicitly Not Assumed)

* Exact rating scale (5.0 vs 10.0)
* Whether images are locally stored or optional
* Whether recommendations refresh in real time
* Exact ML similarity metrics

---
