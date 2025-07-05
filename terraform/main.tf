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

# Create Artifact Registry repository
resource "google_artifact_registry_repository" "prelovium_repo" {
  project       = var.project_id
  location      = var.region
  repository_id = "prelovium"
  description   = "Prelovium application container registry"
  format        = "DOCKER"

  depends_on = [google_project_service.artifact_registry_api]
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

      resources {
        limits = {
          cpu    = "2"
          memory = "4Gi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
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
  name     = google_cloud_run_v2_service.prelovium.name

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