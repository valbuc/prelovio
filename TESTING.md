# Prelovium Testing Guide

This document provides comprehensive information about testing the Prelovium application - a Flask web application for processing fashion images with ML-based background removal and metadata generation.

## Testing Overview

The testing framework includes:

- **Unit Tests**: Test individual functions and components
- **Integration Tests**: Test complete workflows from image upload to metadata generation  
- **Web App Tests**: Test Flask routes, file uploads, and API endpoints
- **Mocked External Dependencies**: AI models and cloud services are mocked for reliable testing

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_image_processing.py # Unit tests for image processing utilities
├── test_metadata.py         # Unit tests for metadata generation
├── test_webapp.py          # Flask web application tests
└── test_integration.py     # End-to-end integration tests
```

## Prerequisites

Install testing dependencies:

```bash
# Using Poetry (recommended)
poetry install

# Or using pip in a virtual environment
python3 -m venv venv
source venv/bin/activate
pip install pytest pytest-flask pytest-cov pytest-mock pillow numpy opencv-python flask transformers
```

## Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration  
make test-webapp

# Run with coverage report
make test-coverage
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_image_processing.py -v

# Run specific test class
pytest tests/test_webapp.py::TestWebApp -v

# Run specific test method
pytest tests/test_image_processing.py::TestImageProcessing::test_load_image -v

# Run with coverage
pytest --cov=prelovium --cov-report=html
```

## Test Categories

### 1. Image Processing Tests (`test_image_processing.py`)

Tests the core image processing functionality:

- **Image loading and color conversion**
- **Alpha channel extraction and manipulation**
- **Background removal (mocked)**
- **Image effects**: blur, shadows, gradients, vignetting
- **Image saving and format conversion**

Example test:
```python
def test_load_image(self, sample_image):
    """Test loading an image."""
    image = load_image(sample_image)
    assert image is not None
    assert isinstance(image, np.ndarray)
    assert len(image.shape) == 3  # Height, Width, Channels
```

### 2. Metadata Generation Tests (`test_metadata.py`)

Tests the AI-powered metadata generation:

- **Vertex AI integration (mocked)**
- **JSON response parsing**  
- **Markdown formatting**
- **Error handling for missing credentials**

Example test:
```python
@patch('prelovium.utils.metadata.vertexai')
@patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-project'})
def test_generate_metadata(self, mock_vertexai, temp_dir):
    """Test metadata generation with mocked Vertex AI."""
    # Test implementation with mocked AI responses
```

### 3. Web Application Tests (`test_webapp.py`)

Tests the Flask web application:

- **Route handling** (index, examples, uploads)
- **File upload validation**
- **JSON API responses**
- **Error handling**
- **Configuration validation**

Example test:
```python
def test_process_file_upload(self, mock_metadata, mock_save, mock_load, mock_prettify, client):
    """Test processing uploaded files."""
    # Create test images and verify complete upload workflow
```

### 4. Integration Tests (`test_integration.py`)

Tests complete end-to-end workflows:

- **Full image upload to processing pipeline**
- **Example image processing workflow** 
- **Error handling in complete workflows**
- **File serving integration**

Example test:
```python
def test_complete_upload_workflow(self, mock_pipe, mock_vertexai, client):
    """Test the complete workflow from image upload to metadata generation."""
    # Tests the entire pipeline with mocked external dependencies
```

## Test Fixtures (`conftest.py`)

Reusable test components:

- **`client`**: Flask test client for web app testing
- **`sample_image`**: Test RGB image file
- **`sample_rgba_image`**: Test RGBA image with transparency
- **`temp_dir`**: Temporary directory for file operations
- **`mock_metadata`**: Sample metadata for testing

## Mocking Strategy

External dependencies are mocked for reliable testing:

### AI/ML Models
- **Background removal**: `@patch('prelovium.utils.image_processing.pipe')`
- **Vertex AI**: `@patch('prelovium.utils.metadata.vertexai')`
- **Image generation**: Mock PIL Images with realistic properties

### File System
- **Temporary files**: Using Python's `tempfile` module
- **Upload directories**: Isolated test directories

### Environment Variables
- **Google Cloud**: `@patch.dict(os.environ, {'GOOGLE_CLOUD_PROJECT': 'test-project'})`

## Coverage Goals

The test suite aims for:
- **80%+ code coverage** (configured in `pytest.ini`)
- **All critical paths tested**
- **Error conditions covered**
- **External dependencies mocked**

## Test Execution Examples

### Running Individual Components

```bash
# Test image processing only
pytest tests/test_image_processing.py::TestImageProcessing::test_prettify -v

# Test web app routes only  
pytest tests/test_webapp.py::TestWebApp::test_process_example_request -v

# Test metadata generation only
pytest tests/test_metadata.py::TestMetadata::test_metadata_to_markdown -v
```

### Development Workflow

```bash
# Quick test during development
make test-quick

# Full test suite with coverage
make test-coverage

# Format code before testing
make format

# Run linting
make lint
```

## Expected Test Results

With properly mocked dependencies, you should see:

```
======================== test session starts ========================
collected 25 items

tests/test_image_processing.py::TestImageProcessing::test_load_image PASSED
tests/test_image_processing.py::TestImageProcessing::test_prettify PASSED
tests/test_webapp.py::TestWebApp::test_index_route PASSED  
tests/test_webapp.py::TestWebApp::test_process_file_upload PASSED
tests/test_metadata.py::TestMetadata::test_generate_metadata PASSED
tests/test_integration.py::TestIntegration::test_complete_upload_workflow PASSED

======================== 25 passed in 2.45s ========================
```

## Troubleshooting

### Common Issues

1. **Missing Dependencies**
   ```bash
   # Install all required packages
   pip install -r requirements.txt  # or poetry install
   ```

2. **Import Errors**
   ```bash
   # Ensure PYTHONPATH includes project root
   export PYTHONPATH=/path/to/prelovium:$PYTHONPATH
   ```

3. **Mock Failures**
   - Verify mock patches match actual import paths
   - Check that mocked objects have required attributes

4. **File Permission Issues**
   ```bash
   # Clean up test artifacts
   make clean
   ```

## Continuous Integration

For CI/CD pipelines, use:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest tests/ --cov=prelovium --cov-fail-under=80
```

## Best Practices

1. **Always mock external dependencies** (AI models, cloud services)
2. **Use realistic test data** (proper image formats, valid metadata)
3. **Test error conditions** (invalid files, missing parameters)
4. **Keep tests isolated** (no shared state between tests)
5. **Clean up resources** (temporary files, test directories)

## Test Data

The testing framework includes:
- **Example fashion items**: jacket, shirt, jeans, shoes, boots, pants, suit, jumper
- **Mock AI responses**: Realistic fashion metadata
- **Test images**: Various formats and sizes for comprehensive testing

## Performance Considerations

- **Mocked ML models** prevent slow inference during testing
- **Small test images** (100x100 pixels) for fast execution
- **Parallel test execution** possible with pytest-xdist

This comprehensive testing framework ensures the Prelovium application works reliably across all components and use cases.