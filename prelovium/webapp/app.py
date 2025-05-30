from flask import Flask, request, jsonify, render_template, send_from_directory
import os
from werkzeug.utils import secure_filename
import json
import cv2

from prelovium.utils.image_processing import prettify, save_image, load_image
from prelovium.utils.metadata import generate_metadata

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "temp", "uploads")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# Example items
EXAMPLES = ["jacket", "shirt", "jeans", "shoes", "boots", "pants", "suit", "jumper"]

# Ensure upload directory exists
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "examples")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


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
        upload_id = secure_filename(f"example_{example_type}")
        upload_folder = os.path.join(app.config["UPLOAD_FOLDER"], upload_id)
        os.makedirs(upload_folder, exist_ok=True)

        # Process images
        primary_image = prettify(primary_path)
        secondary_image = prettify(secondary_path)
        label_image = load_image(label_path, cv2.COLOR_BGR2RGB)

        # Save processed images
        save_image(os.path.join(upload_folder, "primary_processed.jpeg"), primary_image)
        save_image(
            os.path.join(upload_folder, "secondary_processed.jpeg"), secondary_image
        )
        save_image(os.path.join(upload_folder, "label_processed.jpeg"), label_image)

        # Generate metadata
        metadata = generate_metadata(upload_folder)
        metadata_path = os.path.join(upload_folder, "metadata.json")
        json.dump(metadata, open(metadata_path, "w"), indent=4)

        return jsonify(
            {
                "primary": f"/uploads/{upload_id}/primary_processed.jpeg",
                "secondary": f"/uploads/{upload_id}/secondary_processed.jpeg",
                "label": f"/uploads/{upload_id}/label_processed.jpeg",
                "metadata": metadata,
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

    # Create a unique folder for this upload
    upload_id = secure_filename(
        str(hash(primary.filename + secondary.filename + label.filename))
    )
    upload_folder = os.path.join(app.config["UPLOAD_FOLDER"], upload_id)
    os.makedirs(upload_folder, exist_ok=True)

    # Save and process images
    primary_path = os.path.join(upload_folder, "primary.jpeg")
    secondary_path = os.path.join(upload_folder, "secondary.jpeg")
    label_path = os.path.join(upload_folder, "label.jpeg")

    primary.save(primary_path)
    secondary.save(secondary_path)
    label.save(label_path)

    # Process images
    primary_image = prettify(primary_path)
    secondary_image = prettify(secondary_path)
    label_image = load_image(label_path, cv2.COLOR_BGR2RGB)

    # Save processed images
    save_image(os.path.join(upload_folder, "primary_processed.jpeg"), primary_image)
    save_image(os.path.join(upload_folder, "secondary_processed.jpeg"), secondary_image)
    save_image(os.path.join(upload_folder, "label_processed.jpeg"), label_image)

    # Generate metadata
    metadata = generate_metadata(upload_folder)
    metadata_path = os.path.join(upload_folder, "metadata.json")
    json.dump(metadata, open(metadata_path, "w"), indent=4)

    return jsonify(
        {
            "primary": f"/uploads/{upload_id}/primary_processed.jpeg",
            "secondary": f"/uploads/{upload_id}/secondary_processed.jpeg",
            "label": f"/uploads/{upload_id}/label_processed.jpeg",
            "metadata": metadata,
        }
    )


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
