from google.cloud import storage
import os
import tempfile
import cv2
from typing import Dict, Tuple
import uuid
from dotenv import load_dotenv

load_dotenv()


class GCSStorage:
    """Utility class for Google Cloud Storage operations."""

    def __init__(self):
        self.client = storage.Client()
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "prelovium-prelovium-images")
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_image(self, image_data, blob_name: str) -> str:
        """
        Upload image data to GCS and return the public URL.

        Args:
            image_data: Image data (numpy array from OpenCV or file path)
            blob_name: Name for the blob in GCS

        Returns:
            Public URL of the uploaded image
        """
        blob = self.bucket.blob(blob_name)

        # If image_data is a file path, upload directly
        if isinstance(image_data, str) and os.path.exists(image_data):
            blob.upload_from_filename(image_data)
        else:
            # If it's numpy array (processed image), save to temp file first
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                cv2.imwrite(temp_file.name, image_data)
                blob.upload_from_filename(temp_file.name)
                os.unlink(temp_file.name)

        # Return the public URL - bucket is already configured for public read access via IAM
        return blob.public_url

    def upload_images_for_upload(
        self, upload_id: str, original_files: Dict, processed_images: Dict
    ) -> Tuple[Dict, Dict]:
        """
        Upload both original and processed images for an upload session.

        Args:
            upload_id: Unique identifier for the upload session
            original_files: Dict with 'primary', 'secondary', 'label' file paths
            processed_images: Dict with 'primary', 'secondary', 'label' numpy arrays

        Returns:
            Tuple of (original_urls, processed_urls) dictionaries
        """
        original_urls = {}
        processed_urls = {}

        # Upload original images
        for image_type, file_path in original_files.items():
            blob_name = f"originals/{upload_id}/{image_type}.jpg"
            original_urls[image_type] = self.upload_image(file_path, blob_name)

        # Upload processed images
        for image_type, image_data in processed_images.items():
            blob_name = f"processed/{upload_id}/{image_type}.jpg"
            processed_urls[image_type] = self.upload_image(image_data, blob_name)

        return original_urls, processed_urls

    def delete_images_for_upload(self, upload_id: str):
        """Delete all images associated with an upload session."""
        # Delete original images
        for image_type in ["primary", "secondary", "label"]:
            blob_name = f"originals/{upload_id}/{image_type}.jpg"
            blob = self.bucket.blob(blob_name)
            try:
                blob.delete()
            except Exception as e:
                print(f"Error deleting {blob_name}: {e}")

        # Delete processed images
        for image_type in ["primary", "secondary", "label"]:
            blob_name = f"processed/{upload_id}/{image_type}.jpg"
            blob = self.bucket.blob(blob_name)
            try:
                blob.delete()
            except Exception as e:
                print(f"Error deleting {blob_name}: {e}")

    def generate_signed_url(self, blob_name: str, expiration_minutes: int = 60) -> str:
        """Generate a signed URL for private access to a blob."""
        blob = self.bucket.blob(blob_name)

        # Generate a signed URL that expires in the specified time
        from datetime import datetime, timedelta

        expiration = datetime.utcnow() + timedelta(minutes=expiration_minutes)

        url = blob.generate_signed_url(expiration=expiration)
        return url
