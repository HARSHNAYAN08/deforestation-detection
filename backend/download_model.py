from pathlib import Path
import os

# Define MODEL_PATH
MODEL_PATH = Path(__file__).parent / "deforestation_complete_model.h5"

def download_model():
    """
    Check if model exists locally.
    Does NOT auto-download - model must be present manually.
    """
    
    if MODEL_PATH.exists():
        file_size = MODEL_PATH.stat().st_size
        
        # Check if file is valid (> 100MB)
        if file_size > 100_000_000:
            print(f"✅ Model found: {MODEL_PATH}")
            print(f"   Size: {file_size / (1024*1024):.1f} MB")
            return True
        else:
            print(f"⚠️ Model file too small: {file_size / 1024:.1f} KB")
            print(f"   Expected: ~300 MB")
            return False
    else:
        print(f"⚠️ Model not found: {MODEL_PATH}")
        print(f"   Please ensure model file is uploaded to: {MODEL_PATH.parent}")
        return False

# For testing
if __name__ == "__main__":
    result = download_model()
    if result:
        print("\n✅ Model check passed!")
    else:
        print("\n❌ Model check failed - model file missing or invalid")
