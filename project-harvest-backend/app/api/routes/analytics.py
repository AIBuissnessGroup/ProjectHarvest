"""
Analytics API Routes
====================
Endpoints for ML predictions and analytics insights
"""

from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.models.island import PredictionRequest, PredictionResponse, ModelInfo, ErrorResponse
from app.services.ml_service import ml_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix=f"{settings.API_V1_STR}/analytics",
    tags=["Analytics & ML Predictions"]
)


@router.post("/predict", 
             response_model=PredictionResponse,
             summary="Predict Peak CCU for a Map",
             description="""
Predict the all-time peak concurrent users (CCU) for a Fortnite Creative map using our trained Random Forest model.

**Two ways to use:**
1. **Easy Mode:** Just provide `map_code` and we'll fetch all data automatically from fncreate.gg
2. **Manual Mode:** Provide all features manually (type, tags, CCU, etc.)

**Model Performance:**
- R² Score: 0.524 (52.4% variance explained)
- Trained on 74 maps from fncreate.gg
- Best for mainstream maps (20K-50K CCU range)

**Example (Easy):**
```json
{
  "map_code": "1832-0431-4852"
}
```
""")
async def predict_peak_ccu(request: PredictionRequest):
    """
    Predict peak CCU for a map
    
    Supports two modes:
    1. Auto-fetch: Provide map_code only
    2. Manual: Provide all features
    
    Returns:
        Prediction with confidence level and model information
    """
    try:
        from app.services.fncreate_service import fetch_map_from_api, extract_features_from_api
        
        map_data = None
        
        # Check if map_code is provided for auto-fetch
        if request.map_code:
            logger.info(f"🔍 Auto-fetching data for map {request.map_code}")
            
            # Fetch from API
            api_data = await fetch_map_from_api(request.map_code)
            
            if api_data is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Could not fetch map {request.map_code} from fncreate.gg. Map may not exist or API is unavailable."
                )
            
            # Extract features
            map_data = extract_features_from_api(api_data)
            
            if map_data is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to extract features from map data"
                )
            
            logger.info(f"✅ Successfully fetched and extracted features for {map_data.get('name')}")
        
        elif request.primary_tag:
            # Manual mode - use provided features
            logger.info(f"📝 Using manual features with primary_tag: {request.primary_tag}")
            
            map_data = request.model_dump(exclude={'map_code'}, exclude_none=True)
            
            # Set defaults for missing optional fields
            map_data.setdefault('type', 'uefn')
            map_data.setdefault('num_tags', 3)
            map_data.setdefault('max_players', 16)
            map_data.setdefault('xp_enabled', True)
            map_data.setdefault('creator_followers', 0)
            map_data.setdefault('version', 1)
            map_data.setdefault('current_ccu', 0)
            map_data.setdefault('growth_rate_7d', 0.0)
        
        else:
            # Neither map_code nor primary_tag provided
            logger.error(f"❌ Validation failed - request: {request.model_dump()}")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Either 'map_code' OR 'primary_tag' (with other features) must be provided"
            )
        
        # Make prediction
        result = ml_service.predict(map_data)
        
        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate prediction. Model may not be loaded."
            )
        
        return PredictionResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in prediction endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction error: {str(e)}"
        )


@router.get("/model-info",
            response_model=ModelInfo,
            summary="Get ML Model Information",
            description="Get information about the loaded machine learning model including performance metrics")
async def get_model_info():
    """
    Get information about the loaded ML model
    
    Returns:
        Model status, name, version, and performance metrics
    """
    try:
        info = ml_service.get_model_info()
        return ModelInfo(**info)
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving model information: {str(e)}"
        )



