# Prelovium

A startup idea I had a while ago and tinkered on a bit. This is a prototype of a web application where a user can upload just 3 images of a pre-loved fashion item, and the images are automatically enhanced to look professional (this might motivate potential buyers), and an online ad is automatically generated. The idea would be that this online ad is then automatically published on all available online marketplaces, such that it reaches the widest range of possible buyers.

## Features

- Enhances images, segments items and puts them in front of a neutral background.
- Generates online ad: suggests title, price, description, material, color, size, etc.
- And I got plenty ideas for more features :) 

## Development

This project uses Poetry for dependency management and Flask for the web application.

### Prerequisites

1. Python 3.11 or higher
2. Poetry
3. Google Cloud account with Vertex AI API enabled
4. Google Cloud credentials set up locally

### Setup

1. Install Poetry
2. Install dependencies:
   ```bash
   poetry install
   ```
3. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
4. Update the `.env` file with your Google Cloud project ID
5. Run the development server:
   ```bash
   cd prelovium/webapp 
   poetry run python app.py
   ```

## Deployment

The application is configured to deploy to Google Cloud Run. To deploy:

1. Make sure you have the Google Cloud CLI installed and configured
2. Run:
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```
3. Run:
   ```bash
   gcloud beta run services add-iam-policy-binding --region=us-central1 --member=allUsers --role=roles/run.invoker prelovium
   ```
   to make the service public.

The application will be deployed to a public URL in the format: `https://prelovium-xxxxx-uc.a.run.app`

## Environment Variables

- `GOOGLE_CLOUD_PROJECT`: Your Google Cloud project ID
- `FLASK_APP`: Flask application entry point
- `FLASK_ENV`: Flask environment (development/production)
- `FLASK_DEBUG`: Enable/disable Flask debug mode
- `PORT`: Port to run the application on

## License

This project is open source and available under the Apache 2.0 License License. If you stumble over this or use it, I would be really happy to hear your feedback and ideas! 
