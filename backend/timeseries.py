import requests
from datetime import datetime, timedelta
import numpy as np
from PIL import Image
import io
import matplotlib
matplotlib.use('Agg')  # Non-GUI backend
import matplotlib.pyplot as plt
from satellite import get_access_token, SENTINEL_HUB_PROCESS_URL

def fetch_single_day_image(bbox, target_date, token):
    """Fetch image for a specific date"""
    
    # Single-day window
    start = target_date.strftime("%Y-%m-%dT00:00:00Z")
    end = target_date.strftime("%Y-%m-%dT23:59:59Z")
    
    # NDVI-focused evalscript for vegetation
    evalscript = """
    //VERSION=3
    function setup() {
        return {
            input: ["B04", "B08", "B03", "dataMask"],
            output: { bands: 3, sampleType: "AUTO" }
        };
    }
    
    function evaluatePixel(sample) {
        // NDVI = (NIR - Red) / (NIR + Red)
        let ndvi = (sample.B08 - sample.B04) / (sample.B08 + sample.B04 + 0.0001);
        
        // Visualize: green = vegetation, brown = bare
        if (ndvi > 0.4) {
            return [0, 0.8, 0];  // Strong green
        } else if (ndvi > 0.2) {
            return [0.5, 0.7, 0.2];  // Light green
        } else {
            return [0.6, 0.4, 0.2];  // Brown/bare
        }
    }
    """
    
    request_payload = {
        "input": {
            "bounds": {"bbox": bbox},
            "data": [{
                "type": "S2L2A",
                "dataFilter": {
                    "timeRange": {"from": start, "to": end},
                    "maxCloudCoverage": 40
                }
            }]
        },
        "evalscript": evalscript,
        "output": {
            "width": 256,
            "height": 256,
            "responses": [{
                "identifier": "default",
                "format": {"type": "image/png"}
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
                               timeout=30)
        
        if response.status_code == 200:
            return response.content
        return None
    except:
        return None

def calculate_vegetation_percentage(image_bytes):
    """Calculate percentage of green/vegetation pixels"""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img_array = np.array(img)
        
        # Consider pixels as vegetation if green channel is dominant
        green = img_array[:, :, 1]
        red = img_array[:, :, 0]
        
        # Vegetation indicator: green > red + threshold
        vegetation_mask = green > (red + 30)
        vegetation_percentage = (np.sum(vegetation_mask) / vegetation_mask.size) * 100
        
        return round(vegetation_percentage, 2)
    except:
        return None

def analyze_timeseries_data(dates, values):
    """Analyze vegetation trend over time"""
    
    # Filter out None values
    valid_data = [(d, v) for d, v in zip(dates, values) if v is not None]
    
    if len(valid_data) < 3:
        return {
            "status": "insufficient_data",
            "message": "Not enough valid data points for analysis"
        }
    
    dates_valid, values_valid = zip(*valid_data)
    values_array = np.array(values_valid)
    
    # Calculate statistics
    mean_veg = np.mean(values_array)
    std_veg = np.std(values_array)
    min_veg = np.min(values_array)
    max_veg = np.max(values_array)
    
    # Trend analysis (simple linear regression)
    x = np.arange(len(values_array))
    coeffs = np.polyfit(x, values_array, 1)
    trend_slope = coeffs[0]
    
    # Detect anomalies (values beyond 2 std devs)
    anomalies = []
    for i, val in enumerate(values_valid):
        if abs(val - mean_veg) > 2 * std_veg:
            anomalies.append({
                "date": dates_valid[i],
                "value": val,
                "deviation": round(abs(val - mean_veg), 2)
            })
    
    # Overall trend assessment
    if trend_slope > 0.5:
        trend = "increasing"
        health = "improving"
    elif trend_slope < -0.5:
        trend = "decreasing"
        health = "declining"
    else:
        trend = "stable"
        health = "stable"
    
    # Alert level
    if mean_veg < 30:
        alert_level = "critical"
    elif mean_veg < 50:
        alert_level = "warning"
    else:
        alert_level = "healthy"
    
    return {
        "status": "success",
        "statistics": {
            "mean": round(mean_veg, 2),
            "std_dev": round(std_veg, 2),
            "min": round(min_veg, 2),
            "max": round(max_veg, 2),
            "range": round(max_veg - min_veg, 2)
        },
        "trend": {
            "direction": trend,
            "slope": round(trend_slope, 4),
            "health_status": health
        },
        "anomalies": anomalies,
        "alert_level": alert_level,
        "data_points": len(valid_data),
        "missing_days": 30 - len(valid_data)
    }

def generate_vegetation_plot(dates, values, bbox_str):
    """Generate matplotlib plot of vegetation over time"""
    
    # Filter valid data
    valid_data = [(d, v) for d, v in zip(dates, values) if v is not None]
    if len(valid_data) == 0:
        return None
    
    dates_valid, values_valid = zip(*valid_data)
    
    plt.figure(figsize=(12, 6))
    
    # Main plot
    plt.plot(dates_valid, values_valid, marker='o', linewidth=2, 
             markersize=6, color='#2ecc71', label='Vegetation Cover')
    
    # Mean line
    mean_val = np.mean(values_valid)
    plt.axhline(y=mean_val, color='blue', linestyle='--', 
                linewidth=1.5, alpha=0.7, label=f'Mean: {mean_val:.1f}%')
    
    # Trend line
    x_numeric = np.arange(len(values_valid))
    z = np.polyfit(x_numeric, values_valid, 1)
    p = np.poly1d(z)
    plt.plot(dates_valid, p(x_numeric), "r--", alpha=0.5, 
             linewidth=2, label='Trend')
    
    # Styling
    plt.xlabel('Date', fontsize=12, fontweight='bold')
    plt.ylabel('Vegetation Cover (%)', fontsize=12, fontweight='bold')
    plt.title(f'30-Day Vegetation Analysis\nRegion: {bbox_str}', 
              fontsize=14, fontweight='bold')
    plt.legend(loc='best')
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save to bytes
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    return buf.getvalue()
