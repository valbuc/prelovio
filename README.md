# Prelovium

A web application for image processing and analysis using Flask and OpenCV.

## Architecture

- **Backend**: Flask web application with image processing capabilities
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

### Initial Setup

1. **Set up GCP project**:
   ```bash
   make setup-gcp PROJECT_ID=prelovio
   ```

2. **Configure Terraform**:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your project details
   ```

3. **Initialize and apply Terraform**:
   ```bash
   make terraform-init
   make terraform-plan
   make terraform-apply
   ```

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
make deploy PROJECT_ID=prelovio
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

- `GET /` - Main application interface
- `POST /process` - Process uploaded images
- `GET /examples/<item_type>/<image_type>` - Serve example images
- `GET /uploads/<filename>` - Serve processed images

## Environment Variables

- `PORT` - Server port (default: 8080)
- `FLASK_APP` - Flask application entry point
- `FLASK_ENV` - Flask environment (development/production)
- `GOOGLE_CLOUD_PROJECT` - GCP project ID

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Run linting and tests
6. Submit a pull request

## License

This project is licensed under the MIT License. 
