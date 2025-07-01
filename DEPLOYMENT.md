# Deployment Guide

This guide provides step-by-step instructions for deploying the Prelovium application.

## Prerequisites

Before deploying, ensure you have:

1. **Google Cloud SDK** installed and configured
2. **Terraform** installed (version >= 1.0)
3. **Docker** installed
4. **Git** repository access
5. **GitHub** account with repository access

## Initial Setup

### 1. Google Cloud Project Setup

```bash
# Set your project ID
export PROJECT_ID="prelovio"

# Set the project
gcloud config set project $PROJECT_ID

# Enable billing (required for Cloud Run)
# This must be done via the GCP Console

# Run the automated setup
make setup-gcp PROJECT_ID=prelovio
```

### 2. Terraform Configuration

```bash
# Navigate to terraform directory
cd terraform

# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your project details
nano terraform.tfvars
```

Example `terraform.tfvars`:
```hcl
project_id  = "prelovio"
region      = "europe-west1"
environment = "prod"
```

### 3. Deploy Infrastructure

```bash
# Initialize Terraform
make terraform-init

# Review the planned changes
make terraform-plan

# Apply the changes (creates all GCP resources)
make terraform-apply
```

This will create:
- Cloud Run service
- Artifact Registry repository
- Service accounts for GitHub Actions
- Required IAM bindings

### 4. GitHub Actions Setup

#### Get Service Account Key

```bash
# From terraform directory
terraform output -raw github_actions_service_account_key | base64 -d > sa-key.json

# Base64 encode the key for GitHub secrets
base64 -i sa-key.json | pbcopy  # macOS
base64 -i sa-key.json           # Linux
```

#### Configure GitHub Repository Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:
- `GCP_PROJECT_ID`: Your Google Cloud project ID
- `GCP_SA_KEY`: The base64 encoded service account key from above

#### Test the Pipeline

```bash
# Push to main branch to trigger deployment
git add .
git commit -m "Initial deployment setup"
git push origin main
```

## Manual Deployment

If you prefer to deploy manually instead of using GitHub Actions:

```bash
# Deploy directly to Cloud Run
make deploy PROJECT_ID=prelovio
```

## Local Development

### Run Locally

```bash
# Install dependencies
make install

# Start development server
make dev
```

### Test with Docker

```bash
# Build and run with Docker
make deploy-local
```

## Monitoring and Troubleshooting

### Check Cloud Run Service

```bash
# Get service URL
gcloud run services describe prelovium \
  --region=europe-west1 \
  --format='value(status.url)'

# View logs
gcloud logs read --filter="resource.type=cloud_run_revision" --limit=50
```

### Check GitHub Actions

1. Go to GitHub repository → Actions tab
2. Click on the latest workflow run
3. Check the logs for any errors

### Common Issues

**Issue**: `Permission denied` when pushing Docker image
**Solution**: Ensure the service account has `artifactregistry.writer` role

**Issue**: Cloud Run service not accessible
**Solution**: Check if the service allows unauthenticated access:
```bash
gcloud run services add-iam-policy-binding prelovium \
  --region=europe-west1 \
  --member=allUsers \
  --role=roles/run.invoker
```

**Issue**: Terraform state conflicts
**Solution**: Use remote state storage (see `terraform/backend.tf`)

## Updating the Application

### Through GitHub Actions (Recommended)

1. Make your changes
2. Push to a feature branch
3. Create a pull request (triggers tests)
4. Merge to main (triggers deployment)

### Manual Update

```bash
# Make your changes
# ...

# Deploy manually
make deploy PROJECT_ID=prelovio
```

## Infrastructure Updates

When modifying Terraform configuration:

```bash
# Plan changes
make terraform-plan

# Apply changes
make terraform-apply
```

## Cleanup

To destroy all resources:

```bash
# Destroy infrastructure
make terraform-destroy

# Clean local Docker resources
make clean
```

## Security Considerations

1. **Service Account Keys**: Store GitHub secrets securely
2. **Public Access**: The Cloud Run service is publicly accessible by default
3. **Container Images**: Images are stored in Artifact Registry with appropriate permissions
4. **Terraform State**: Consider using remote state storage for production

## Cost Optimization

- Cloud Run scales to zero when not in use
- Artifact Registry charges for storage only
- Consider setting up alerts for unexpected usage

## Support

For issues:
1. Check the logs in Cloud Run
2. Review GitHub Actions logs
3. Verify Terraform configuration
4. Check GCP quotas and billing