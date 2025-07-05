# Database and Google Cloud Storage Setup Guide

This guide will help you set up the database and Google Cloud Storage integration for Prelovium.

## Prerequisites

1. **Google Cloud Project**: You need a Google Cloud Project with billing enabled
2. **Google Cloud Storage**: A bucket for storing images
3. **Google Cloud Vertex AI**: Enabled for metadata generation
4. **Service Account**: A service account with appropriate permissions

## Google Cloud Setup

### 1. Create a Google Cloud Storage Bucket

```bash
# Create a new bucket (replace with your preferred name)
gsutil mb gs://prelovium-images-your-unique-name

# Make the bucket publicly readable for image serving
gsutil iam ch allUsers:objectViewer gs://prelovium-images-your-unique-name
```

### 2. Create a Service Account

```bash
# Create a service account
gcloud iam service-accounts create prelovium-service \
    --display-name="Prelovium Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:prelovium-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="serviceAccount:prelovium-service@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Create and download the service account key
gcloud iam service-accounts keys create prelovium-key.json \
    --iam-account=prelovium-service@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 3. Enable Required APIs

```bash
# Enable required Google Cloud APIs
gcloud services enable storage.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

## Environment Configuration

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env
   ```

2. **Update the environment variables**:
   ```env
   GOOGLE_CLOUD_PROJECT=your-actual-project-id
   GOOGLE_APPLICATION_CREDENTIALS=path/to/prelovium-key.json
   GCS_BUCKET_NAME=prelovium-images-your-unique-name
   DATABASE_URL=sqlite:///prelovium.db
   ```

## Database Setup

The application uses SQLAlchemy and will automatically create the necessary tables when you first run it.

### For Development (SQLite)
- No additional setup required
- Database file will be created automatically

### For Production (PostgreSQL)
1. **Install PostgreSQL**
2. **Create a database**:
   ```sql
   CREATE DATABASE prelovium;
   CREATE USER prelovium_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE prelovium TO prelovium_user;
   ```
3. **Update DATABASE_URL**:
   ```env
   DATABASE_URL=postgresql://prelovium_user:your_password@localhost/prelovium
   ```

## Installation

1. **Install dependencies**:
   ```bash
   poetry install
   ```

2. **Run the application**:
   ```bash
   poetry run python -m prelovium.webapp.app
   ```

## Features

### Database Integration
- **Upload Storage**: All uploads are stored in the database with metadata
- **Image URLs**: Original and processed image URLs are stored
- **AI Metadata**: Generated product information is saved

### Google Cloud Storage Integration
- **Image Storage**: All images are stored in GCS buckets
- **Public Access**: Processed images are publicly accessible
- **Organized Structure**: Images are organized by upload ID and type

### New UI Features
- **History Page**: View all previous uploads at `/history`
- **Upload Details**: Click on any upload to view detailed information
- **Navigation**: Easy navigation between upload and history pages

## API Endpoints

- `GET /history` - History page
- `GET /api/uploads` - Get all uploads as JSON
- `GET /api/uploads/<upload_id>` - Get specific upload details

## Troubleshooting

### Common Issues

1. **Google Cloud Authentication**:
   - Make sure `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account key
   - Verify the service account has necessary permissions

2. **Bucket Access**:
   - Ensure the bucket exists and is publicly readable
   - Check the bucket name in your environment variables

3. **Database Connection**:
   - For SQLite: Check file permissions in the application directory
   - For PostgreSQL: Verify connection string and database exists

4. **Dependencies**:
   - Run `poetry install` to install all required packages
   - Make sure you have the correct Python version (3.11+)

### Testing the Setup

1. **Test Database Connection**:
   ```python
   from prelovium.utils.database import db
   from prelovium.webapp.app import app
   
   with app.app_context():
       db.create_all()
       print("Database setup successful!")
   ```

2. **Test Google Cloud Storage**:
   ```python
   from prelovium.utils.gcs_storage import GCSStorage
   
   gcs = GCSStorage()
   print(f"Connected to bucket: {gcs.bucket_name}")
   ```

## Security Considerations

- Keep your service account key secure and never commit it to version control
- Use environment variables for all sensitive configuration
- Consider using Google Cloud Identity and Access Management (IAM) for fine-grained permissions
- In production, use a proper database (PostgreSQL) instead of SQLite

## Scaling Considerations

- **Database**: Consider using connection pooling for high-traffic applications
- **Storage**: GCS automatically handles scaling and availability
- **Processing**: Consider using Cloud Run or Kubernetes for horizontal scaling