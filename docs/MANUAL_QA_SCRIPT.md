# Manual QA Script

Use this script before release to validate critical user journeys.

## Preconditions

- Frontend app is reachable (local or deployed)
- API and auth backends are reachable
- Test user mailbox is accessible for signup verification if required

## Test Session Metadata

- Environment: ______________________
- Frontend URL: ______________________
- API base URL: ______________________
- Tester: ____________________________
- Date: ______________________________

## 1. Signup and Login

1. Open landing page.
2. Create a new account with unique email/password.
3. Confirm signup response and redirect behavior.
4. Log out.
5. Log in with same credentials.

Expected:
- Signup succeeds and returns authenticated session.
- Login succeeds and protected pages are accessible.

Result: PASS / FAIL
Notes: _________________________________________________

## 2. Onboarding Submission

1. Navigate to onboarding flow as authenticated user.
2. Select at least one genre and one studio preference.
3. Submit onboarding.

Expected:
- Onboarding request succeeds.
- Success state is shown and next route is accessible.

Result: PASS / FAIL
Notes: _________________________________________________

## 3. Recommendations Trigger and Fetch

1. Trigger recommendation generation.
2. Poll/fetch recommendations.
3. Confirm at least one recommendation is returned.

Expected:
- Trigger endpoint responds accepted/ok.
- Recommendations endpoint returns structured recommendation list.

Result: PASS / FAIL
Notes: _________________________________________________

## 4. Anime Profile and Similar Section

1. Open a recommendation card.
2. Verify anime profile page loads metadata.
3. Verify similar anime section loads results.

Expected:
- Anime profile request succeeds.
- Similar anime request succeeds and renders items.

Result: PASS / FAIL
Notes: _________________________________________________

## 5. Lists Add and Remove

1. Add an anime to a list (watching/completed/plan_to_watch/on_hold).
2. Verify list item appears in My Lists.
3. Remove the same item.
4. Verify list item no longer appears.

Expected:
- Add request succeeds with list key item.
- Remove request succeeds and UI reflects removal.

Result: PASS / FAIL
Notes: _________________________________________________

## 6. Rating Submission and Persistence

1. Submit a rating for an anime.
2. Refresh or revisit the profile/listing view.
3. Confirm rating value remains persisted.

Expected:
- Rating write succeeds.
- Persisted value is returned by subsequent reads.

Result: PASS / FAIL
Notes: _________________________________________________

## Final Sign-off

- Overall result: PASS / FAIL
- Blocking issues: ______________________________________
- Follow-up tickets created: _____________________________
