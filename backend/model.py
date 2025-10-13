import tensorflow as tf
import numpy as np
import cv2
import os

# UPDATE THIS PATH - Change from old path to your new path
#MODEL_PATH = r"C:\Users\HP\Downloads\deforestation_complete_model.h5"

from download_model import download_model, MODEL_PATH

# Download model if needed
download_model()
class DeforestationDetector:
    def __init__(self):
        self.model = self.load_model()
        
    def load_model(self):
        """Load the complete BioWar deforestation model"""
        try:
            model = tf.keras.models.load_model(MODEL_PATH)
            print(f"✅ Complete model loaded from {MODEL_PATH}")
            return model
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return None
    
    def preprocess_for_model(self, image_np):
        """Preprocess image for BioWar model"""
        # Resize to 512x512
        image_resized = cv2.resize(image_np, (512, 512))
        
        # Normalize to [0, 1]
        if image_resized.max() > 1.0:
            image_resized = image_resized.astype(np.float32) / 255.0
        
        # Add batch dimension
        image_batch = np.expand_dims(image_resized, axis=0)
        
        return image_batch
    
    def detect_deforestation(self, image_np):
        """Detect deforestation using BioWar model"""
        if self.model is None:
            return 0.0, None
            
        # Preprocess image
        processed_image = self.preprocess_for_model(image_np)
        
        # Run prediction
        prediction = self.model.predict(processed_image, verbose=0)
        
        # Extract prediction mask
        pred_mask = prediction[0]  # Shape: (512, 512, 3)
        
        # BioWar class mapping: 0=Forest, 1=Deforestation, 2=Other
        deforestation_mask = pred_mask[:, :, 0]  # Deforestation class
        
        # Calculate deforestation confidence
        deforestation_pixels = np.sum(deforestation_mask > 0.5)
        total_pixels = deforestation_mask.size
        confidence = deforestation_pixels / total_pixels
        
        return float(confidence), pred_mask
    
    def visualize_prediction(self, prediction):
        """Create BioWar visualization: RED=Deforestation, GREEN=Forest"""
        if prediction is None:
            return None
            
        visual = np.zeros_like(prediction)
        
        # BioWar color mapping
        prediction_class1 = np.copy(prediction[..., 0])  # Forest
        prediction_class2 = np.copy(prediction[..., 1])  # Deforestation
        prediction_class3 = np.copy(prediction[..., 2])  # Other
        
        visual[..., 0] = prediction_class2  # RED - Deforestation
        visual[..., 1] = prediction_class1  # GREEN - Forest
        visual[..., 2] = prediction_class3  # BLUE - Other
        
        return visual

# Global model instance
detector = DeforestationDetector()
