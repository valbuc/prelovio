output "service_url" {
  description = "URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.prelovium.uri
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = google_artifact_registry_repository.prelovium_repo.name
}

output "github_actions_service_account_email" {
  description = "Email of the GitHub Actions service account"
  value       = google_service_account.github_actions.email
}

output "github_actions_service_account_key" {
  description = "Base64 encoded service account key for GitHub Actions"
  value       = google_service_account_key.github_actions_key.private_key
  sensitive   = true
}

output "gcs_bucket_name" {
  description = "Name of the Google Cloud Storage bucket for images"
  value       = google_storage_bucket.prelovium_images.name
}

output "gcs_bucket_url" {
  description = "URL of the Google Cloud Storage bucket"
  value       = google_storage_bucket.prelovium_images.url
}

output "prelovium_app_service_account_email" {
  description = "Email of the Prelovium application service account"
  value       = google_service_account.prelovium_app.email
}

output "prelovium_app_service_account_key" {
  description = "Base64 encoded service account key for the Prelovium application"
  value       = google_service_account_key.prelovium_app_key.private_key
  sensitive   = true
}