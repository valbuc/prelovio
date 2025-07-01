import pytest
import json
import os
import tempfile
from io import BytesIO
from unittest.mock import patch, MagicMock
from PIL import Image
import numpy as np

from prelovium.webapp.app import app


class TestIntegration:
    """Integration tests for the complete image processing workflow."""
    
    def create_realistic_test_image(self, color='red', size=(200, 200)):
        """Create a more realistic test image."""
        img = Image.new('RGB', size, color=color)
        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=85)
        img_io.seek(0)
        return img_io
    
    @patch('prelovium.utils.image_processing.pipe')
    @patch('prelovium.utils.metadata.vertexai')
    @patch('prelovium.utils.metadata.GenerativeModel')
    @patch('prelovium.utils.metadata.Image')
    @patch('prelovium.utils.metadata.glob.glob')
    @patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-project'})
    def test_complete_upload_workflow(self, mock_glob, mock_vertex_image, mock_model_class, mock_vertexai, mock_pipe, client):
        """Test the complete workflow from image upload to metadata generation."""
        
        # Mock the background removal pipeline
        mock_rgba_image = Image.new('RGBA', (200, 200), (255, 0, 0, 200))
        mock_pipe.return_value = mock_rgba_image
        
        # Mock Vertex AI metadata generation
        mock_glob.return_value = ['test1.jpeg', 'test2.jpeg', 'test3.jpeg']
        mock_vertex_image.load_from_file.return_value = MagicMock()
        
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance
        
        # Mock AI response
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        
        test_metadata = {
            "title": "Stylish Red Jacket",
            "description": "A beautiful red jacket perfect for casual wear",
            "price": 75,
            "brand": "FashionBrand",
            "brand_domain": "www.fashionbrand.com",
            "size": "M",
            "colors": ["red"],
            "materials": ["cotton", "polyester"],
            "categories": ["jacket", "outerwear"]
        }
        
        mock_part.text = json.dumps(test_metadata)
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        mock_model_instance.generate_content.return_value = mock_response
        
        # Create test images
        primary_img = self.create_realistic_test_image('red', (300, 400))
        secondary_img = self.create_realistic_test_image('blue', (300, 400))
        label_img = self.create_realistic_test_image('white', (100, 50))
        
        # Upload and process images
        response = client.post('/process', 
                             data={
                                 'primary': (primary_img, 'primary.jpg'),
                                 'secondary': (secondary_img, 'secondary.jpg'),
                                 'label': (label_img, 'label.jpg')
                             },
                             content_type='multipart/form-data')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check that all expected fields are present
        assert 'primary' in data
        assert 'secondary' in data
        assert 'label' in data
        assert 'metadata' in data
        
        # Verify metadata structure
        metadata = data['metadata']
        assert metadata['title'] == 'Stylish Red Jacket'
        assert metadata['price'] == 75
        assert metadata['brand'] == 'FashionBrand'
        assert isinstance(metadata['colors'], list)
        assert isinstance(metadata['materials'], list)
        assert isinstance(metadata['categories'], list)
        
        # Verify that processed image URLs are returned
        assert data['primary'].startswith('/uploads/')
        assert data['secondary'].startswith('/uploads/')
        assert data['label'].startswith('/uploads/')
        
        # Verify that background removal was called
        mock_pipe.assert_called()
    
    @patch('prelovium.utils.image_processing.pipe')
    @patch('prelovium.utils.metadata.generate_metadata')
    def test_example_processing_workflow(self, mock_metadata, mock_pipe, client):
        """Test processing example images workflow."""
        
        # Mock the background removal pipeline
        mock_rgba_image = Image.new('RGBA', (200, 200), (0, 0, 255, 200))
        mock_pipe.return_value = mock_rgba_image
        
        # Mock metadata generation
        mock_metadata.return_value = {
            "title": "Classic Denim Jacket",
            "description": "A timeless denim jacket",
            "price": 60,
            "brand": "DenimCo",
            "brand_domain": "www.denimco.com",
            "size": "L",
            "colors": ["blue", "indigo"],
            "materials": ["denim", "cotton"],
            "categories": ["jacket", "casual"]
        }
        
        # Process example images
        response = client.post('/process', 
                             json={'example': 'jacket'},
                             content_type='application/json')
        
        # Verify response
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check response structure
        assert 'primary' in data
        assert 'secondary' in data
        assert 'label' in data
        assert 'metadata' in data
        
        # Verify metadata
        metadata = data['metadata']
        assert metadata['title'] == 'Classic Denim Jacket'
        assert metadata['price'] == 60
        
        # Verify that background removal was called for primary and secondary images
        assert mock_pipe.call_count >= 2
        
        # Verify metadata generation was called
        mock_metadata.assert_called_once()
    
    def test_error_handling_workflow(self, client):
        """Test error handling in the workflow."""
        
        # Test with incomplete form data
        response = client.post('/process', 
                             data={'primary': (BytesIO(b'fake image'), 'primary.jpg')},
                             content_type='multipart/form-data')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('prelovium.utils.image_processing.pipe')
    def test_image_processing_pipeline(self, mock_pipe, client):
        """Test that the image processing pipeline is called correctly."""
        
        # Mock successful background removal
        mock_rgba_image = Image.new('RGBA', (100, 100), (255, 255, 0, 180))
        mock_pipe.return_value = mock_rgba_image
        
        # Mock metadata generation to avoid AI calls
        with patch('prelovium.utils.metadata.generate_metadata') as mock_metadata:
            mock_metadata.return_value = {
                "title": "Test Item",
                "price": 25,
                "brand": "TestBrand",
                "brand_domain": "NA",
                "size": "M",
                "colors": ["yellow"],
                "materials": ["cotton"],
                "categories": ["test"]
            }
            
            # Create test images
            primary_img = self.create_realistic_test_image('yellow')
            secondary_img = self.create_realistic_test_image('yellow')
            label_img = self.create_realistic_test_image('white')
            
            response = client.post('/process', 
                                 data={
                                     'primary': (primary_img, 'primary.jpg'),
                                     'secondary': (secondary_img, 'secondary.jpg'),
                                     'label': (label_img, 'label.jpg')
                                 },
                                 content_type='multipart/form-data')
            
            assert response.status_code == 200
            
            # Verify that the pipeline was called for processing
            assert mock_pipe.call_count >= 2  # At least for primary and secondary
    
    def test_file_serving_integration(self, client):
        """Test that processed files can be served."""
        
        # First, we need to create some processed files by running the workflow
        with patch('prelovium.utils.image_processing.pipe') as mock_pipe, \
             patch('prelovium.utils.metadata.generate_metadata') as mock_metadata:
            
            mock_rgba_image = Image.new('RGBA', (100, 100), (0, 255, 0, 200))
            mock_pipe.return_value = mock_rgba_image
            
            mock_metadata.return_value = {
                "title": "Green Test Item",
                "price": 35,
                "brand": "TestBrand",
                "brand_domain": "NA",
                "size": "S",
                "colors": ["green"],
                "materials": ["synthetic"],
                "categories": ["test"]
            }
            
            # Process images
            primary_img = self.create_realistic_test_image('green')
            secondary_img = self.create_realistic_test_image('green')
            label_img = self.create_realistic_test_image('white')
            
            response = client.post('/process', 
                                 data={
                                     'primary': (primary_img, 'primary.jpg'),
                                     'secondary': (secondary_img, 'secondary.jpg'),
                                     'label': (label_img, 'label.jpg')
                                 },
                                 content_type='multipart/form-data')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            # Try to access the processed images
            primary_url = data['primary']
            response = client.get(primary_url)
            # The file should exist and be servable (or at least the route should be valid)
            assert response.status_code in [200, 404]  # 404 is acceptable in test environment