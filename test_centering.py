#!/usr/bin/env python3
"""Test script to verify image centering fix"""

import os
import sys
import numpy as np
from PIL import Image

# Add the project root to Python path
sys.path.insert(0, '/workspace/prelovium')

from prelovium.utils.image_processing import prettify, trim_and_pad_image, remove_background

def test_image_centering():
    """Test that images are properly centered after processing"""
    
    # Test with a few example images
    test_images = [
        "/workspace/prelovium/prelovium/webapp/examples/shoes/primary.jpeg",
        "/workspace/prelovium/prelovium/webapp/examples/jacket/primary.jpeg",
        "/workspace/prelovium/prelovium/webapp/examples/boots/primary.jpeg"
    ]
    
    print("Testing image centering...")
    
    for i, image_path in enumerate(test_images):
        if not os.path.exists(image_path):
            print(f"Warning: {image_path} not found, skipping...")
            continue
            
        print(f"\nProcessing image {i+1}: {os.path.basename(image_path)}")
        
        try:
            # Remove background and trim/pad
            image_without_bg = remove_background(image_path)
            padded_image = trim_and_pad_image(image_without_bg, 0.1)
            
            # Check the bounding box of the final image
            bbox = padded_image.getbbox()
            if bbox:
                left, top, right, bottom = bbox
                image_width, image_height = padded_image.size
                
                # Calculate center positions
                object_center_x = (left + right) / 2
                object_center_y = (top + bottom) / 2
                image_center_x = image_width / 2
                image_center_y = image_height / 2
                
                # Calculate offset from center
                offset_x = abs(object_center_x - image_center_x)
                offset_y = abs(object_center_y - image_center_y)
                
                # Calculate offset as percentage of image size
                offset_x_pct = (offset_x / image_width) * 100
                offset_y_pct = (offset_y / image_height) * 100
                
                print(f"  Image size: {image_width}x{image_height}")
                print(f"  Object center: ({object_center_x:.1f}, {object_center_y:.1f})")
                print(f"  Image center: ({image_center_x:.1f}, {image_center_y:.1f})")
                print(f"  Offset: ({offset_x:.1f}, {offset_y:.1f}) pixels")
                print(f"  Offset percentage: ({offset_x_pct:.2f}%, {offset_y_pct:.2f}%)")
                
                # Check if centering is good (less than 5% offset)
                if offset_x_pct < 5 and offset_y_pct < 5:
                    print("  ✓ Image is well-centered")
                else:
                    print("  ✗ Image may be off-center")
            else:
                print("  Warning: No bounding box found")
                
        except Exception as e:
            print(f"  Error processing image: {e}")
    
    print("\nCentering test completed!")

if __name__ == "__main__":
    test_image_centering()