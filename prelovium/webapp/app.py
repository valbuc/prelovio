from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from werkzeug.utils import secure_filename
import json
import cv2
import uuid
from datetime import datetime

from prelovium.utils.image_processing import prettify, save_image, load_image
from prelovium.utils.metadata import generate_metadata
from prelovium.utils.database import db, Upload, migrate_existing_uploads
from prelovium.utils.gcs_storage import GCSStorage

app = Flask(__name__)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL", "sqlite:///prelovium.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize database
db.init_app(app)

# Initialize Google Cloud Storage
gcs = GCSStorage()

app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "temp", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Example items
EXAMPLES = ["jacket", "shirt", "jeans", "shoes", "boots", "pants", "suit", "jumper"]

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")

# Create database tables and run migrations
with app.app_context():
    db.create_all()
    migrate_existing_uploads()  # Run migration to add status field to existing uploads


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/health")
def health_check():
    """Health check endpoint for Cloud Run startup probe."""
    return jsonify({"status": "healthy"}), 200


@app.route("/")
def index():
    return render_template("index.html", examples=EXAMPLES)


@app.route("/examples/<item_type>/<image_type>")
def example_image(item_type, image_type):
    if item_type not in EXAMPLES or image_type not in ["primary", "secondary", "label"]:
        return jsonify({"error": "Invalid example request"}), 400

    # Serve from the new location
    example_dir = os.path.join(EXAMPLES_DIR, item_type)
    filename = f"{image_type}.jpeg"
    return send_from_directory(example_dir, filename)


@app.route("/process", methods=["POST"])
def process_images():
    if request.is_json:
        # Handle example request
        data = request.get_json()
        if "example" not in data or data["example"] not in EXAMPLES:
            return jsonify({"error": "Invalid example request"}), 400

        example_type = data["example"]
        example_folder = os.path.join(EXAMPLES_DIR, example_type)
        primary_path = os.path.join(example_folder, "primary.jpeg")

        # Process example images
        secondary_path = os.path.join(example_folder, "secondary.jpeg")
        label_path = os.path.join(example_folder, "label.jpeg")

        # Create a unique folder for this example
        upload_id = secure_filename(f"example_{example_type}_{str(uuid.uuid4())[:8]}")
        upload_folder = os.path.join(app.config["UPLOAD_FOLDER"], upload_id)
        os.makedirs(upload_folder, exist_ok=True)

        # Process images
        primary_image = prettify(primary_path)
        secondary_image = prettify(secondary_path)
        label_image = load_image(label_path, cv2.COLOR_BGR2RGB)

        # Save processed images locally for metadata generation
        save_image(os.path.join(upload_folder, "primary_processed.jpeg"), primary_image)
        save_image(
            os.path.join(upload_folder, "secondary_processed.jpeg"), secondary_image
        )
        save_image(os.path.join(upload_folder, "label_processed.jpeg"), label_image)

        # Generate metadata
        metadata = generate_metadata(upload_folder)

        try:
            # Upload to Google Cloud Storage
            original_files = {
                "primary": primary_path,
                "secondary": secondary_path,
                "label": label_path,
            }
            processed_images = {
                "primary": primary_image,
                "secondary": secondary_image,
                "label": label_image,
            }

            original_urls, processed_urls = gcs.upload_images_for_upload(
                upload_id, original_files, processed_images
            )

            # Save to database
            upload_record = Upload.from_metadata(
                upload_id, original_urls, processed_urls, metadata
            )
            db.session.add(upload_record)
            db.session.commit()

            # Clean up local files
            import shutil

            shutil.rmtree(upload_folder)

            return jsonify(
                {
                    "primary": processed_urls["primary"],
                    "secondary": processed_urls["secondary"],
                    "label": processed_urls["label"],
                    "metadata": metadata,
                    "upload_id": upload_id,
                }
            )

        except Exception as e:
            print(f"Error processing example: {e}")
            # Fallback to local serving
            return jsonify(
                {
                    "primary": f"/uploads/{upload_id}/primary_processed.jpeg",
                    "secondary": f"/uploads/{upload_id}/secondary_processed.jpeg",
                    "label": f"/uploads/{upload_id}/label_processed.jpeg",
                    "metadata": metadata,
                    "upload_id": upload_id,
                }
            )

    # Handle file upload request
    if (
        "primary" not in request.files
        or "secondary" not in request.files
        or "label" not in request.files
    ):
        return jsonify({"error": "Missing required images"}), 400

    primary = request.files["primary"]
    secondary = request.files["secondary"]
    label = request.files["label"]

    if not all([primary.filename, secondary.filename, label.filename]):
        return jsonify({"error": "No selected files"}), 400

    if not all([allowed_file(f.filename) for f in [primary, secondary, label]]):
        return (
            jsonify({"error": f"Invalid file type, Please use .png, .jpg or .jpeg"}),
            400,
        )

    # Create a unique upload ID
    upload_id = str(uuid.uuid4())
    upload_folder = os.path.join(app.config["UPLOAD_FOLDER"], upload_id)
    os.makedirs(upload_folder, exist_ok=True)

    # Save uploaded files
    primary_path = os.path.join(upload_folder, "primary.jpeg")
    secondary_path = os.path.join(upload_folder, "secondary.jpeg")
    label_path = os.path.join(upload_folder, "label.jpeg")

    primary.save(primary_path)
    secondary.save(secondary_path)
    label.save(label_path)

    try:
        # Process images
        primary_image = prettify(primary_path)
        secondary_image = prettify(secondary_path)
        label_image = load_image(label_path, cv2.COLOR_BGR2RGB)

        # Save processed images locally for metadata generation
        save_image(os.path.join(upload_folder, "primary_processed.jpeg"), primary_image)
        save_image(
            os.path.join(upload_folder, "secondary_processed.jpeg"), secondary_image
        )
        save_image(os.path.join(upload_folder, "label_processed.jpeg"), label_image)

        # Generate metadata
        metadata = generate_metadata(upload_folder)

        # Upload to Google Cloud Storage
        original_files = {
            "primary": primary_path,
            "secondary": secondary_path,
            "label": label_path,
        }
        processed_images = {
            "primary": primary_image,
            "secondary": secondary_image,
            "label": label_image,
        }

        original_urls, processed_urls = gcs.upload_images_for_upload(
            upload_id, original_files, processed_images
        )

        # Save to database
        upload_record = Upload.from_metadata(
            upload_id, original_urls, processed_urls, metadata
        )
        db.session.add(upload_record)
        db.session.commit()

        # Clean up local files
        import shutil

        shutil.rmtree(upload_folder)

        return jsonify(
            {
                "primary": processed_urls["primary"],
                "secondary": processed_urls["secondary"],
                "label": processed_urls["label"],
                "metadata": metadata,
                "upload_id": upload_id,
            }
        )

    except Exception as e:
        print(f"Error processing upload: {e}")
        # Clean up local files on error
        import shutil

        if os.path.exists(upload_folder):
            shutil.rmtree(upload_folder)
        return jsonify({"error": "Failed to process images"}), 500


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/history")
def history():
    """Display all previous uploads."""
    try:
        # Get status filter from query parameter
        status_filter = request.args.get('status', 'all')
        
        # Build query based on status filter
        query = Upload.query
        if status_filter != 'all' and status_filter in Upload.VALID_STATUSES:
            query = query.filter(Upload.status == status_filter)
        
        # Get all uploads ordered by most recent first
        uploads = query.order_by(Upload.created_at.desc()).all()
        uploads_data = [upload.to_dict() for upload in uploads]

        return render_template("history.html", uploads=uploads_data, current_filter=status_filter)
    except Exception as e:
        print(f"Error loading history: {e}")
        return render_template(
            "history.html", uploads=[], error="Failed to load upload history", current_filter='all'
        )


@app.route("/api/uploads")
def api_uploads():
    """API endpoint to get all uploads as JSON."""
    try:
        # Get status filter from query parameter
        status_filter = request.args.get('status', 'all')
        
        # Build query based on status filter
        query = Upload.query
        if status_filter != 'all' and status_filter in Upload.VALID_STATUSES:
            query = query.filter(Upload.status == status_filter)
        
        uploads = query.order_by(Upload.created_at.desc()).all()
        uploads_data = [upload.to_dict() for upload in uploads]
        return jsonify(uploads_data)
    except Exception as e:
        print(f"Error loading uploads: {e}")
        return jsonify({"error": "Failed to load uploads"}), 500


@app.route("/api/uploads/<upload_id>")
def api_upload_detail(upload_id):
    """API endpoint to get details of a specific upload."""
    try:
        upload = Upload.query.filter_by(upload_id=upload_id).first()
        if not upload:
            return jsonify({"error": "Upload not found"}), 404

        return jsonify(upload.to_dict())
    except Exception as e:
        print(f"Error loading upload {upload_id}: {e}")
        return jsonify({"error": "Failed to load upload"}), 500


@app.route("/api/uploads/<upload_id>/status", methods=["PUT"])
def api_update_upload_status(upload_id):
    """API endpoint to update the status of a specific upload."""
    try:
        upload = Upload.query.filter_by(upload_id=upload_id).first()
        if not upload:
            return jsonify({"error": "Upload not found"}), 404

        data = request.get_json()
        if not data or 'status' not in data:
            return jsonify({"error": "Status is required"}), 400

        new_status = data['status']
        
        # Validate and update status
        try:
            upload.update_status(new_status)
            db.session.commit()
            return jsonify({"message": "Status updated successfully", "upload": upload.to_dict()})
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
            
    except Exception as e:
        print(f"Error updating upload {upload_id}: {e}")
        return jsonify({"error": "Failed to update upload status"}), 500


@app.route("/api/statuses")
def api_get_statuses():
    """API endpoint to get all valid statuses."""
    try:
        statuses = [
            {
                'value': status,
                'label': Upload().get_status_display() if status == 'in_review' else status.replace('_', ' ').title(),
                'color': Upload().get_status_color() if status == 'in_review' else 'gray'
            }
            for status in Upload.VALID_STATUSES
        ]
        
        # Fix the status display labels and colors
        status_info = {
            'in_review': {'label': 'In Review', 'color': 'yellow'},
            'published': {'label': 'Published', 'color': 'green'},
            'hidden': {'label': 'Hidden', 'color': 'gray'},
            'deleted': {'label': 'Deleted', 'color': 'red'},
            'sold': {'label': 'Sold', 'color': 'blue'}
        }
        
        statuses = [
            {
                'value': status,
                'label': status_info[status]['label'],
                'color': status_info[status]['color']
            }
            for status in Upload.VALID_STATUSES
        ]
        
        return jsonify(statuses)
    except Exception as e:
        print(f"Error loading statuses: {e}")
        return jsonify({"error": "Failed to load statuses"}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
