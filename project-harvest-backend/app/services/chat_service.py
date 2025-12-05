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

IMPORTANT - Explaining Predictions (Keep it Clean!):
The prediction_factors object contains the ACTUAL reasons for the prediction. Use them, but keep responses READABLE.

CRITICAL: Use the EXACT "trend" value from the model response (Growing/Declining/Stable). Do NOT reinterpret it!

Format your response like this:
1. **Opening**: State the map name, the EXACT trend from the model (Growing/Declining/Stable), and predicted CCU in 7 days
2. **Why**: Explain the PRIMARY reason in ONE clear sentence
3. **Key factors** (use bullet points, max 3):
   - Only mention the TOP 2-3 most important factors
   - Keep each bullet SHORT
   - DON'T include model weight percentages unless user asks
4. **Daily forecast**: Show with day labels (Day 1: X, Day 2: Y, etc.)
5. **Offer chart**: Ask if they want a visualization

Example of GOOD response:
"**🍌PEELY VS JONESY** is predicted to be **Stable** over the next 7 days, reaching approximately **250 CCU** (currently 513).

**Why?** The map has a solid baseline CCU but is experiencing some momentum loss.

**Key factors:**
- Baseline CCU of 262 (moderate player base)
- Recent momentum declining (-46%)
- High volatility in player counts

**Daily forecast:**
- Day 1: 260 CCU
- Day 2: 258 CCU
- Day 3: 256 CCU
- Day 4: 255 CCU
- Day 5: 253 CCU
- Day 6: 251 CCU
- Day 7: 250 CCU

Would you like me to generate a chart?"

If user asks "why" or "explain the factors in detail", THEN provide the model weight percentages.

IMPORTANT - Chart Visualizations:
- When user asks for a chart, graph, or visualization, you MUST call the appropriate function:
  - For future/prediction charts: call predict_future_ccu function
  - For historical/current/actual CCU charts: call get_historical_ccu function
- NEVER just say "I'll generate the chart" without actually calling the function
- If user says "yes", "make it", "generate it", "show me the chart" after discussing a map, call the appropriate chart function for that map
- If the user asks for a prediction WITHOUT mentioning charts, provide the prediction data and then ask: "Would you like me to generate a chart showing this forecast?"
- Available charts:
  1. **Future CCU Chart**: Shows 7-day forecast with confidence intervals (use predict_future_ccu)
  2. **Historical CCU Chart**: Shows actual past CCU data with anomaly markers (use get_historical_ccu)

IMPORTANT - Data Sources:
- If the function result includes "cache_warning" or "data_source: local_cache", ALWAYS mention at the end:
  "⚠️ Please note: This data is from our local cache (collected [date]) and may be outdated as the fncreate.gg API is currently unavailable."
- If "collection_date" is provided, include it in the warning

Response Formatting (IMPORTANT):
- Use **bold** for key metrics, map names, and important numbers (e.g., **432 CCU**, **Declining trend**)
- Use bullet points for lists of insights or recommendations
- Structure responses with clear sections when providing detailed analysis
- Keep responses concise (2-3 paragraphs max) but well-formatted

Guidelines:
- Be encouraging but realistic
- Focus on actionable insights with specific timing
- When showing daily forecasts, highlight key inflection points
- Explain predictions in context (growth rate, creator influence, tags, etc.)
- Use emojis sparingly for readability (1-2 per response max)
- NEVER output raw JSON data in your response. Summarize the data in natural language instead.
- When generating charts, just confirm you're generating it - the frontend will display the chart automatically.

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
            },
            {
                "name": "get_historical_ccu",
                "description": "Generate a historical CCU chart for a map showing past performance with anomaly markers. ALWAYS use this when user asks to 'see the chart', 'make a chart', 'generate a chart', 'show me the spikes', or wants to visualize historical/current CCU data. Also use when user confirms with 'yes', 'make it', 'do it' after discussing anomalies or historical data.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "map_code": {
                            "type": "string",
                            "description": "The map code to get historical data for"
                        }
                    },
                    "required": ["map_code"]
                }
            },
            {
                "name": "analyze_peak_times",
                "description": "Analyze when a map has the most players (peak times). Use when user asks about 'peak times', 'most popular times', 'best times to play', 'when are players online', 'busiest hours', or time-based analysis.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "map_code": {
                            "type": "string",
                            "description": "The map code to analyze peak times for"
                        }
                    },
                    "required": ["map_code"]
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
            chart_data = None
            
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
                        
                        # Store chart data if it's a chart-generating function
                        if function_name == "predict_future_ccu" and function_result.get("success"):
                            chart_data = function_result
                        elif function_name == "get_historical_ccu" and function_result.get("success"):
                            chart_data = function_result
                        
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
                    "function_called": function_called,
                    "chart_data": chart_data
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
            
            elif function_name == "get_historical_ccu":
                return await self._get_historical_ccu(arguments["map_code"])
            
            elif function_name == "analyze_peak_times":
                return await self._analyze_peak_times(arguments["map_code"])
            
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
    
    async def _get_historical_ccu(self, map_code: str) -> Dict[str, Any]:
        """
        Get historical CCU data for a map to display in a chart.
        Returns the actual CCU values over time with anomaly markers.
        """
        
        logger.info(f"📊 Fetching historical CCU for map {map_code}")
        
        # Fetch map data
        map_data = await fetch_map_from_api(map_code)
        if not map_data:
            return {
                "error": f"Could not fetch map {map_code}. It may not exist or the API is unavailable."
            }
        
        # Get the raw stats
        stats_7d = map_data.get('stats_7d', {})
        map_info = map_data.get('map_data', {})
        map_name = map_info.get('name', 'Unknown Map')
        
        # Extract CCU data points with timestamps
        historical_data = []
        
        # Check if stats_7d has 'data' -> 'stats' structure
        if isinstance(stats_7d, dict):
            stats_list = stats_7d.get('data', {}).get('stats', [])
            
            # Get actual date range from API (same as ml_service uses)
            from datetime import datetime, timedelta
            try:
                date_from_str = stats_7d.get('data', {}).get('from', '')
                date_to_str = stats_7d.get('data', {}).get('to', '')
                date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
                date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
                total_duration = (date_to - date_from).total_seconds()
                has_api_dates = True
                logger.info(f"📅 Using API dates: {date_from_str} to {date_to_str}")
            except Exception as e:
                logger.warning(f"⚠️ Could not parse API dates, falling back to calculated: {e}")
                has_api_dates = False
            
            if isinstance(stats_list, list):
                for i, ccu in enumerate(stats_list):
                    if isinstance(ccu, (int, float)):
                        # Calculate timestamp using actual API dates (consistent with ml_service)
                        if has_api_dates and len(stats_list) > 1:
                            progress = i / (len(stats_list) - 1)
                            seconds_offset = total_duration * progress
                            timestamp = date_from + timedelta(seconds=seconds_offset)
                        else:
                            # Fallback: calculate backwards from now
                            timestamp = datetime.now() - timedelta(minutes=30 * (len(stats_list) - i - 1))
                        
                        historical_data.append({
                            "timestamp": timestamp.strftime("%b %d, %I:%M %p"),
                            "ccu": int(ccu),
                            "index": i
                        })
        
        if not historical_data:
            return {
                "error": "No historical CCU data available for this map."
            }
        
        # Use the HYBRID anomaly detector to find spikes
        anomalies = []
        anomaly_indices = set()
        marked_count = 0
        
        try:
            logger.info(f"🔍 Running HYBRID anomaly detector on map {map_code}...")
            
            # Call the hybrid anomaly detector (STL + Peaks + LOF)
            anomaly_result = await ml_service.detect_anomalies(map_code)
            
            if anomaly_result and 'spike_details' in anomaly_result:
                spike_details = anomaly_result.get('spike_details', [])
                logger.info(f"📊 Hybrid anomaly detector found {len(spike_details)} spikes")
                
                for spike in spike_details:
                    spike_idx = spike.get('timestamp_index', -1)
                    spike_ccu = spike.get('ccu', 0)
                    
                    if spike_idx >= 0 and spike_idx < len(historical_data):
                        # Mark this point in historical data
                        anomaly_indices.add(spike_idx)
                        historical_data[spike_idx]['isAnomaly'] = True
                        marked_count += 1
                        
                        anomalies.append({
                            "timestamp": historical_data[spike_idx]['timestamp'],
                            "ccu": spike_ccu,
                            "index": spike_idx,
                            "votes": spike.get('votes', 0),
                            "methods_agreed": spike.get('methods_agreed', []),
                            "approximate_timestamp": spike.get('approximate_timestamp', '')
                        })
                        logger.info(f"  🚨 Marked spike at index {spike_idx}: CCU={spike_ccu}, Votes={spike.get('votes', 0)}/3")
                
                logger.info(f"✅ Marked {marked_count} anomalies from hybrid detector")
            else:
                logger.warning(f"⚠️ No spike details from anomaly detector")
                
        except Exception as e:
            logger.error(f"❌ Could not run anomaly detection: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # Data source info
        data_source = map_data.get('_source', 'live_api')
        cache_warning = map_data.get('_cache_warning', None)
        collection_date = map_data.get('_collection_date', None)
        
        return {
            "success": True,
            "map_code": map_code,
            "map_name": map_name,
            "historical_data": historical_data,
            "anomalies": anomalies,
            "anomaly_count": marked_count,
            "data_points": len(historical_data),
            "time_span": f"{len(historical_data) * 30} minutes ({len(historical_data)} data points)",
            "data_source": data_source,
            "cache_warning": cache_warning,
            "collection_date": collection_date,
            "chart_type": "historical_ccu"
        }
    
    async def _analyze_peak_times(self, map_code: str) -> Dict[str, Any]:
        """
        Analyze peak times for a map - when are players most active?
        Identifies popular hours, days of week, and patterns.
        """
        
        logger.info(f"⏰ Analyzing peak times for map {map_code}")
        
        # Fetch map data
        map_data = await fetch_map_from_api(map_code)
        if not map_data:
            return {
                "error": f"Could not fetch map {map_code}. It may not exist or the API is unavailable."
            }
        
        # Get the raw stats
        stats_7d = map_data.get('stats_7d', {})
        map_info = map_data.get('map_data', {})
        map_name = map_info.get('name', 'Unknown Map')
        
        # Extract CCU data with timestamps
        from datetime import datetime, timedelta
        from collections import defaultdict
        import numpy as np
        
        hourly_data = defaultdict(list)  # hour -> list of CCU values
        daily_data = defaultdict(list)   # day_name -> list of CCU values
        time_series = []
        
        # Check if stats_7d has 'data' -> 'stats' structure
        if isinstance(stats_7d, dict):
            stats_list = stats_7d.get('data', {}).get('stats', [])
            
            # Get actual date range from API
            try:
                date_from_str = stats_7d.get('data', {}).get('from', '')
                date_to_str = stats_7d.get('data', {}).get('to', '')
                date_from = datetime.fromisoformat(date_from_str.replace('Z', '+00:00'))
                date_to = datetime.fromisoformat(date_to_str.replace('Z', '+00:00'))
                total_duration = (date_to - date_from).total_seconds()
                has_api_dates = True
            except Exception as e:
                logger.warning(f"⚠️ Could not parse API dates: {e}")
                has_api_dates = False
                date_from = datetime.now() - timedelta(days=7)
                total_duration = 7 * 24 * 60 * 60  # 7 days in seconds
            
            if isinstance(stats_list, list) and len(stats_list) > 0:
                for i, ccu in enumerate(stats_list):
                    if isinstance(ccu, (int, float)):
                        # Calculate timestamp
                        if has_api_dates and len(stats_list) > 1:
                            progress = i / (len(stats_list) - 1)
                            seconds_offset = total_duration * progress
                            timestamp = date_from + timedelta(seconds=seconds_offset)
                        else:
                            timestamp = date_from + timedelta(minutes=30 * i)
                        
                        hour = timestamp.hour
                        day_name = timestamp.strftime('%A')  # Monday, Tuesday, etc.
                        
                        hourly_data[hour].append(int(ccu))
                        daily_data[day_name].append(int(ccu))
                        time_series.append({
                            'timestamp': timestamp,
                            'ccu': int(ccu),
                            'hour': hour,
                            'day': day_name
                        })
        
        if not time_series:
            return {
                "error": "No time series data available for this map."
            }
        
        # Calculate hourly averages and find peak hours
        hourly_avg = {}
        for hour, values in hourly_data.items():
            hourly_avg[hour] = round(np.mean(values), 1)
        
        # Sort by average CCU to find peak hours
        sorted_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)
        peak_hours = sorted_hours[:3]  # Top 3 peak hours
        low_hours = sorted_hours[-3:]  # Bottom 3 hours
        
        # Calculate daily averages
        daily_avg = {}
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for day, values in daily_data.items():
            daily_avg[day] = round(np.mean(values), 1)
        
        # Sort days by average CCU
        sorted_days = sorted(daily_avg.items(), key=lambda x: x[1], reverse=True)
        
        # Calculate overall stats
        all_ccu = [t['ccu'] for t in time_series]
        overall_avg = float(round(np.mean(all_ccu), 1))
        overall_max = int(max(all_ccu))
        overall_min = int(min(all_ccu))
        
        # Format peak hours for display
        def format_hour(h):
            if h == 0:
                return "12 AM (Midnight)"
            elif h < 12:
                return f"{h} AM"
            elif h == 12:
                return "12 PM (Noon)"
            else:
                return f"{h-12} PM"
        
        # Convert numpy types to native Python types
        peak_hours_formatted = [
            {"hour": format_hour(int(h)), "avg_ccu": float(avg), "raw_hour": int(h)}
            for h, avg in peak_hours
        ]
        
        low_hours_formatted = [
            {"hour": format_hour(int(h)), "avg_ccu": float(avg), "raw_hour": int(h)}
            for h, avg in low_hours
        ]
        
        # Data source info
        data_source = map_data.get('_source', 'live_api')
        cache_warning = map_data.get('_cache_warning', None)
        collection_date = map_data.get('_collection_date', None)
        
        # Convert daily and hourly breakdowns to native Python types
        daily_breakdown = {day: float(daily_avg.get(day, 0)) for day in day_order if day in daily_avg}
        hourly_breakdown = {format_hour(int(h)): float(avg) for h, avg in sorted(hourly_avg.items())}
        
        # Convert best/worst day tuples
        best_day = (sorted_days[0][0], float(sorted_days[0][1])) if sorted_days else None
        worst_day = (sorted_days[-1][0], float(sorted_days[-1][1])) if sorted_days else None
        
        return {
            "success": True,
            "map_code": map_code,
            "map_name": map_name,
            "analysis": {
                "peak_hours": peak_hours_formatted,
                "low_activity_hours": low_hours_formatted,
                "best_day": best_day,
                "worst_day": worst_day,
                "daily_breakdown": daily_breakdown,
                "hourly_breakdown": hourly_breakdown
            },
            "stats": {
                "overall_average": overall_avg,
                "peak_ccu": overall_max,
                "lowest_ccu": overall_min,
                "data_points": len(time_series),
                "time_span_days": float(round(total_duration / (24 * 60 * 60), 1))
            },
            "insights": {
                "best_campaign_time": f"{peak_hours_formatted[0]['hour']} on {sorted_days[0][0]}" if peak_hours_formatted and sorted_days else "Unknown",
                "avoid_time": f"{low_hours_formatted[0]['hour']}" if low_hours_formatted else "Unknown",
                "pattern_detected": bool(len(peak_hours) > 0 and (peak_hours[0][1] > overall_avg * 1.5))
            },
            "data_source": data_source,
            "cache_warning": cache_warning,
            "collection_date": collection_date
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
