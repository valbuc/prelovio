import json
import glob
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part, FinishReason, Image
import vertexai.preview.generative_models as generative_models
from dotenv import load_dotenv

load_dotenv()


system_prompt = """You are provided with 3 photos of a fashion item.
These photos will be used to advertise the item on online second hand marketplaces.
Given the 3 photos, you are supposed to suggest a title, a short description, a price (in euro),
a brand, the web domain of the brand (starting with www.), and the item's size and color(s),
material(s), and category/categories. If you cannot deduce information, enter 'NA'.
Please return the output in a json of the following format:

{
	"title": "...",
	"description": "...":,
    "
	"price": 15,
	"brand": "...",
	"brand_domain": "www....",
	"size": "...",
	"colors": ["green", "...", ...],
    "materials": ["cotton", "...", ...],
    "categories": ["shorts", "...", ...]
}

Only return the json object and nothing else.
"""

generation_config = {
    "max_output_tokens": 256,
    "top_p": 0.95,
    "temperature": 0,
}

safety_settings = {
    generative_models.HarmCategory.HARM_CATEGORY_HATE_SPEECH: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    generative_models.HarmCategory.HARM_CATEGORY_HARASSMENT: generative_models.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}


def generate_metadata(folder_path):
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is not set")

    vertexai.init(project=project_id, location="us-central1")

    # for each png or jpeg file in the folder_path, load image
    all_image_files = glob.glob(folder_path + "/*.png") + glob.glob(
        folder_path + "/*.jpeg"
    )
    images = []
    for image_path in all_image_files:
        image = Image.load_from_file(image_path)
        images.append(image)

    model = GenerativeModel("gemini-2.0-flash", system_instruction=[system_prompt])
    responses = model.generate_content(
        ["""Photos:"""] + images,
        generation_config=generation_config,
        safety_settings=safety_settings,
    )

    # Clean the response text by removing markdown code block formatting
    response_text = responses.candidates[0].content.parts[0].text
    response_text = response_text.replace("```json", "").replace("```", "").strip()
    return json.loads(response_text)


def metadata_to_markdown(metadata: dict):
    markdown = "## "
    markdown += metadata["title"] + "\n"
    markdown += "#### Price: " + str(metadata["price"]) + "\n"
    markdown += "Size: " + metadata["size"] + "\n\n"
    markdown += "Colors: " + ", ".join(metadata["colors"]) + "\n\n"
    markdown += "Materials: " + ", ".join(metadata["materials"]) + "\n\n"
    markdown += "Categories: " + ", ".join(metadata["categories"]) + "\n\n"
    if metadata["brand_domain"] == "NA":
        markdown += "Brand: " + metadata["brand"] + "\n\n"
    else:
        markdown += (
            "Brand: ["
            + metadata["brand"]
            + "](https://"
            + metadata["brand_domain"]
            + ")\n\n"
        )
    markdown += "\n" + metadata["description"] + "\n"
    return markdown
