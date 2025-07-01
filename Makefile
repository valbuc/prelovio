.PHONY: test test-unit test-integration test-webapp test-coverage clean install format lint help

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install dependencies"
	@echo "  test          - Run all tests"
	@echo "  test-unit     - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  test-webapp   - Run webapp tests only"
	@echo "  test-coverage - Run tests with coverage report"
	@echo "  format        - Format code with black"
	@echo "  lint          - Run linting checks"
	@echo "  clean         - Clean up temporary files"
	@echo "  run           - Start the Flask development server"

# Install dependencies
install:
	poetry install

# Run all tests
test:
	poetry run pytest

# Run unit tests only
test-unit:
	poetry run pytest tests/test_image_processing.py tests/test_metadata.py -v

# Run integration tests only
test-integration:
	poetry run pytest tests/test_integration.py -v

# Run webapp tests only
test-webapp:
	poetry run pytest tests/test_webapp.py -v

# Run tests with coverage
test-coverage:
	poetry run pytest --cov=prelovium --cov-report=html --cov-report=term-missing

# Format code
format:
	poetry run black prelovium/ tests/

# Run linting
lint:
	poetry run flake8 prelovium/
	poetry run mypy prelovium/

# Clean temporary files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .coverage htmlcov/ .pytest_cache/
	rm -rf prelovium/webapp/temp/uploads/*

# Start development server
run:
	poetry run python -m prelovium.webapp.app

# Quick test (faster subset for development)
test-quick:
	poetry run pytest tests/test_image_processing.py::TestImageProcessing::test_load_image -v
	poetry run pytest tests/test_webapp.py::TestWebApp::test_index_route -v