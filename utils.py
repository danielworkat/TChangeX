import os
import logging
from typing import Tuple, Optional
from PIL import Image, ImageFile
from pathlib import Path

# Configure logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enable partial image loading for corrupted files
ImageFile.LOAD_TRUNCATED_IMAGES = True

def resize_image(
    input_path: str,
    output_path: str,
    size: Tuple[int, int] = (300, 300),
    quality: int = 85,
    format: str = "JPEG",
    optimize: bool = True,
    preserve_metadata: bool = False
) -> bool:
    """
    Resize image while maintaining aspect ratio with enhanced features
    
    Args:
        input_path: Path to input image file
        output_path: Path to save resized image
        size: Maximum (width, height) dimensions
        quality: Output quality (1-100)
        format: Output format ('JPEG', 'PNG', etc.)
        optimize: Whether to optimize the output image
        preserve_metadata: Whether to keep EXIF metadata
    
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        ValueError: If input parameters are invalid
    """
    # Parameter validation
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")

    if quality < 1 or quality > 100:
        raise ValueError("Quality must be between 1 and 100")

    try:
        # Create output directory if doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Open and process image
        with Image.open(input_path) as img:
            # Preserve original mode (RGB, RGBA, etc.)
            original_mode = img.mode
            
            # Convert to RGB if format requires it
            if format.upper() == "JPEG" and original_mode != "RGB":
                img = img.convert("RGB")

            # Calculate thumbnail size maintaining aspect ratio
            img.thumbnail(size, Image.Resampling.LANCZOS)

            # Prepare save parameters
            save_params = {
                'format': format,
                'quality': quality,
                'optimize': optimize
            }

            # Preserve EXIF metadata if requested
            if preserve_metadata and hasattr(img, 'info'):
                exif = img.info.get('exif')
                if exif:
                    save_params['exif'] = exif

            # Save the processed image
            img.save(output_path, **save_params)
            logger.info(f"Successfully resized image: {input_path} -> {output_path}")
            return True

    except Exception as e:
        logger.error(f"Failed to resize image {input_path}: {str(e)}")
        # Clean up if output file was partially created
        if os.path.exists(output_path):
            os.remove(output_path)
        return False

def is_valid_image(file_path: str) -> bool:
    """
    Check if a file is a valid image
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        bool: True if valid image, False otherwise
    """
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception as e:
        logger.warning(f"Invalid image file {file_path}: {str(e)}")
        return False

def convert_image_format(
    input_path: str,
    output_path: str,
    output_format: str = "WEBP",
    quality: int = 80
) -> Optional[str]:
    """
    Convert image to different format
    
    Args:
        input_path: Path to input image
        output_path: Path to save converted image
        output_format: Target format ('WEBP', 'PNG', etc.)
        quality: Output quality (1-100)
        
    Returns:
        str: Path to converted file if successful, None otherwise
    """
    try:
        if resize_image(
            input_path=input_path,
            output_path=output_path,
            size=(99999, 99999),  # Effectively no resizing
            quality=quality,
            format=output_format
        ):
            return output_path
        return None
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        return None
