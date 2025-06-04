# Branch Protection Configuration Guide

This document outlines the recommended branch protection rules for the Brain2Gain repository to ensure code quality and security.

## Protected Branches

### Main Branch (`main`)

Configure the following protection rules for the `main` branch:

#### Required Status Checks
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging

**Required checks:**
- `Code Quality & Security`
- `Backend Tests`
- `Frontend Tests` 
- `Build & Security Scan`
- `E2E Tests` (if applicable)

#### Pull Request Requirements
- ✅ Require pull request reviews before merging
- **Required reviewers:** 2
- ✅ Dismiss stale PR approvals when new commits are pushed
- ✅ Require review from code owners (if CODEOWNERS file exists)
- ✅ Restrict dismissals to administrators only

#### Additional Restrictions
- ✅ Restrict pushes that create public merge commits
- ✅ Require signed commits
- ✅ Require linear history
- ✅ Include administrators in these restrictions

#### Allow Force Pushes
- ❌ Do not allow force pushes

#### Allow Deletions
- ❌ Do not allow deletions

### Develop Branch (`develop`)

Configure the following protection rules for the `develop` branch:

#### Required Status Checks
- ✅ Require status checks to pass before merging
- ✅ Require branches to be up to date before merging

**Required checks:**
- `Code Quality & Security`
- `Backend Tests`
- `Frontend Tests`

#### Pull Request Requirements
- ✅ Require pull request reviews before merging
- **Required reviewers:** 1
- ✅ Dismiss stale PR approvals when new commits are pushed

#### Additional Restrictions
- ✅ Require signed commits
- ❌ Do not include administrators in restrictions (for hotfixes)

#### Allow Force Pushes
- ❌ Do not allow force pushes

#### Allow Deletions
- ❌ Do not allow deletions

## Setting Up Branch Protection

### Via GitHub Web Interface

1. Go to repository **Settings** → **Branches**
2. Click **Add rule** or edit existing rule
3. Enter branch name pattern (e.g., `main`, `develop`)
4. Configure protection settings as outlined above
5. Click **Create** or **Save changes**

### Via GitHub CLI

```bash
# Main branch protection
gh api repos/:owner/:repo/branches/main/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Code Quality & Security","Backend Tests","Frontend Tests","Build & Security Scan"]}' \
  --field enforce_admins=true \
  --field required_pull_request_reviews='{"required_approving_review_count":2,"dismiss_stale_reviews":true,"require_code_owner_reviews":true}' \
  --field restrictions=null

# Develop branch protection
gh api repos/:owner/:repo/branches/develop/protection \
  --method PUT \
  --field required_status_checks='{"strict":true,"contexts":["Code Quality & Security","Backend Tests","Frontend Tests"]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
  --field restrictions=null
```

### Via Repository Configuration as Code

Create `.github/settings.yml` for repository configuration:

```yaml
repository:
  name: brain2gain
  description: Brain2Gain E-commerce Platform for Sports Supplements
  homepage: https://brain2gain.com
  topics: ecommerce, sports-supplements, fastapi, react, typescript
  private: false
  has_issues: true
  has_projects: true
  has_wiki: false
  has_downloads: true
  default_branch: main
  allow_squash_merge: true
  allow_merge_commit: false
  allow_rebase_merge: false
  delete_branch_on_merge: true

branches:
  - name: main
    protection:
      required_status_checks:
        strict: true
        contexts:
          - "Code Quality & Security"
          - "Backend Tests"
          - "Frontend Tests"
          - "Build & Security Scan"
      enforce_admins: true
      required_pull_request_reviews:
        required_approving_review_count: 2
        dismiss_stale_reviews: true
        require_code_owner_reviews: true
        dismissal_restrictions:
          users: []
          teams: ["brain2gain-admins"]
      restrictions:
        users: []
        teams: ["brain2gain-maintainers"]
      
  - name: develop
    protection:
      required_status_checks:
        strict: true
        contexts:
          - "Code Quality & Security"
          - "Backend Tests"
          - "Frontend Tests"
      enforce_admins: false
      required_pull_request_reviews:
        required_approving_review_count: 1
        dismiss_stale_reviews: true
        require_code_owner_reviews: false
      restrictions: null
```

## CODEOWNERS File

Create `.github/CODEOWNERS` to automatically request reviews:

```
# Global owners
* @brain2gain-team

# Backend code
/backend/ @backend-team @senior-developers

# Frontend code  
/frontend/ @frontend-team @senior-developers

# Infrastructure and CI/CD
/.github/ @devops-team @senior-developers
/docker-compose*.yml @devops-team
/Dockerfile* @devops-team
/scripts/ @devops-team

# Documentation
/docs/ @technical-writers @senior-developers
README.md @technical-writers
SECURITY.md @security-team

# Security sensitive files
/.github/workflows/ @security-team @devops-team
/backend/app/core/security.py @security-team
/backend/app/core/config.py @security-team
```

## Rulesets (Advanced)

For organizations, consider using GitHub Rulesets for more advanced protection:

```yaml
name: "Main Branch Protection"
target: "branch"
enforcement: "active"
conditions:
  ref_name:
    include:
      - "refs/heads/main"
rules:
  - type: "pull_request"
    parameters:
      required_approving_review_count: 2
      dismiss_stale_reviews_on_push: true
      require_code_owner_review: true
      require_last_push_approval: true
  - type: "required_status_checks"
    parameters:
      strict_required_status_checks_policy: true
      required_status_checks:
        - "Code Quality & Security"
        - "Backend Tests"
        - "Frontend Tests"
        - "Build & Security Scan"
  - type: "non_fast_forward"
  - type: "required_signatures"
```

## Testing Branch Protection

Verify branch protection is working:

1. **Create a test PR** with failing checks
2. **Verify blocking:** PR should be blocked from merging
3. **Test review requirements:** Ensure required reviews are enforced
4. **Check status requirements:** All required checks must pass

## Monitoring and Maintenance

- **Review protection rules** monthly
- **Update required checks** when CI/CD changes
- **Monitor bypass attempts** in audit logs
- **Adjust reviewer requirements** based on team size

## Troubleshooting

### Common Issues

1. **Status check not found**: Ensure check name matches exactly in workflow
2. **Admin bypass**: Verify "Include administrators" is enabled
3. **Stale reviews**: Enable "Dismiss stale reviews" to ensure fresh approvals

### Emergency Procedures

For critical hotfixes:

1. **Create emergency branch** from main
2. **Apply minimal fix** with thorough testing
3. **Fast-track review** with senior developer
4. **Monitor deployment** closely
5. **Follow up** with proper PR to develop

## Compliance

These settings help ensure:

- **SOC 2 Type II** compliance for access controls
- **GDPR** compliance for data protection
- **SOX** compliance for financial data integrity
- **ISO 27001** compliance for information security