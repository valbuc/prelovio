import pytest
import os
import tempfile
import shutil
from PIL import Image
import numpy as np
from prelovium.webapp.app import app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config['TESTING'] = True
    app.config['UPLOAD_FOLDER'] = tempfile.mkdtemp()
    
    with app.test_client() as client:
        with app.app_context():
            yield client
    
    # Cleanup
    if os.path.exists(app.config['UPLOAD_FOLDER']):
        shutil.rmtree(app.config['UPLOAD_FOLDER'])


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    image = Image.new('RGB', (100, 100), color='red')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
    image.save(temp_file.name)
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def sample_rgba_image():
    """Create a sample RGBA test image with alpha channel."""
    # Create a simple RGBA image with transparency
    img_array = np.zeros((100, 100, 4), dtype=np.uint8)
    img_array[:, :, 0] = 255  # Red channel
    img_array[:, :, 3] = 200  # Alpha channel (some transparency)
    
    image = Image.fromarray(img_array, 'RGBA')
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
    image.save(temp_file.name)
    yield temp_file.name
    os.unlink(temp_file.name)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_metadata():
    """Sample metadata for testing."""
    return {
        "title": "Test Fashion Item",
        "description": "A test item for unit testing",
        "price": 25,
        "brand": "TestBrand",
        "brand_domain": "www.testbrand.com",
        "size": "M",
        "colors": ["red", "blue"],
        "materials": ["cotton", "polyester"],
        "categories": ["shirt", "casual"]
    }