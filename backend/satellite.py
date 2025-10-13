import requests
from datetime import datetime, timedelta
import os

# Sentinel Hub configuration
SENTINEL_HUB_OAUTH_URL = "https://services.sentinel-hub.com/oauth/token"
SENTINEL_HUB_PROCESS_URL = "https://services.sentinel-hub.com/api/v1/process"

# Replace with your Sentinel Hub credentials
CLIENT_ID = "1b2af6a9-500f-4e38-8714-c8a078774f58"

CLIENT_SECRET = "OLGv2EVGy32T0EW3PwNbe55huOY9a3ia"
def get_access_token():
    """Get OAuth token for Sentinel Hub API"""
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    try:
        response = requests.post(SENTINEL_HUB_OAUTH_URL, data=data, timeout=30)
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"Error getting access token: {e}")
        return None

def get_access_token():
    print(f"Using Client ID: {CLIENT_ID[:8]}...")  # Show first 8 chars only
    print(f"Using Client Secret: {CLIENT_SECRET[:8]}...")
    
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    try:
        response = requests.post(SENTINEL_HUB_OAUTH_URL, data=data, timeout=30)
        print(f"Auth response status: {response.status_code}")
        response.raise_for_status()
        token = response.json()['access_token']
        print("✅ Access token obtained successfully")
        return token
    except Exception as e:
        print(f"❌ Auth error: {e}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
        return None


def fetch_sentinel2_image(bbox, days_back=7):
    """
    Fetch latest Sentinel-2 image for deforestation detection
    bbox: [min_lon, min_lat, max_lon, max_lat]
    """
    token = get_access_token()
    if not token:
        return None
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)
    
    # Evalscript for RGB + NIR bands (good for vegetation analysis)
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: ["B04", "B03", "B02", "B08", "dataMask"],
            output: { 
                bands: 3,
                sampleType: "AUTO"
            }
        };
    }
    
    function evaluatePixel(sample) {
        // Enhanced vegetation visualization
        // Use NIR for better forest detection
        let gain = 2.5;
        return [
            gain * sample.B04,  // Red
            gain * sample.B03,  // Green  
            gain * sample.B02   // Blue
        ];
    }
    """

    request_payload = {
        "input": {
            "bounds": {
                "bbox": bbox
            },
            "data": [{
                "type": "S2L2A",
                "dataFilter": {
                    "timeRange": {
                        "from": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "to": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                    },
                    "maxCloudCoverage": 30
                }
            }]
        },
        "evalscript": evalscript,
        "output": {
            "width": 512,
            "height": 512,
            "responses": [{
                "identifier": "default",
                "format": {
                    "type": "image/png"
                }
            }]
        }
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(SENTINEL_HUB_PROCESS_URL, 
                               json=request_payload, 
                               headers=headers,
                               timeout=60)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Error fetching satellite image: {e}")
        return None

# Test coordinates (Amazon rainforest area)
def get_test_coordinates():
    """Returns test coordinates for Amazon deforestation monitoring"""
    return [-60.0292, -3.4653, -59.8292, -3.2653]  # Manaus area
