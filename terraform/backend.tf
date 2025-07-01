# Terraform backend configuration
# This file configures remote state storage (optional)
# Uncomment and configure the backend block if you want to store Terraform state remotely

# terraform {
#   backend "gcs" {
#     bucket = "your-terraform-state-bucket"
#     prefix = "terraform/state"
#   }
# }

# To use remote state:
# 1. Create a GCS bucket for storing Terraform state
# 2. Uncomment the backend block above
# 3. Update the bucket name
# 4. Run: terraform init -migrate-state