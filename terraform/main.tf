terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "cloud_run_api" {
  project = var.project_id
  service = "run.googleapis.com"
}

resource "google_project_service" "artifact_registry_api" {
  project = var.project_id
  service = "artifactregistry.googleapis.com"
}

resource "google_project_service" "cloud_build_api" {
  project = var.project_id
  service = "cloudbuild.googleapis.com"
}

resource "google_project_service" "storage_api" {
  project = var.project_id
  service = "storage.googleapis.com"
}

resource "google_project_service" "vertex_ai_api" {
  project = var.project_id
  service = "aiplatform.googleapis.com"
}

resource "google_project_service" "iam_api" {
  project = var.project_id
  service = "iam.googleapis.com"
}

resource "google_project_service" "secret_manager_api" {
  project = var.project_id
  service = "secretmanager.googleapis.com"
}

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "prelovium_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = "prelovium"
  description   = "Prelovium application container registry"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry_api]
}

# Create Google Cloud Storage bucket for images
resource "google_storage_bucket" "prelovium_images" {
  name          = "${var.project_id}-prelovium-images"
  location      = var.region
  force_destroy = true

  uniform_bucket_level_access = true

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "PUT", "POST", "DELETE"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.storage_api]
}

# Make bucket publicly readable for serving images
resource "google_storage_bucket_iam_member" "public_access" {
  bucket = google_storage_bucket.prelovium_images.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# Create service account for the application
resource "google_service_account" "prelovium_app" {
  account_id   = "prelovium-app-sa"
  display_name = "Prelovium Application Service Account"
  description  = "Service account for Prelovium application to access GCS and Vertex AI"
}

# Grant permissions to the application service account
resource "google_project_iam_member" "prelovium_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.prelovium_app.email}"
}

resource "google_project_iam_member" "prelovium_vertex_ai_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.prelovium_app.email}"
}

resource "google_project_iam_member" "prelovium_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.prelovium_app.email}"
}

# Create service account key for the application
resource "google_service_account_key" "prelovium_app_key" {
  service_account_id = google_service_account.prelovium_app.name
}

# Create Secret Manager secret for the service account key
resource "google_secret_manager_secret" "prelovium_app_key" {
  secret_id = "prelovium-app-key"
  
  replication {
    auto {}
  }
  
  depends_on = [google_project_service.secret_manager_api]
}

# Store the service account key in Secret Manager
resource "google_secret_manager_secret_version" "prelovium_app_key" {
  secret      = google_secret_manager_secret.prelovium_app_key.id
  secret_data = base64decode(google_service_account_key.prelovium_app_key.private_key)
}

# Cloud Run service
resource "google_cloud_run_v2_service" "prelovium" {
  name     = "prelovium"
  location = var.region
  project  = var.project_id

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/prelovium/prelovium:latest"
      
      ports {
        container_port = 8080
      }

      env {
        name  = "PORT"
        value = "8080"
      }
      
      env {
        name  = "FLASK_APP"
        value = "prelovium.webapp.app:app"
      }
      
      env {
        name  = "FLASK_ENV"
        value = "production"
      }
      
      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }
      
      env {
        name  = "GCS_BUCKET_NAME"
        value = google_storage_bucket.prelovium_images.name
      }
      
      env {
        name  = "DATABASE_URL"
        value = var.database_url
      }
      
      env {
        name  = "GOOGLE_APPLICATION_CREDENTIALS"
        value = "/etc/secrets/gcp-key.json"
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }
      
      volume_mounts {
        name       = "gcp-key"
        mount_path = "/etc/secrets"
      }
    }
    
    volumes {
      name = "gcp-key"
      secret {
        secret_name = google_secret_manager_secret.prelovium_app_key.secret_id
        items {
          key  = "1"
          path = "gcp-key.json"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
    
    service_account = google_service_account.prelovium_app.email
    
    # Allow the service account to access Secret Manager
    annotations = {
      "run.googleapis.com/execution-environment" = "gen2"
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  depends_on = [
    google_project_service.cloud_run_api,
    google_artifact_registry_repository.prelovium_repo
  ]
}

# Make service publicly accessible
resource "google_cloud_run_v2_service_iam_policy" "prelovium_public" {
  location = google_cloud_run_v2_service.prelovium.location
  project  = google_cloud_run_v2_service.prelovium.project
  service  = google_cloud_run_v2_service.prelovium.name

  policy_data = data.google_iam_policy.public_access.policy_data
}

data "google_iam_policy" "public_access" {
  binding {
    role = "roles/run.invoker"
    members = [
      "allUsers",
    ]
  }
}

# Service account for GitHub Actions
resource "google_service_account" "github_actions" {
  account_id   = "github-actions-sa"
  display_name = "GitHub Actions Service Account"
  description  = "Service account for GitHub Actions to deploy to Cloud Run"
}

# Grant necessary permissions to GitHub Actions service account
resource "google_project_iam_member" "github_actions_cloud_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_artifact_registry_writer" {
  project = var.project_id
  role    = "roles/artifactregistry.writer"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

resource "google_project_iam_member" "github_actions_service_account_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.github_actions.email}"
}

# Create service account key for GitHub Actions
resource "google_service_account_key" "github_actions_key" {
  service_account_id = google_service_account.github_actions.name
}