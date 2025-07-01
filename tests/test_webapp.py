import pytest
import json
import os
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock
from PIL import Image

from prelovium.webapp.app import app, allowed_file


class TestWebApp:
    
    def test_index_route(self, client):
        """Test the main index route."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'jacket' in response.data  # Should contain example items
    
    def test_allowed_file(self):
        """Test file extension validation."""
        assert allowed_file('test.jpg') == True
        assert allowed_file('test.jpeg') == True
        assert allowed_file('test.png') == True
        assert allowed_file('test.gif') == False
        assert allowed_file('test.txt') == False
        assert allowed_file('test') == False
    
    def test_example_image_valid(self, client):
        """Test serving example images."""
        response = client.get('/examples/jacket/primary')
        assert response.status_code == 200
        assert response.content_type.startswith('image/')
    
    def test_example_image_invalid_item(self, client):
        """Test serving example images with invalid item type."""
        response = client.get('/examples/invalid_item/primary')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_example_image_invalid_type(self, client):
        """Test serving example images with invalid image type."""
        response = client.get('/examples/jacket/invalid_type')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('prelovium.webapp.app.prettify')
    @patch('prelovium.webapp.app.load_image')
    @patch('prelovium.webapp.app.save_image')
    @patch('prelovium.webapp.app.generate_metadata')
    def test_process_example_request(self, mock_metadata, mock_save, mock_load, mock_prettify, client):
        """Test processing example images."""
        # Setup mocks
        mock_prettify.return_value = "processed_image"
        mock_load.return_value = "label_image"
        mock_metadata.return_value = {
            "title": "Test Jacket",
            "price": 50,
            "brand": "TestBrand"
        }
        
        response = client.post('/process', 
                             json={'example': 'jacket'},
                             content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'primary' in data
        assert 'secondary' in data
        assert 'label' in data
        assert 'metadata' in data
        assert data['metadata']['title'] == 'Test Jacket'
    
    def test_process_invalid_example(self, client):
        """Test processing with invalid example."""
        response = client.post('/process', 
                             json={'example': 'invalid_item'},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_process_missing_example(self, client):
        """Test processing with missing example key."""
        response = client.post('/process', 
                             json={'not_example': 'jacket'},
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    def create_test_image(self):
        """Helper to create a test image file."""
        img = Image.new('RGB', (100, 100), color='red')
        img_io = BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        return img_io
    
    @patch('prelovium.webapp.app.prettify')
    @patch('prelovium.webapp.app.load_image')
    @patch('prelovium.webapp.app.save_image')
    @patch('prelovium.webapp.app.generate_metadata')
    def test_process_file_upload(self, mock_metadata, mock_save, mock_load, mock_prettify, client):
        """Test processing uploaded files."""
        # Setup mocks
        mock_prettify.return_value = "processed_image"
        mock_load.return_value = "label_image"
        mock_metadata.return_value = {
            "title": "Uploaded Item",
            "price": 30
        }
        
        # Create test files
        primary_img = self.create_test_image()
        secondary_img = self.create_test_image()
        label_img = self.create_test_image()
        
        response = client.post('/process', 
                             data={
                                 'primary': (primary_img, 'primary.jpg'),
                                 'secondary': (secondary_img, 'secondary.jpg'),
                                 'label': (label_img, 'label.jpg')
                             },
                             content_type='multipart/form-data')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'primary' in data
        assert 'secondary' in data
        assert 'label' in data
        assert 'metadata' in data
    
    def test_process_missing_files(self, client):
        """Test processing with missing files."""
        primary_img = self.create_test_image()
        
        response = client.post('/process', 
                             data={'primary': (primary_img, 'primary.jpg')},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Missing required images' in data['error']
    
    def test_process_empty_filenames(self, client):
        """Test processing with empty filenames."""
        response = client.post('/process', 
                             data={
                                 'primary': (BytesIO(), ''),
                                 'secondary': (BytesIO(), ''),
                                 'label': (BytesIO(), '')
                             },
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'No selected files' in data['error']
    
    def test_process_invalid_file_types(self, client):
        """Test processing with invalid file types."""
        # Create text file instead of image
        text_file = BytesIO(b'not an image')
        
        response = client.post('/process', 
                             data={
                                 'primary': (text_file, 'primary.txt'),
                                 'secondary': (text_file, 'secondary.txt'),
                                 'label': (text_file, 'label.txt')
                             },
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Invalid file type' in data['error']
    
    def test_uploaded_file_route(self, client):
        """Test serving uploaded files."""
        # This test would need a real uploaded file, so we'll test the route existence
        response = client.get('/uploads/nonexistent/file.jpg')
        # The route should exist but file won't be found (404 or handled by Flask)
        assert response.status_code in [404, 500]  # Expected for non-existent file


class TestFlaskConfig:
    
    def test_app_config(self):
        """Test Flask app configuration."""
        assert app.config['MAX_CONTENT_LENGTH'] == 16 * 1024 * 1024
        assert 'temp' in app.config['UPLOAD_FOLDER']


class TestConstants:
    
    def test_examples_list(self):
        """Test that examples list contains expected items."""
        from prelovium.webapp.app import EXAMPLES
        
        expected_items = ["jacket", "shirt", "jeans", "shoes", "boots", "pants", "suit", "jumper"]
        assert all(item in EXAMPLES for item in expected_items)
    
    def test_allowed_extensions(self):
        """Test allowed file extensions."""
        from prelovium.webapp.app import ALLOWED_EXTENSIONS
        
        expected_extensions = {"png", "jpg", "jpeg"}
        assert ALLOWED_EXTENSIONS == expected_extensions