import cv2
import numpy as np
from PIL import Image
import io

def preprocess_satellite_image(image_bytes):
    """
    Preprocess satellite image for deforestation detection
    Input: PNG/JPEG image bytes from satellite API
    Output: RGB numpy array ready for model
    """
    try:
        # Convert bytes to PIL Image
        image_pil = Image.open(io.BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if image_pil.mode != 'RGB':
            image_pil = image_pil.convert('RGB')
        
        # Convert to numpy array
        image_np = np.array(image_pil)
        
        # Ensure values are in [0, 255] range
        if image_np.max() <= 1.0:
            image_np = (image_np * 255).astype(np.uint8)
        
        return image_np
        
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None

def enhance_image_for_detection(image_np):
    """
    Optional: Enhance image for better detection
    """
    # Apply slight contrast enhancement
    enhanced = cv2.convertScaleAbs(image_np, alpha=1.1, beta=10)
    
    # Optional: Apply denoising
    denoised = cv2.fastNlMeansDenoisingColored(enhanced, None, 10, 10, 7, 21)
    
    return denoised
