from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from fastapi.responses import Response
from timeseries import (
    fetch_single_day_image, 
    calculate_vegetation_percentage,
    analyze_timeseries_data,
    generate_vegetation_plot
)
from satellite import get_access_token

from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import sys
from datetime import datetime, timedelta  # ← ADD THIS LINE

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from satellite import fetch_sentinel2_image, get_test_coordinates, get_access_token
from preprocess import preprocess_satellite_image, enhance_image_for_detection
from model import detector
from alert import log_deforestation_alert, get_recent_alerts
from timeseries import (
    fetch_single_day_image, 
    calculate_vegetation_percentage,
    analyze_timeseries_data,
    generate_vegetation_plot
)
from datetime import datetime, timedelta
import numpy as np



# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from satellite import fetch_sentinel2_image, get_test_coordinates
from preprocess import preprocess_satellite_image, enhance_image_for_detection
from model import detector
from alert import log_deforestation_alert, get_recent_alerts

app = FastAPI(title="Deforestation Detection API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Deforestation Detection API is running"}

@app.get("/detect/")
async def detect_deforestation(
    region: str = Query(..., description="Region bbox as minLon,minLat,maxLon,maxLat"),
    days_back: int = Query(7, description="Days back to search for images")
):
    """
    Main endpoint to detect deforestation in a region
    """
    try:
        # Parse bounding box
        bbox = [float(coord.strip()) for coord in region.split(",")]
        if len(bbox) != 4:
            raise ValueError("Bbox must have 4 coordinates")
        
        # Fetch satellite image
        print(f"Fetching satellite image for region: {bbox}")
        image_bytes = fetch_sentinel2_image(bbox, days_back)
        
        if image_bytes is None:
            raise HTTPException(status_code=404, detail="Could not fetch satellite image")
        
        # Preprocess image
        image_np = preprocess_satellite_image(image_bytes)
        if image_np is None:
            raise HTTPException(status_code=500, detail="Failed to preprocess image")
        
        # Optional enhancement
        enhanced_image = enhance_image_for_detection(image_np)
        
        # Run deforestation detection
        confidence, mask = detector.detect_deforestation(enhanced_image)
        
        # Log alert if significant deforestation detected
        alert_logged, alert_message = log_deforestation_alert(region, confidence, bbox)
        
        # Prepare response
        deforestation_percentage = round(confidence * 100, 2)
        
        response_data = {
            "success": True,
            "region": region,
            "deforestation_detected": confidence > 0.05,
            "confidence_score": round(confidence, 4),
            "deforestation_percentage": deforestation_percentage,
            "alert_logged": alert_logged,
            "alert_message": alert_message,
            "analysis_timestamp": None,
            "recommendation": get_recommendation(confidence)
        }
        
        return JSONResponse(response_data)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

@app.get("/test/")
async def test_detection():
    """
    Test endpoint using predefined Amazon coordinates
    """
    test_coords = get_test_coordinates()
    region_str = ",".join(map(str, test_coords))
    return await detect_deforestation(region=region_str, days_back=14)

@app.get("/test/auth")
async def test_auth():
    """Test Sentinel Hub authentication"""
    from satellite import get_access_token
    token = get_access_token()
    return {
        "auth_success": token is not None,
        "token_preview": token[:20] + "..." if token else None
    }

@app.get("/test/model-details")
async def test_model_details():
    """Test to see detailed model output"""
    try:
        import numpy as np
        
        # Create a forest-like test image (green vegetation)
        forest_image = np.zeros((512, 512, 3), dtype=np.uint8)
        forest_image[:, :, 1] = 150  # Strong green channel
        forest_image[:, :, 0] = 50   # Low red
        forest_image[:, :, 2] = 50   # Low blue
        
        # Create a deforested-like test image (brown/bare soil)
        deforest_image = np.zeros((512, 512, 3), dtype=np.uint8)
        deforest_image[:, :, 0] = 120  # Brown/red soil
        deforest_image[:, :, 1] = 80   # Some green
        deforest_image[:, :, 2] = 40   # Low blue
        
        # Test both
        forest_conf, forest_mask = detector.detect_deforestation(forest_image)
        deforest_conf, deforest_mask = detector.detect_deforestation(deforest_image)
        
        return {
            "forest_test": {
                "confidence": round(forest_conf, 4),
                "percentage": round(forest_conf * 100, 2),
                "mask_stats": {
                    "min": float(forest_mask.min()),
                    "max": float(forest_mask.max()),
                    "mean": float(forest_mask.mean())
                } if forest_mask is not None else None
            },
            "deforest_test": {
                "confidence": round(deforest_conf, 4), 
                "percentage": round(deforest_conf * 100, 2),
                "mask_stats": {
                    "min": float(deforest_mask.min()),
                    "max": float(deforest_mask.max()),
                    "mean": float(deforest_mask.mean())
                } if deforest_mask is not None else None
            }
        }
        
    except Exception as e:
        return {"error": str(e)}


@app.get("/alerts/")
async def get_alerts(limit: int = Query(10, description="Number of recent alerts")):
    """
    Get recent deforestation alerts
    """
    try:
        alerts = get_recent_alerts(limit)
        return JSONResponse({
            "success": True,
            "alert_count": len(alerts),
            "alerts": alerts
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")

@app.get("/model/status")
async def model_status():
    """Check if the deforestation model is loaded properly"""
    return JSONResponse({
        "model_loaded": detector.model is not None,
        "model_path": r"C:\Users\HP\Downloads\deforestation_complete_model.h5",  # UPDATE THIS LINE
        "model_ready": detector.model is not None,
        "model_input_shape": str(detector.model.input_shape) if detector.model else None,
        "model_output_shape": str(detector.model.output_shape) if detector.model else None
    })

@app.get("/analyze/timeseries/")
async def analyze_vegetation_timeseries(
    region: str = Query(..., description="Region bbox as minLon,minLat,maxLon,maxLat")
):
    """
    Fetch last 30 days of images and analyze vegetation trend
    """
    try:
        # Parse bbox
        bbox = [float(coord.strip()) for coord in region.split(",")]
        if len(bbox) != 4:
            raise ValueError("Bbox must have 4 coordinates")
        
        # Get token
        token = get_access_token()
        if not token:
            raise HTTPException(status_code=401, detail="Authentication failed")
        
        print(f"🔍 Starting 30-day vegetation analysis for {region}")
        
        # Fetch images for last 30 days
        end_date = datetime.utcnow()
        dates = []
        vegetation_percentages = []
        
        for day_offset in range(30):
            target_date = end_date - timedelta(days=day_offset)
            date_str = target_date.strftime("%Y-%m-%d")
            
            print(f"  Fetching {date_str}...")
            image_bytes = fetch_single_day_image(bbox, target_date, token)
            
            if image_bytes:
                veg_pct = calculate_vegetation_percentage(image_bytes)
                dates.append(date_str)
                vegetation_percentages.append(veg_pct)
                print(f"    ✅ {date_str}: {veg_pct}% vegetation")
            else:
                dates.append(date_str)
                vegetation_percentages.append(None)
                print(f"    ❌ {date_str}: No data")
        
        # Reverse to chronological order
        dates.reverse()
        vegetation_percentages.reverse()
        
        # Analyze data
        analysis = analyze_timeseries_data(dates, vegetation_percentages)
        
        # Generate plot
        plot_bytes = generate_vegetation_plot(dates, vegetation_percentages, region)
        
        # Prepare response
        response_data = {
            "success": True,
            "region": region,
            "time_period": {
                "start": dates[0] if dates else None,
                "end": dates[-1] if dates else None,
                "total_days": 30
            },
            "vegetation_data": {
                "dates": dates,
                "percentages": vegetation_percentages
            },
            "analysis": analysis,
            "plot_available": plot_bytes is not None
        }
        
        return JSONResponse(response_data)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Invalid input: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.get("/analyze/timeseries/plot")
async def get_timeseries_plot(
    region: str = Query(..., description="Region bbox")
):
    """
    Get the vegetation plot as PNG image
    """
    try:
        bbox = [float(coord.strip()) for coord in region.split(",")]
        token = get_access_token()
        
        # Fetch and process data (same as above)
        end_date = datetime.utcnow()
        dates = []
        values = []
        
        for day_offset in range(30):
            target_date = end_date - timedelta(days=day_offset)
            date_str = target_date.strftime("%Y-%m-%d")
            image_bytes = fetch_single_day_image(bbox, target_date, token)
            
            if image_bytes:
                veg_pct = calculate_vegetation_percentage(image_bytes)
                dates.append(date_str)
                values.append(veg_pct)
            else:
                dates.append(date_str)
                values.append(None)
        
        dates.reverse()
        values.reverse()
        
        plot_bytes = generate_vegetation_plot(dates, values, region)
        
        if plot_bytes:
            return Response(content=plot_bytes, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Could not generate plot")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def get_recommendation(confidence):
    """Generate recommendation based on confidence level"""
    if confidence > 0.2:
        return "🚨 CRITICAL: Immediate field investigation required. Contact local authorities."
    elif confidence > 0.1:
        return "⚠️ HIGH RISK: Schedule verification within 48 hours. Monitor closely."
    elif confidence > 0.05:
        return "⚡ MEDIUM RISK: Monitor area. Consider follow-up analysis next week."
    else:
        return "✅ LOW RISK: No significant deforestation detected. Continue routine monitoring."

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

