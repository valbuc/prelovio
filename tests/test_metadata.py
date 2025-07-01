import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
from PIL import Image

from prelovium.utils.metadata import generate_metadata, metadata_to_markdown


class TestMetadata:
    
    @patch('prelovium.utils.metadata.vertexai')
    @patch('prelovium.utils.metadata.GenerativeModel')
    @patch('prelovium.utils.metadata.Image')
    @patch('prelovium.utils.metadata.glob.glob')
    @patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-project'})
    def test_generate_metadata(self, mock_glob, mock_image_class, mock_model_class, mock_vertexai, temp_dir):
        """Test metadata generation with mocked Vertex AI."""
        # Setup mocks
        mock_glob.return_value = [
            os.path.join(temp_dir, 'image1.jpeg'),
            os.path.join(temp_dir, 'image2.png')
        ]
        
        mock_image_instance = MagicMock()
        mock_image_class.load_from_file.return_value = mock_image_instance
        
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance
        
        # Mock response with proper structure
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        
        test_metadata = {
            "title": "Test Jacket",
            "description": "A beautiful test jacket",
            "price": 50,
            "brand": "TestBrand",
            "brand_domain": "www.testbrand.com",
            "size": "L",
            "colors": ["blue", "white"],
            "materials": ["cotton", "polyester"],
            "categories": ["jacket", "outerwear"]
        }
        
        mock_part.text = json.dumps(test_metadata)
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_model_instance.generate_content.return_value = mock_response
        
        # Test the function
        result = generate_metadata(temp_dir)
        
        # Assertions
        assert result == test_metadata
        mock_vertexai.init.assert_called_once_with(project='test-project', location='us-central1')
        mock_model_instance.generate_content.assert_called_once()
    
    def test_generate_metadata_missing_project_id(self, temp_dir):
        """Test that missing GOOGLE_CLOUD_PROJECT raises ValueError."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="GOOGLE_CLOUD_PROJECT environment variable is not set"):
                generate_metadata(temp_dir)
    
    @patch('prelovium.utils.metadata.vertexai')
    @patch('prelovium.utils.metadata.GenerativeModel')
    @patch('prelovium.utils.metadata.Image')
    @patch('prelovium.utils.metadata.glob.glob')
    @patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-project'})
    def test_generate_metadata_with_markdown_response(self, mock_glob, mock_image_class, mock_model_class, mock_vertexai, temp_dir):
        """Test metadata generation with markdown-formatted response."""
        # Setup mocks
        mock_glob.return_value = [os.path.join(temp_dir, 'image1.jpeg')]
        mock_image_instance = MagicMock()
        mock_image_class.load_from_file.return_value = mock_image_instance
        
        mock_model_instance = MagicMock()
        mock_model_class.return_value = mock_model_instance
        
        # Mock response with markdown formatting
        mock_response = MagicMock()
        mock_candidate = MagicMock()
        mock_content = MagicMock()
        mock_part = MagicMock()
        
        test_metadata = {"title": "Test Item", "price": 30}
        markdown_response = f"```json\n{json.dumps(test_metadata)}\n```"
        
        mock_part.text = markdown_response
        mock_content.parts = [mock_part]
        mock_candidate.content = mock_content
        mock_response.candidates = [mock_candidate]
        
        mock_model_instance.generate_content.return_value = mock_response
        
        # Test the function
        result = generate_metadata(temp_dir)
        
        # Assertions
        assert result == test_metadata
    
    def test_metadata_to_markdown(self, mock_metadata):
        """Test converting metadata to markdown format."""
        markdown = metadata_to_markdown(mock_metadata)
        
        assert "## Test Fashion Item" in markdown
        assert "#### Price: 25" in markdown
        assert "Size: M" in markdown
        assert "Colors: red, blue" in markdown
        assert "Materials: cotton, polyester" in markdown
        assert "Categories: shirt, casual" in markdown
        assert "[TestBrand](https://www.testbrand.com)" in markdown
        assert "A test item for unit testing" in markdown
    
    def test_metadata_to_markdown_no_brand_domain(self):
        """Test markdown generation when brand domain is NA."""
        metadata = {
            "title": "Test Item",
            "price": 30,
            "size": "S",
            "colors": ["black"],
            "materials": ["leather"],
            "categories": ["shoes"],
            "brand": "UnknownBrand",
            "brand_domain": "NA",
            "description": "Test description"
        }
        
        markdown = metadata_to_markdown(metadata)
        
        assert "Brand: UnknownBrand" in markdown
        assert "www." not in markdown  # Should not contain URL formatting