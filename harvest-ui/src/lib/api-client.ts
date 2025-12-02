/**
 * API Client for Project Harvest Backend
 * Handles all communication with FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// ============================================
// Types
// ============================================

export interface MapData {
  map_code: string;
  title?: string;
  creator?: string;
  current_ccu?: number;
  peak_ccu?: number;
  [key: string]: any;
}

export interface FutureCCUPrediction {
  map_code: string;
  predicted_ccu_7d: number;
  trend: 'Growing' | 'Declining' | 'Stable';
  daily_forecast: Array<{
    day: number;
    predicted_ccu: number;
    confidence_lower: number;
    confidence_upper: number;
  }>;
  baseline_ccu: number;
  trend_slope: number;
  insights: {
    steepest_drop_day?: number;
    steepest_drop_amount?: number;
    best_campaign_day?: number;
    volatility: string;
  };
}

export interface AnomalyDetection {
  map_code: string;
  anomalies_detected: number;
  spike_intervals: Array<{
    timestamp: string;
    ccu_value: number;
    spike_score: number;
    analysis: string;
  }>;
}

export interface DiscoveryPrediction {
  map_code: string;
  discovery_probability: number;
  predicted_class: 'Yes' | 'No';
  confidence_score: number;
  strengths: string[];
  weaknesses: string[];
  recommendations: string[];
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatResponse {
  response: string;
  conversation_history?: ChatMessage[];
  chart_data?: any;
  function_called?: string;
}

// ============================================
// API Error Handling
// ============================================

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public details?: any
  ) {
    super(message);
    this.name = 'APIError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new APIError(
      errorData.detail || `HTTP Error ${response.status}`,
      response.status,
      errorData
    );
  }
  return response.json();
}

// ============================================
// Analytics Endpoints
// ============================================

export const analyticsAPI = {
  /**
   * Get future CCU prediction (7 days) with daily breakdown
   */
  async predictFutureCCU(mapCode: string): Promise<FutureCCUPrediction> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/predict/future-ccu`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ map_code: mapCode }),
    });
    return handleResponse<FutureCCUPrediction>(response);
  },

  /**
   * Detect anomalies/spikes in CCU data
   */
  async detectAnomalies(mapCode: string): Promise<AnomalyDetection> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/detect/anomalies`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ map_code: mapCode }),
    });
    return handleResponse<AnomalyDetection>(response);
  },

  /**
   * Predict probability of hitting Discovery placement
   */
  async predictDiscovery(mapCode: string): Promise<DiscoveryPrediction> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/predict/discovery`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ map_code: mapCode }),
    });
    return handleResponse<DiscoveryPrediction>(response);
  },

  /**
   * Get model information
   */
  async getModelInfo(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/analytics/model-info`);
    return handleResponse(response);
  },
};

// ============================================
// Chat Endpoints
// ============================================

export const chatAPI = {
  /**
   * Send a message to the AI chatbot
   */
  async sendMessage(
    message: string,
    conversationHistory: ChatMessage[] = []
  ): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message,
        conversation_history: conversationHistory,
      }),
    });
    return handleResponse<ChatResponse>(response);
  },

  /**
   * Get AI insights for a specific map
   */
  async getMapInsights(mapCode: string): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/insights/${mapCode}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    return handleResponse<ChatResponse>(response);
  },

  /**
   * Compare multiple maps
   */
  async compareMaps(mapCodes: string[]): Promise<ChatResponse> {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ map_codes: mapCodes }),
    });
    return handleResponse<ChatResponse>(response);
  },

  /**
   * Check chat health
   */
  async checkHealth(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/v1/chat/health`);
    return handleResponse(response);
  },
};

// ============================================
// Maps Endpoints (fncreate.gg data)
// ============================================

export const mapsAPI = {
  /**
   * Get map details from fncreate.gg
   */
  async getMapDetails(mapCode: string): Promise<MapData> {
    const response = await fetch(`${API_BASE_URL}/api/v1/islands/${mapCode}`);
    return handleResponse<MapData>(response);
  },

  /**
   * Search for maps (if implemented in backend)
   */
  async searchMaps(query: string, limit: number = 20): Promise<MapData[]> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/islands/search?q=${encodeURIComponent(query)}&limit=${limit}`
    );
    return handleResponse<MapData[]>(response);
  },
};

// ============================================
// Health Check
// ============================================

export const healthAPI = {
  /**
   * Check if backend is healthy
   */
  async check(): Promise<{ status: string; version?: string }> {
    const response = await fetch(`${API_BASE_URL}/health`);
    return handleResponse(response);
  },
};

// ============================================
// Combined Helper Functions
// ============================================

/**
 * Get comprehensive analysis for a map (all 3 models)
 */
export async function getFullMapAnalysis(mapCode: string) {
  try {
    const [futureCCU, anomalies, discovery, mapDetails] = await Promise.allSettled([
      analyticsAPI.predictFutureCCU(mapCode),
      analyticsAPI.detectAnomalies(mapCode),
      analyticsAPI.predictDiscovery(mapCode),
      mapsAPI.getMapDetails(mapCode),
    ]);

    return {
      futureCCU: futureCCU.status === 'fulfilled' ? futureCCU.value : null,
      anomalies: anomalies.status === 'fulfilled' ? anomalies.value : null,
      discovery: discovery.status === 'fulfilled' ? discovery.value : null,
      mapDetails: mapDetails.status === 'fulfilled' ? mapDetails.value : null,
      errors: {
        futureCCU: futureCCU.status === 'rejected' ? futureCCU.reason : null,
        anomalies: anomalies.status === 'rejected' ? anomalies.reason : null,
        discovery: discovery.status === 'rejected' ? discovery.reason : null,
        mapDetails: mapDetails.status === 'rejected' ? mapDetails.reason : null,
      },
    };
  } catch (error) {
    console.error('Error fetching full map analysis:', error);
    throw error;
  }
}

export default {
  analytics: analyticsAPI,
  chat: chatAPI,
  maps: mapsAPI,
  health: healthAPI,
  getFullMapAnalysis,
};

