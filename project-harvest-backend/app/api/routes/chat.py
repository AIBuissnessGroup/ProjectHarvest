"""
Chat/AI API Routes
==================
Endpoints for AI-powered chat using Google Gemini
"""

from fastapi import APIRouter, HTTPException, status
from app.models.island import (
    ChatRequest, 
    ChatResponse, 
    InsightsResponse,
    ChatHealthCheck
)
from app.services.chat_service import chat_service
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix=f"{settings.API_V1_STR}/chat",
    tags=["AI Chat"]
)


@router.get(
    "/health",
    response_model=ChatHealthCheck,
    summary="Check chat service health",
    description="Verify if the AI chat service is configured and available"
)
async def chat_health_check():
    """
    Check if the chat service is properly configured.
    
    Returns:
        - status: 'available' or 'unavailable'
        - service: 'Google Gemini'
        - configured: Whether GEMINI_API_KEY is set
        - message: Human-readable status
    """
    
    is_configured = settings.GEMINI_API_KEY is not None
    
    if is_configured:
        return ChatHealthCheck(
            status="available",
            service="Google Gemini",
            configured=True,
            message="✅ Chat service is configured and ready to use! Ask me anything about your Fortnite maps."
        )
    else:
        return ChatHealthCheck(
            status="unavailable",
            service="Google Gemini",
            configured=False,
            message="⚠️ Chat service is not configured. Set GEMINI_API_KEY to enable AI features."
        )


@router.post(
    "",
    response_model=ChatResponse,
    summary="Chat with AI assistant",
    description="Conversational interface with Google Gemini. Ask questions about maps, predictions, and get insights."
)
async def chat(request: ChatRequest):
    """
    Chat with the AI assistant powered by Google Gemini.
    
    The AI can:
    - Get ML predictions for maps
    - Compare multiple maps
    - Explain predictions and metrics
    - Provide recommendations
    
    Examples:
    - "What is the predicted peak CCU for map 1832-0431-4852?"
    - "Compare maps 1832-0431-4852 and 6562-8953-6567"
    - "Why is my map underperforming?"
    - "What tags should I use to increase engagement?"
    
    Args:
        request: ChatRequest with message and optional conversation history
    
    Returns:
        ChatResponse with AI-generated response
    """
    
    # Check if chat service is configured
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    try:
        logger.info(f"💬 Chat request: {request.message[:100]}...")
        
        # Send message to chat service
        result = await chat_service.chat(
            user_message=request.message,
            conversation_history=request.conversation_history
        )
        
        # Check for errors
        if "error" in result:
            error_msg = result.get("error")
            logger.error(f"❌ Chat error: {error_msg}")
            
            # Return error in response (not HTTP error, so conversation can continue)
            return ChatResponse(
                response=result.get("response", "Sorry, I encountered an error."),
                error=error_msg
            )
        
        # Return successful response
        return ChatResponse(
            response=result["response"],
            function_called=result.get("function_called"),
            chart_data=result.get("chart_data")
        )
    
    except Exception as e:
        logger.error(f"❌ Unexpected error in chat endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )


@router.post(
    "/insights/{map_code}",
    response_model=InsightsResponse,
    summary="Get quick AI insights for a map",
    description="Get AI-powered analysis and recommendations for a specific map"
)
async def get_insights(map_code: str):
    """
    Get quick AI insights for a specific map.
    
    This endpoint:
    1. Fetches map data from fncreate.gg
    2. Runs ML prediction
    3. Generates AI-powered insights and recommendations
    
    No conversation context - just instant insights!
    
    Args:
        map_code: Map code (e.g., '1832-0431-4852')
    
    Returns:
        InsightsResponse with AI-generated insights
    """
    
    # Check if chat service is configured
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    try:
        logger.info(f"🔍 Generating insights for map {map_code}")
        
        # Get quick insights from chat service
        insights = await chat_service.get_quick_insights(map_code)
        
        # Check if insights were generated
        if insights.startswith("❌") or "error" in insights.lower():
            return InsightsResponse(
                map_code=map_code,
                map_name=None,
                insights=insights,
                error="Failed to generate insights"
            )
        
        # Return successful insights
        return InsightsResponse(
            map_code=map_code,
            map_name=None,  # Could extract from chat_service response if needed
            insights=insights
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error generating insights for {map_code}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate insights: {str(e)}"
        )


@router.post(
    "/compare",
    response_model=ChatResponse,
    summary="Compare multiple maps (shortcut)",
    description="Convenient endpoint to compare 2+ maps without full conversation"
)
async def compare_maps(map_codes: list[str]):
    """
    Compare multiple maps using AI.
    
    Convenient shortcut for comparing maps without sending a full chat message.
    
    Args:
        map_codes: List of map codes to compare (e.g., ['1832-0431-4852', '6562-8953-6567'])
    
    Returns:
        ChatResponse with AI comparison and analysis
    """
    
    # Check if chat service is configured
    if not settings.GEMINI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Chat service is not configured. Please set GEMINI_API_KEY environment variable."
        )
    
    # Validate input
    if not map_codes or len(map_codes) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please provide at least 2 map codes to compare"
        )
    
    if len(map_codes) > 10:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Maximum 10 maps can be compared at once"
        )
    
    try:
        logger.info(f"⚖️  Comparing {len(map_codes)} maps via shortcut endpoint")
        
        # Create chat message
        map_codes_str = ", ".join(map_codes)
        message = f"Compare these maps and provide a detailed analysis: {map_codes_str}"
        
        # Send to chat service
        result = await chat_service.chat(user_message=message)
        
        # Return response
        return ChatResponse(
            response=result["response"],
            function_called=result.get("function_called")
        )
    
    except Exception as e:
        logger.error(f"❌ Error comparing maps: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare maps: {str(e)}"
        )

