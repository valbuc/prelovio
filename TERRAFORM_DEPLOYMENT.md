# Terraform Deployment Guide for Prelovium

This guide covers the automated infrastructure deployment for Prelovium using Terraform.

## What Gets Deployed

The Terraform configuration automatically creates:

- ✅ **Google Cloud Storage Bucket** - For storing original and processed images
- ✅ **Service Account** - With necessary permissions for GCS and Vertex AI
- ✅ **Secret Manager** - For securely storing service account keys
- ✅ **Cloud Run Service** - Configured with environment variables and secrets
- ✅ **IAM Bindings** - Proper security permissions
- ✅ **API Enablement** - All required Google Cloud APIs

## Quick Start

### 1. Prerequisites
- Google Cloud Project with billing enabled
- Terraform installed
- Google Cloud CLI (`gcloud`) installed

### 2. Setup Authentication
```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

### 3. Configure Variables
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
```hcl
project_id  = "your-actual-project-id"
region      = "europe-west1"
environment = "prod"
database_url = "sqlite:///prelovium.db"
```

### 4. Deploy Infrastructure
```bash
terraform init
terraform plan
terraform apply
```

### 5. Get Important Outputs
```bash
# Application URL
terraform output service_url

# GCS Bucket Name
terraform output gcs_bucket_name

# Service Account Email
terraform output prelovium_app_service_account_email
```

## Key Features

### 🔐 Security
- Service account with minimal required permissions
- Service account keys stored securely in Secret Manager
- Proper IAM bindings for Cloud Run

### 📦 Storage
- GCS bucket with public read access for serving images
- CORS configuration for web uploads
- Organized folder structure (`originals/` and `processed/`)

### ⚙️ Configuration
- Environment variables automatically configured
- Service account credentials mounted as secrets
- Database URL configurable for SQLite or PostgreSQL

## Local Development

After Terraform deployment, set up local development:

```bash
# Get service account key for local development
terraform output -raw prelovium_app_service_account_key | base64 -d > ../prelovium-key.json

# Create .env file
cd ..
cp .env.example .env

# Auto-populate from Terraform outputs
cd terraform
echo "GOOGLE_CLOUD_PROJECT=$(terraform output -raw project_id)" >> ../.env
echo "GCS_BUCKET_NAME=$(terraform output -raw gcs_bucket_name)" >> ../.env
echo "GOOGLE_APPLICATION_CREDENTIALS=prelovium-key.json" >> ../.env
echo "DATABASE_URL=sqlite:///prelovium.db" >> ../.env
```

## Production Considerations

### Database
For production, consider using Cloud SQL PostgreSQL:
```hcl
# In terraform.tfvars
database_url = "postgresql://user:password@cloud-sql-proxy-host:5432/prelovium"
```

### Scaling
- Cloud Run automatically scales based on traffic
- Current limits: 0-10 instances, 2 CPU, 4GB memory
- Adjust in `terraform/main.tf` if needed

### Security
- Service account keys are stored in Secret Manager
- Bucket access is public for image serving only
- IAM follows principle of least privilege

## Cleanup

To remove all resources:
```bash
cd terraform
terraform destroy
```

**Warning**: This will delete all stored images and data!

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure you have Owner or Editor role on the project
2. **API Not Enabled**: Terraform should enable APIs automatically
3. **Bucket Name Conflict**: Bucket names must be globally unique

### Useful Commands

```bash
# Check terraform state
terraform state list

# See all outputs
terraform output

# Refresh state
terraform refresh

# Validate configuration
terraform validate
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Cloud Run     │    │   GCS Bucket    │    │  Secret Manager │
│   (App Server)  │◄──►│  (Image Store)  │    │  (SA Keys)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Service       │    │   Public Web    │    │   Vertex AI     │
│   Account       │    │   Access        │    │   (Metadata)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

This setup provides a production-ready, scalable, and secure infrastructure for the Prelovium application!