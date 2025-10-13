from pathlib import Path
import requests
import os

# Define MODEL_PATH
MODEL_PATH = Path(__file__).parent / "deforestation_complete_model.h5"

# Your Dropbox direct download link (with ?dl=1)
DROPBOX_URL = "https://www.dropbox.com/scl/fi/ukpsz9yg383hsr6lmxvvv/deforestation_complete_model.h5?rlkey=1ijz3mgmm94dkhyadvkq01au3&st=90dzddyi&dl=1"  # Replace with your actual link

def download_model():
    """Download model from Dropbox if not present"""
    
    if MODEL_PATH.exists():
        file_size = MODEL_PATH.stat().st_size
        
        if file_size > 100_000_000:  # 100MB
            print(f"✅ Model found: {MODEL_PATH}")
            print(f"   Size: {file_size / (1024*1024):.1f} MB")
            return True
        else:
            print(f"⚠️ Model too small, re-downloading...")
            MODEL_PATH.unlink()
    
    print("📥 Downloading model from Dropbox...")
    
    try:
        response = requests.get(DROPBOX_URL, stream=True, timeout=300)
        
        if response.status_code == 200:
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(MODEL_PATH, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"Progress: {progress:.1f}%", end='\r')
            
            file_size = MODEL_PATH.stat().st_size
            print(f"\n✅ Model downloaded: {file_size / (1024*1024):.1f} MB")
            return True
        else:
            print(f"❌ Download failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        return False

if __name__ == "__main__":
    download_model()
