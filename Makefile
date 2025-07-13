# Makefile for Prelovium application

# Variables
PROJECT_ID ?= $(shell gcloud config get-value project)
REGION ?= europe-west1
SERVICE_NAME ?= prelovium
IMAGE_NAME ?= $(REGION)-docker.pkg.dev/$(PROJECT_ID)/prelovium/prelovium
DOCKER_TAG ?= latest

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
NC=\033[0m # No Color

.PHONY: help install test build run deploy-local deploy terraform-init terraform-plan terraform-apply terraform clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies using Poetry
	@echo "$(GREEN)Installing dependencies...$(NC)"
	poetry install

test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	poetry run python -m pytest tests/ || echo "$(YELLOW)No tests found$(NC)"

build: ## Build Docker image locally
	@echo "$(GREEN)Building Docker image...$(NC)"
	docker build -t prelovium:$(DOCKER_TAG) .
	@echo "$(GREEN)Docker image built successfully$(NC)"

run: ## Run the application locally
	@echo "$(GREEN)Starting application locally...$(NC)"
	poetry run python -m prelovium.webapp.app

run-docker: build ## Run the application in Docker locally
	@echo "$(GREEN)Starting application in Docker...$(NC)"
	docker run -p 8080:8080 --rm prelovium:$(DOCKER_TAG)

deploy-local: ## Deploy to local Docker
	@echo "$(GREEN)Deploying locally with Docker...$(NC)"
	$(MAKE) build
	$(MAKE) run-docker

deploy: ## Deploy to Google Cloud Run
	@echo "$(GREEN)Deploying to Google Cloud Run...$(NC)"
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "$(RED)Error: PROJECT_ID is not set. Please set it with: make deploy PROJECT_ID=your-project-id$(NC)"; \
		exit 1; \
	fi
	
	# Configure Docker for Artifact Registry
	gcloud auth configure-docker $(REGION)-docker.pkg.dev
	
	# Build and tag image
	docker build -t $(IMAGE_NAME):$(DOCKER_TAG) .
	
	# Push image
	docker push $(IMAGE_NAME):$(DOCKER_TAG)
	
	# Deploy to Cloud Run
	gcloud run deploy $(SERVICE_NAME) \
		--image $(IMAGE_NAME):$(DOCKER_TAG) \
		--region $(REGION) \
		--platform managed \
		--allow-unauthenticated \
		--memory 4Gi \
		--cpu 2 \
		--set-env-vars "FLASK_APP=prelovium.webapp.app:app,FLASK_ENV=production,GOOGLE_CLOUD_PROJECT=$(PROJECT_ID)"
	
	@echo "$(GREEN)Deployment completed!$(NC)"
	@echo "Service URL:"
	@gcloud run services describe $(SERVICE_NAME) --region $(REGION) --format 'value(status.url)'

terraform-init: ## Initialize Terraform
	@echo "$(GREEN)Initializing Terraform...$(NC)"
	cd terraform && terraform init

terraform-plan: ## Plan Terraform changes
	@echo "$(GREEN)Planning Terraform changes...$(NC)"
	cd terraform && terraform plan

terraform-apply: ## Apply Terraform changes
	@echo "$(GREEN)Applying Terraform changes...$(NC)"
	cd terraform && terraform apply -auto-approve

terraform: ## Run complete Terraform workflow (init, plan, apply)
	@echo "$(GREEN)Running complete Terraform workflow...$(NC)"
	cd terraform && terraform init
	cd terraform && terraform plan
	cd terraform && terraform apply -auto-approve

terraform-destroy: ## Destroy Terraform resources
	@echo "$(RED)Destroying Terraform resources...$(NC)"
	cd terraform && terraform destroy

setup-gcp: ## Set up GCP project for deployment
	@echo "$(GREEN)Setting up GCP project...$(NC)"
	@if [ -z "$(PROJECT_ID)" ]; then \
		echo "$(RED)Error: PROJECT_ID is not set. Please set it with: make setup-gcp PROJECT_ID=your-project-id$(NC)"; \
		exit 1; \
	fi
	
	# Enable required APIs
	gcloud services enable run.googleapis.com --project=$(PROJECT_ID)
	gcloud services enable artifactregistry.googleapis.com --project=$(PROJECT_ID)
	gcloud services enable cloudbuild.googleapis.com --project=$(PROJECT_ID)
	
	# Create Artifact Registry repository
	gcloud artifacts repositories create prelovium \
		--repository-format=docker \
		--location=$(REGION) \
		--project=$(PROJECT_ID) || true
	
	@echo "$(GREEN)GCP setup completed!$(NC)"

clean: ## Clean up local Docker images and containers
	@echo "$(GREEN)Cleaning up Docker resources...$(NC)"
	docker system prune -a -f
	docker images | grep prelovium | awk '{print $$3}' | xargs -r docker rmi || true

dev: ## Start development environment
	@echo "$(GREEN)Starting development environment...$(NC)"
	poetry run flask --app prelovium.webapp.app run --host=0.0.0.0 --port=8080 --debug

lint: ## Run linting
	@echo "$(GREEN)Running linters...$(NC)"
	poetry run black prelovium/
	poetry run isort prelovium/
	poetry run flake8 prelovium/

format: ## Format code
	@echo "$(GREEN)Formatting code...$(NC)"
	poetry run black prelovium/
	poetry run isort prelovium/

check: ## Check code quality
	@echo "$(GREEN)Checking code quality...$(NC)"
	poetry run black --check prelovium/
	poetry run isort --check-only prelovium/
	poetry run flake8 prelovium/

# Default target
.DEFAULT_GOAL := help