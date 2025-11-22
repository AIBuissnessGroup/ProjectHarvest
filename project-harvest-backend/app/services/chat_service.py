"""
Google Gemini AI Service for Project Harvest

This service provides AI-powered conversational insights about Fortnite Creative maps.
Gemini can trigger ML predictions and analyze map performance through function calling.

Using Gemini instead of ChatGPT:
- Free tier: 1500 requests/day (vs OpenAI's paid-only)
- Fast responses
- Function calling support
- Great for prototypes and demos!
"""

import google.generativeai as genai
import json
import logging
from typing import Optional, Dict, Any, List
from app.core.config import settings
from app.services.fncreate_service import fetch_map_from_api, extract_features_from_api
from app.services.ml_service import ml_service

logger = logging.getLogger(__name__)


class ChatService:
    """
    Service for AI-powered chat using Google Gemini with function calling.
    
    Gemini can trigger functions to:
    - Get ML predictions for maps
    - Compare 2+ maps with rankings and statistics
    - Analyze map performance
    
    The actual computation (API calls, ML predictions) is done by YOUR code.
    Gemini just decides WHEN to trigger functions and formats the results nicely.
    """
    
    def __init__(self):
        """Initialize Gemini client and define available functions"""
        if not settings.GEMINI_API_KEY:
            logger.warning("⚠️  GEMINI_API_KEY not set. Chat service will not work.")
            self.model = None
        else:
            # Configure Gemini API
            genai.configure(api_key=settings.GEMINI_API_KEY)
            
            # Initialize Gemini model with function calling
            self.model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',  # Latest fast model with free tier
                tools=[self._get_function_declarations()],
                system_instruction=self._get_system_prompt()
            )
        
        # Initialize chat session
        self.chat_session = None
    
    def _get_system_prompt(self) -> str:
        """System prompt that defines Gemini's role"""
        return """You are an expert Fortnite Creative analytics assistant for Project Harvest.

Your role:
- Help users understand their map's predicted performance
- Explain ML predictions in simple, actionable terms
- Provide data-driven recommendations to improve map engagement
- Compare maps and identify success factors

Available ML Models:
1. **Future CCU Predictor** (R² = 0.76): Predicts CCU trends over next 7 days with daily breakdown
2. **Anomaly Detector**: Identifies unusual CCU spikes from campaigns or viral moments
3. **Discovery Predictor** (AUC = 0.82): Predicts probability of hitting Discovery placement

Key Features:
- Daily CCU forecasts (day-by-day breakdown for 7 days)
- Trend analysis (growing/declining/stable with strength indicators)
- Key insights (steepest drops, best campaign timing, volatility warnings)
- Discovery optimization recommendations

Guidelines:
- Be encouraging but realistic
- Focus on actionable insights with specific timing
- When showing daily forecasts, highlight key inflection points
- Explain predictions in context (growth rate, creator influence, tags, etc.)
- Keep responses concise (2-3 paragraphs max)
- Use emojis sparingly for readability

When providing recommendations:
- Suggest specific days for campaign launches based on forecast
- Reference similar successful maps when relevant
- Consider creator resources and map type
- Provide both quick wins and long-term strategies"""
    
    def _get_function_declarations(self) -> List[Dict]:
        """Define functions that Gemini can trigger"""
        return [
            {
                "name": "get_map_prediction",
                "description": "Get ML prediction for peak CCU of a Fortnite Creative map. Use this when user asks about predictions, performance, or peak players for a specific map.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "map_code": {
                            "type": "string",
                            "description": "The map code in format XXXX-XXXX-XXXX (e.g., '1832-0431-4852')"
                        }
                    },
                    "required": ["map_code"]
                }
            },
            {
                "name": "predict_future_ccu",
                "description": "Predict what CCU a map will have in 7 days based on current trends. Use when user asks about future performance, growth forecasts, or 'what will happen' questions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "map_code": {
                            "type": "string",
                            "description": "The map code in format XXXX-XXXX-XXXX"
                        }
                    },
                    "required": ["map_code"]
                }
            },
            {
                "name": "detect_anomalies",
                "description": "Detect unusual CCU spikes or campaign activity for a map. Use when user asks about spikes, unusual activity, viral moments, or campaign detection.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "map_code": {
                            "type": "string",
                            "description": "The map code to analyze"
                        }
                    },
                    "required": ["map_code"]
                }
            },
            {
                "name": "predict_discovery",
                "description": "Predict probability that a map will hit Discovery placement. Use when user asks about Discovery chances, optimization for Discovery, or 'will this reach Discovery'.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "map_code": {
                            "type": "string",
                            "description": "The map code to analyze"
                        }
                    },
                    "required": ["map_code"]
                }
            },
            {
                "name": "compare_maps",
                "description": "Compare performance predictions of multiple Fortnite Creative maps (2 or more). Use when user wants to compare, contrast, rank, or see differences between maps.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "map_codes": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "description": "List of map codes to compare (e.g., ['1832-0431-4852', '6562-8953-6567'])"
                        }
                    },
                    "required": ["map_codes"]
                }
            }
        ]
    
    async def chat(self, user_message: str, conversation_history: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Main chat interface with function calling support.
        
        Flow:
        1. Send user message to Gemini
        2. If Gemini requests a function, YOUR CODE executes it
        3. Send results back to Gemini
        4. Gemini formats response with the data
        
        Args:
            user_message (str): User's question/message
            conversation_history (List[Dict], optional): Previous messages for context
        
        Returns:
            Dict with 'response' (str) and 'function_called' (str, optional)
        """
        
        if not self.model:
            return {
                "response": "❌ Chat service is not configured. Please set GEMINI_API_KEY environment variable.",
                "error": "missing_api_key"
            }
        
        try:
            # Start new chat session if needed
            if not self.chat_session:
                self.chat_session = self.model.start_chat(history=[])
            
            logger.info(f"💬 Chat request: {user_message[:100]}...")
            
            # Step 1: Send message to Gemini
            response = self.chat_session.send_message(user_message)
            
            # Step 2: Check if Gemini wants to call a function
            function_called = None
            
            # Check for function calls in response
            if response.candidates and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_call = part.function_call
                        function_name = function_call.name
                        function_args = dict(function_call.args)
                        
                        logger.info(f"🔧 Gemini requesting function call: {function_name}({function_args})")
                        
                        # Step 3: YOUR CODE executes the requested function
                        function_result = await self._execute_function(function_name, function_args)
                        function_called = function_name
                        
                        # Step 4: Send function results back to Gemini
                        response = self.chat_session.send_message(
                            genai.types.content_types.to_content({
                                "function_response": {
                                    "name": function_name,
                                    "response": function_result
                                }
                            })
                        )
                        
                        # Break after first function call (can extend to support multiple)
                        break
            
            # Extract text response
            if response.candidates and response.candidates[0].content.parts:
                text_response = ""
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text'):
                        text_response += part.text
                
                return {
                    "response": text_response.strip(),
                    "function_called": function_called
                }
            else:
                return {
                    "response": "I'm sorry, I couldn't generate a response. Please try rephrasing your question.",
                    "error": "no_response"
                }
        
        except Exception as e:
            logger.error(f"❌ Error in chat service: {e}")
            return {
                "response": f"Sorry, an unexpected error occurred: {str(e)}",
                "error": "unexpected_error"
            }
    
    async def _execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute functions that Gemini triggers.
        
        This is where YOUR CODE does the actual work:
        - Fetching map data from fncreate.gg
        - Running ML predictions
        - Comparing maps
        
        Gemini just decides WHEN to call these, YOUR CODE does the computation.
        """
        
        try:
            if function_name == "get_map_prediction":
                return await self._get_map_prediction(arguments["map_code"])
            
            elif function_name == "predict_future_ccu":
                return await self._predict_future_ccu(arguments["map_code"])
            
            elif function_name == "detect_anomalies":
                return await self._detect_anomalies(arguments["map_code"])
            
            elif function_name == "predict_discovery":
                return await self._predict_discovery(arguments["map_code"])
            
            elif function_name == "compare_maps":
                return await self._compare_maps(arguments["map_codes"])
            
            else:
                return {"error": f"Unknown function: {function_name}"}
        
        except Exception as e:
            logger.error(f"❌ Error executing function {function_name}: {e}")
            return {"error": str(e)}
    
    async def _get_map_prediction(self, map_code: str) -> Dict[str, Any]:
        """
        Get ML prediction for a map.
        
        This function:
        1. Fetches map data from fncreate.gg API
        2. Extracts features for ML model
        3. Runs YOUR trained Random Forest model
        4. Returns structured data for Gemini to read
        """
        
        logger.info(f"🔍 Fetching prediction for map {map_code}")
        
        # Step 1: Fetch from API
        map_data = await fetch_map_from_api(map_code)
        if not map_data:
            return {
                "error": f"Could not fetch map {map_code}. It may not exist on fncreate.gg or the API is unavailable."
            }
        
        # Step 2: Extract features
        features = extract_features_from_api(map_data)
        if not features:
            return {
                "error": f"Could not extract features from map {map_code}."
            }
        
        # Step 3: Run YOUR ML model
        prediction = ml_service.predict(features)
        if not prediction:
            return {
                "error": "ML model failed to generate prediction."
            }
        
        # Step 4: Return structured data for Gemini
        return {
            "success": True,
            "map_name": features['name'],
            "map_code": map_code,
            "map_type": features['type'],
            "primary_tag": features['primary_tag'],
            "current_ccu": features['current_ccu'],
            "predicted_peak_ccu": prediction['predicted_peak_ccu'],
            "confidence": prediction['confidence'],
            "model_r2_score": prediction['model_r2_score'],
            "growth_rate_7d": features['growth_rate_7d'],
            "creator_followers": features['creator_followers'],
            "max_players": features['max_players'],
            "version": features['version'],
            "xp_enabled": features['xp_enabled']
        }
    
    async def _predict_future_ccu(self, map_code: str) -> Dict[str, Any]:
        """
        Predict future CCU (7-day forecast) for a map.
        
        Uses time-series trend analysis to predict where CCU will be in 7 days.
        """
        logger.info(f"🔮 Predicting future CCU for map {map_code}")
        
        try:
            result = await ml_service.predict_future_ccu(map_code)
            return {
                "success": True,
                **result
            }
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error in future CCU prediction: {e}")
            return {"error": f"Failed to predict future CCU: {str(e)}"}
    
    async def _detect_anomalies(self, map_code: str) -> Dict[str, Any]:
        """
        Detect CCU anomalies/spikes for a map.
        
        Identifies unusual activity that may indicate campaigns or viral moments.
        """
        logger.info(f"🔍 Detecting anomalies for map {map_code}")
        
        try:
            result = await ml_service.detect_anomalies(map_code)
            return {
                "success": True,
                **result
            }
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error in anomaly detection: {e}")
            return {"error": f"Failed to detect anomalies: {str(e)}"}
    
    async def _predict_discovery(self, map_code: str) -> Dict[str, Any]:
        """
        Predict Discovery placement probability for a map.
        
        Returns probability + strengths + weaknesses + recommendations.
        """
        logger.info(f"🎰 Predicting Discovery for map {map_code}")
        
        try:
            result = await ml_service.predict_discovery(map_code)
            return {
                "success": True,
                **result
            }
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error in discovery prediction: {e}")
            return {"error": f"Failed to predict Discovery: {str(e)}"}
    
    async def _compare_maps(self, map_codes: List[str]) -> Dict[str, Any]:
        """
        Compare predictions for multiple maps (2 or more).
        
        Gets predictions for all maps and returns comparison data with rankings.
        
        Args:
            map_codes (List[str]): List of map codes to compare
        
        Returns:
            Dict with predictions for all maps, rankings, and comparison stats
        """
        
        logger.info(f"⚖️  Comparing {len(map_codes)} maps: {', '.join(map_codes)}")
        
        # Get predictions for all maps
        maps_data = []
        errors = []
        
        for i, map_code in enumerate(map_codes):
            map_data = await self._get_map_prediction(map_code)
            
            if "error" in map_data:
                errors.append(f"Map {i+1} ({map_code}): {map_data['error']}")
            else:
                maps_data.append(map_data)
        
        # If any errors occurred, return them
        if errors:
            return {"error": " | ".join(errors)}
        
        # If no valid maps, return error
        if not maps_data:
            return {"error": "No valid maps to compare"}
        
        # Calculate rankings and statistics
        # Sort by predicted peak CCU (descending)
        ranked_by_prediction = sorted(
            maps_data,
            key=lambda x: x['predicted_peak_ccu'],
            reverse=True
        )
        
        # Sort by current CCU (descending)
        ranked_by_current = sorted(
            maps_data,
            key=lambda x: x['current_ccu'],
            reverse=True
        )
        
        # Sort by growth rate (descending)
        ranked_by_growth = sorted(
            maps_data,
            key=lambda x: x['growth_rate_7d'],
            reverse=True
        )
        
        # Calculate comparison statistics
        predicted_ccus = [m['predicted_peak_ccu'] for m in maps_data]
        current_ccus = [m['current_ccu'] for m in maps_data]
        growth_rates = [m['growth_rate_7d'] for m in maps_data]
        
        comparison_stats = {
            "total_maps_compared": len(maps_data),
            "predicted_peak_ccu": {
                "highest": max(predicted_ccus),
                "lowest": min(predicted_ccus),
                "average": sum(predicted_ccus) / len(predicted_ccus),
                "range": max(predicted_ccus) - min(predicted_ccus)
            },
            "current_ccu": {
                "highest": max(current_ccus),
                "lowest": min(current_ccus),
                "average": sum(current_ccus) / len(current_ccus)
            },
            "growth_rate_7d": {
                "highest": max(growth_rates),
                "lowest": min(growth_rates),
                "average": sum(growth_rates) / len(growth_rates)
            }
        }
        
        # Build rankings with positions
        rankings = {
            "by_predicted_peak_ccu": [
                {
                    "rank": i + 1,
                    "map_name": m['map_name'],
                    "map_code": m['map_code'],
                    "predicted_peak_ccu": m['predicted_peak_ccu'],
                    "percentage_of_best": (m['predicted_peak_ccu'] / ranked_by_prediction[0]['predicted_peak_ccu'] * 100) if ranked_by_prediction[0]['predicted_peak_ccu'] > 0 else 0
                }
                for i, m in enumerate(ranked_by_prediction)
            ],
            "by_current_ccu": [
                {
                    "rank": i + 1,
                    "map_name": m['map_name'],
                    "map_code": m['map_code'],
                    "current_ccu": m['current_ccu']
                }
                for i, m in enumerate(ranked_by_current)
            ],
            "by_growth_rate": [
                {
                    "rank": i + 1,
                    "map_name": m['map_name'],
                    "map_code": m['map_code'],
                    "growth_rate_7d": m['growth_rate_7d']
                }
                for i, m in enumerate(ranked_by_growth)
            ]
        }
        
        # Return comprehensive comparison
        return {
            "success": True,
            "maps": maps_data,  # Full data for all maps
            "rankings": rankings,  # Ranked lists by different metrics
            "statistics": comparison_stats,  # Summary statistics
            "top_performer": ranked_by_prediction[0],  # Best map by prediction
            "fastest_growing": ranked_by_growth[0]  # Best map by growth rate
        }
    
    async def get_quick_insights(self, map_code: str) -> str:
        """
        Get quick AI insights for a map without conversation context.
        
        Simpler alternative to full chat - just returns formatted insights.
        """
        
        user_message = f"Provide a brief performance analysis and 3 recommendations for map {map_code}."
        result = await self.chat(user_message)
        return result.get('response', 'Unable to generate insights.')


# Singleton instance
chat_service = ChatService()
