import cv2
import numpy as np
from PIL import Image
from transformers import pipeline
import matplotlib.pyplot as plt
import tempfile
import os

BLUR_AMOUNT = 32  # blor of shadow
OFFSET_X = -25  # Horizontal offset for the shadow
OFFSET_Y = 60  # Vertical offset for the shadow
OPACITY = 0.2  # intensity/darkness of shadow
TOP_COLOR = [245, 245, 245]  # rgb
BOTTOM_COLOR = [235, 235, 235]  # rgb
VIGNETTE_EXPONENT = 2  # harshness of vignette onset
VIGNETTE_SCALE = 0.1  # intensity/darkness of vignette
PADDING = 0.1

pipe = pipeline("image-segmentation", model="briaai/RMBG-1.4", trust_remote_code=True)


def remove_background(image_path):
    """using hf model for background removal"""
    pillow_image = pipe(image_path)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        pillow_image.save(temp_file.name, "PNG")
    return pillow_image


def trim_and_pad_image(image, padding_ratio=0.1, vertical_ratio=1.333):
    """removing edges without content and adding regular padding"""
    bbox = image.getbbox()
    trimmed_image = image.crop(bbox)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        trimmed_image.save(temp_file.name, "PNG")

    # add padding
    width, height = trimmed_image.size
    padding_width = int(width * padding_ratio)
    padding_height = int(height * padding_ratio)
    padded_width = width + 2 * padding_width
    padded_height = height + 2 * padding_height
    padded_image = Image.new("RGBA", (padded_width, padded_height), (0, 0, 0, 0))
    padded_image.paste(trimmed_image, (padding_width, padding_height))

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        padded_image.save(temp_file.name, "PNG")

    # expand to target ratio
    if padded_height < padded_width * vertical_ratio:
        target_height = int(padded_width * vertical_ratio)
        target_width = padded_width
    elif padded_height > padded_width * vertical_ratio:
        target_width = int(padded_height / vertical_ratio)
        target_height = padded_height
    else:
        # Image already has the correct ratio
        target_width = padded_width
        target_height = padded_height
    
    final_image = Image.new("RGBA", (target_width, target_height), (0, 0, 0, 0))
    
    # Calculate precise centering using integer division for perfect centering
    center_x = (target_width - padded_width) // 2
    center_y = (target_height - padded_height) // 2
    
    final_image.paste(padded_image, (center_x, center_y))

    # Save the result
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
        final_image.save(temp_file.name, "PNG")
    return final_image


def load_image(path, color_conversion=None):
    """Load an image and optionally convert its color."""
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)
    if color_conversion:
        image = cv2.cvtColor(image, color_conversion)
    return image


def extract_alpha_channel(image):
    """Extract the alpha channel and the RGB channels from an image."""
    alpha_channel = image[:, :, 3]
    rgb_channels = image[:, :, 0:3]
    return alpha_channel, rgb_channels


def apply_blur_to_alpha(alpha, blur_amount):
    """Apply blur to the alpha channel."""
    return cv2.blur(alpha, (blur_amount, blur_amount))


def expand_and_normalize_alpha(alpha):
    """Expand alpha dimensions and normalize its values to the range [0,1]."""
    expanded_alpha = np.expand_dims(alpha, axis=2)
    repeated_alpha = np.repeat(expanded_alpha, 3, axis=2)
    normalized_alpha = repeated_alpha / 255
    return normalized_alpha


def offset_alpha(alpha, offset_x, offset_y):
    """Offset the alpha channel to simulate shadow direction."""
    rows, cols = alpha.shape
    translation_matrix = np.float32([[1, 0, offset_x], [0, 1, offset_y]])
    offset_alpha = cv2.warpAffine(alpha, translation_matrix, (cols, rows))
    return offset_alpha


def create_shadow_on_bg(bg, alpha_blur, opacity=0.5):
    """Put shadow (based on blurred alpha) on top of the background."""
    black_canvas = np.zeros(bg.shape, dtype=np.uint8)
    shadowed_bg = (
        (opacity * alpha_blur) * black_canvas + (1 - (opacity * alpha_blur)) * bg
    ).astype(np.uint8)
    return shadowed_bg


def composite_foreground_on_bg(fg, alpha, bg_with_shadow):
    """Put the foreground image on top of the background with shadow."""
    composited_image = (alpha * fg + (1 - alpha) * bg_with_shadow).astype(np.uint8)
    return composited_image


def save_image(path, image):
    """Save an image after converting from RGBA to BGRA."""
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    cv2.imwrite(path, image)


def create_gradient_bg(image_shape, top_color, bottom_color):
    """Create a background image with a vertical gradient."""
    rows, cols, _ = image_shape
    gradient = np.zeros((rows, cols, 3), dtype=np.uint8)

    for i in range(3):
        gradient[:, :, i] = np.tile(
            np.linspace(top_color[i], bottom_color[i], rows).astype(np.uint8), (cols, 1)
        ).T

    return gradient


def add_vignette(image, exponent=2, scale=0.1):
    """Create a vignette mask using a power law (gamma) kernel."""
    rows, cols = image.shape[:2]
    X = np.linspace(-1, 1, cols)
    Y = np.linspace(-1, 1, rows)
    X, Y = np.meshgrid(X, Y)

    # Calculate the distance from the center
    distance = np.sqrt(X**2 + Y**2)

    # Apply the power law transformation
    mask = np.clip(1 - (distance**exponent) * scale, 0, 1)

    # Normalize the mask to 0-255
    mask = 255 * mask
    mask = mask.astype(np.uint8)
    mask = cv2.merge([mask, mask, mask])
    return cv2.subtract(image, (1 - mask))


def display(image):
    fig, ax = plt.subplots()
    ax.imshow(image)
    ax.axis("off")
    fig.patch.set_visible(False)
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    plt.show()


def prettify(path: str):
    image_without_background = pipe(path)
    padded_image = trim_and_pad_image(image_without_background, PADDING)
    np_image = np.array(padded_image)
    alpha, fg_rgb = extract_alpha_channel(np_image)
    bg = create_gradient_bg(fg_rgb.shape, TOP_COLOR, BOTTOM_COLOR)

    offset_alpha_channel = offset_alpha(alpha, OFFSET_X, OFFSET_Y)
    alpha_blur = apply_blur_to_alpha(offset_alpha_channel, BLUR_AMOUNT)
    alpha_blur_normalized = expand_and_normalize_alpha(alpha_blur)
    bg_with_shadow = create_shadow_on_bg(bg, alpha_blur_normalized, OPACITY)
    alpha_normalized = expand_and_normalize_alpha(alpha)
    image = composite_foreground_on_bg(fg_rgb, alpha_normalized, bg_with_shadow)
    final_image = add_vignette(image, exponent=VIGNETTE_EXPONENT, scale=VIGNETTE_SCALE)
    return final_image
