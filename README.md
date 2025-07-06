# Prelovium

A web application for image processing and analysis using Flask and OpenCV, with database storage and Google Cloud Storage integration.

## Features

- 🖼️ **Image Processing**: AI-powered background removal and enhancement
- 🤖 **AI Metadata Generation**: Automatic product descriptions using Google Vertex AI
- 💾 **Database Storage**: SQLAlchemy-based storage for upload history and metadata
- ☁️ **Cloud Storage**: Google Cloud Storage for scalable image storage
- 📱 **Modern UI**: Responsive web interface with upload history
- 🔐 **Secure**: Service account-based authentication with Secret Manager

## Architecture

- **Backend**: Flask web application with SQLAlchemy database
- **Storage**: Google Cloud Storage for images, database for metadata
- **AI/ML**: Google Vertex AI for metadata generation
- **Infrastructure**: Google Cloud Run with Terraform for infrastructure as code
- **CI/CD**: GitHub Actions for automated deployment
- **Container Registry**: Google Artifact Registry
- **Development**: Poetry for Python dependency management

## Prerequisites

- Python 3.11+
- Poetry
- Docker
- Google Cloud SDK (`gcloud`)
- Terraform (for infrastructure management)

## Local Development

### Setup

1. **Install dependencies**:
   ```bash
   make install
   ```

2. **Run the application locally**:
   ```bash
   make run
   ```

3. **Run with Docker locally**:
   ```bash
   make deploy-local
   ```

4. **Development mode with hot reload**:
   ```bash
   make dev
   ```

### Available Make Commands

Run `make help` to see all available commands:

- `make install` - Install dependencies using Poetry
- `make test` - Run tests
- `make build` - Build Docker image locally
- `make run` - Run the application locally
- `make run-docker` - Run the application in Docker locally
- `make deploy-local` - Deploy to local Docker
- `make dev` - Start development environment with hot reload
- `make deploy` - Deploy to Google Cloud Run
- `make clean` - Clean up local Docker images and containers
- `make lint` - Run linting tools
- `make format` - Format code
- `make check` - Check code quality

## Cloud Deployment

### Automated Infrastructure Setup (Recommended)

The easiest way to deploy is using the included Terraform configuration:

1. **Prerequisites**:
   ```bash
   # Install Terraform and authenticate with Google Cloud
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Configure Terraform**:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your project details
   ```

3. **Deploy everything**:
   ```bash
   terraform init
   terraform plan
   terraform apply
   ```

This automatically creates:
- ✅ Google Cloud Storage bucket for images
- ✅ Service account with proper permissions
- ✅ Cloud Run service with environment variables
- ✅ Secret Manager for secure credential storage
- ✅ Database configuration
- ✅ All required APIs enabled

📖 **For detailed setup instructions, see [TERRAFORM_DEPLOYMENT.md](TERRAFORM_DEPLOYMENT.md)**

### Manual Setup (Alternative)

For manual infrastructure setup, see [DATABASE_SETUP.md](DATABASE_SETUP.md)

### GitHub Actions Setup

1. **Set up GitHub repository secrets**:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: Service account key JSON (base64 encoded)

2. **Get the service account key** (after running Terraform):
   ```bash
   cd terraform
   terraform output -raw github_actions_service_account_key | base64 -d > sa-key.json
   ```

3. **Base64 encode the service account key**:
   ```bash
   base64 -i sa-key.json
   ```

4. **Add the base64 encoded key to GitHub secrets** as `GCP_SA_KEY`

### Manual Deployment

For manual deployment to Google Cloud Run:

```bash
make deploy PROJECT_ID=prelovium
```

## Project Structure

```
prelovium/
├── .github/workflows/     # GitHub Actions workflows
├── terraform/            # Terraform infrastructure code
├── prelovium/           # Main application code
│   ├── utils/           # Utility modules
│   └── webapp/          # Flask web application
├── Dockerfile           # Container configuration
├── Makefile            # Build and deployment commands
├── pyproject.toml      # Python project configuration
└── README.md           # This file
```

## Infrastructure

The application is deployed on Google Cloud Platform using:

- **Cloud Run**: Serverless container platform
- **Artifact Registry**: Container image storage
- **Terraform**: Infrastructure as Code
- **GitHub Actions**: CI/CD pipeline

### Terraform Resources

- Google Cloud Run service
- Artifact Registry repository
- IAM service accounts and bindings
- Required API enablement

## Development Workflow

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes and test locally**:
   ```bash
   make dev
   ```

3. **Format and lint code**:
   ```bash
   make format
   make check
   ```

4. **Commit and push**:
   ```bash
   git add .
   git commit -m "Add your feature"
   git push origin feature/your-feature
   ```

5. **Create pull request** - GitHub Actions will run tests

6. **Merge to main** - Automatic deployment to production

## API Endpoints

### Web Interface
- `GET /` - Main application interface for image upload
- `GET /history` - View all previous uploads and generated ads
- `POST /process` - Process uploaded images and generate metadata

### API Endpoints
- `GET /api/uploads` - Get all uploads as JSON
- `GET /api/uploads/<upload_id>` - Get specific upload details
- `GET /examples/<item_type>/<image_type>` - Serve example images
- `GET /uploads/<filename>` - Serve processed images (legacy support)

### New Features
- **Upload History**: View all previous uploads in a beautiful grid layout
- **Detailed View**: Click on any upload to see full details in a modal
- **Cloud Storage**: All images automatically uploaded to Google Cloud Storage
- **Database Integration**: Upload metadata and AI-generated ads stored in database

## Environment Variables

### Runtime Configuration
- `PORT` - Server port (default: 8080)
- `FLASK_APP` - Flask application entry point
- `FLASK_ENV` - Flask environment (development/production)

### Google Cloud Configuration
- `GOOGLE_CLOUD_PROJECT` - GCP project ID
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to service account key file
- `GCS_BUCKET_NAME` - Google Cloud Storage bucket name for images

### Database Configuration
- `DATABASE_URL` - Database connection string (SQLite or PostgreSQL)

**Note**: When using Terraform deployment, these variables are automatically configured!

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run linting and tests
6. Submit a pull request

## License

This project is licensed under the MIT License. 
