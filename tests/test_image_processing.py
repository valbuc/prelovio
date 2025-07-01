import pytest
import numpy as np
import cv2
from PIL import Image
import tempfile
import os
from unittest.mock import patch, MagicMock

from prelovium.utils.image_processing import (
    load_image,
    extract_alpha_channel,
    apply_blur_to_alpha,
    expand_and_normalize_alpha,
    offset_alpha,
    create_shadow_on_bg,
    composite_foreground_on_bg,
    save_image,
    create_gradient_bg,
    add_vignette,
    trim_and_pad_image,
    remove_background,
    prettify
)


class TestImageProcessing:
    
    def test_load_image(self, sample_image):
        """Test loading an image."""
        image = load_image(sample_image)
        assert image is not None
        assert isinstance(image, np.ndarray)
        assert len(image.shape) == 3  # Height, Width, Channels
    
    def test_load_image_with_color_conversion(self, sample_image):
        """Test loading an image with color conversion."""
        image = load_image(sample_image, cv2.COLOR_BGR2RGB)
        assert image is not None
        assert isinstance(image, np.ndarray)
    
    def test_extract_alpha_channel(self):
        """Test extracting alpha channel from RGBA image."""
        # Create test RGBA image
        rgba_image = np.zeros((10, 10, 4), dtype=np.uint8)
        rgba_image[:, :, 3] = 255  # Full alpha
        
        alpha, rgb = extract_alpha_channel(rgba_image)
        
        assert alpha.shape == (10, 10)
        assert rgb.shape == (10, 10, 3)
        assert np.all(alpha == 255)
    
    def test_apply_blur_to_alpha(self):
        """Test applying blur to alpha channel."""
        alpha = np.ones((50, 50), dtype=np.uint8) * 255
        blurred = apply_blur_to_alpha(alpha, 5)
        
        assert blurred.shape == alpha.shape
        assert isinstance(blurred, np.ndarray)
    
    def test_expand_and_normalize_alpha(self):
        """Test expanding and normalizing alpha channel."""
        alpha = np.ones((10, 10), dtype=np.uint8) * 128
        normalized = expand_and_normalize_alpha(alpha)
        
        assert normalized.shape == (10, 10, 3)
        assert np.allclose(normalized, 128/255)
    
    def test_offset_alpha(self):
        """Test offsetting alpha channel."""
        alpha = np.zeros((50, 50), dtype=np.uint8)
        alpha[20:30, 20:30] = 255  # White square
        
        offset = offset_alpha(alpha, 5, -5)
        
        assert offset.shape == alpha.shape
        assert isinstance(offset, np.ndarray)
    
    def test_create_shadow_on_bg(self):
        """Test creating shadow on background."""
        bg = np.ones((50, 50, 3), dtype=np.uint8) * 128
        alpha_blur = np.ones((50, 50, 3)) * 0.5
        
        shadowed_bg = create_shadow_on_bg(bg, alpha_blur, opacity=0.3)
        
        assert shadowed_bg.shape == bg.shape
        assert shadowed_bg.dtype == np.uint8
    
    def test_composite_foreground_on_bg(self):
        """Test compositing foreground on background."""
        fg = np.ones((50, 50, 3), dtype=np.uint8) * 255
        alpha = np.ones((50, 50, 3)) * 0.8
        bg = np.ones((50, 50, 3), dtype=np.uint8) * 100
        
        composite = composite_foreground_on_bg(fg, alpha, bg)
        
        assert composite.shape == fg.shape
        assert composite.dtype == np.uint8
    
    def test_save_image(self, temp_dir):
        """Test saving an image."""
        image = np.ones((50, 50, 3), dtype=np.uint8) * 128
        save_path = os.path.join(temp_dir, "test_save.jpg")
        
        save_image(save_path, image)
        
        assert os.path.exists(save_path)
        loaded = cv2.imread(save_path)
        assert loaded is not None
    
    def test_create_gradient_bg(self):
        """Test creating gradient background."""
        image_shape = (100, 100, 3)
        top_color = [255, 255, 255]
        bottom_color = [100, 100, 100]
        
        gradient = create_gradient_bg(image_shape, top_color, bottom_color)
        
        assert gradient.shape == image_shape
        assert gradient.dtype == np.uint8
        # Check that top and bottom rows are different
        assert not np.array_equal(gradient[0, :], gradient[-1, :])
    
    def test_add_vignette(self):
        """Test adding vignette effect."""
        image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        vignetted = add_vignette(image, exponent=2, scale=0.1)
        
        assert vignetted.shape == image.shape
        assert vignetted.dtype == np.uint8
    
    def test_trim_and_pad_image(self, sample_rgba_image):
        """Test trimming and padding image."""
        image = Image.open(sample_rgba_image)
        
        padded = trim_and_pad_image(image, padding_ratio=0.1)
        
        assert isinstance(padded, Image.Image)
        assert padded.mode == 'RGBA'
    
    @patch('prelovium.utils.image_processing.pipe')
    def test_remove_background(self, mock_pipe, sample_image):
        """Test background removal with mocked pipeline."""
        mock_result = Image.new('RGBA', (100, 100), (255, 0, 0, 255))
        mock_pipe.return_value = mock_result
        
        result = remove_background(sample_image)
        
        mock_pipe.assert_called_once_with(sample_image)
        assert isinstance(result, Image.Image)
    
    @patch('prelovium.utils.image_processing.pipe')
    def test_prettify(self, mock_pipe, sample_image):
        """Test prettify function with mocked pipeline."""
        # Create a mock RGBA image
        mock_rgba = Image.new('RGBA', (100, 100), (255, 0, 0, 200))
        mock_pipe.return_value = mock_rgba
        
        result = prettify(sample_image)
        
        mock_pipe.assert_called_once_with(sample_image)
        assert isinstance(result, np.ndarray)
        assert len(result.shape) == 3
        assert result.shape[2] == 3  # RGB channels