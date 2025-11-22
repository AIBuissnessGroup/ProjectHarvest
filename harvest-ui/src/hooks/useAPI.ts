/**
 * React Hooks for API Integration
 * Provides easy-to-use hooks for fetching data from the backend
 */

import { useState, useEffect, useCallback } from 'react';
import {
  analyticsAPI,
  chatAPI,
  mapsAPI,
  getFullMapAnalysis,
  APIError,
  type FutureCCUPrediction,
  type AnomalyDetection,
  type DiscoveryPrediction,
  type MapData,
  type ChatMessage,
  type ChatResponse,
} from '@/lib/api-client';

// ============================================
// Generic Hook Types
// ============================================

interface UseAPIState<T> {
  data: T | null;
  loading: boolean;
  error: APIError | Error | null;
  refetch: () => void;
}

// ============================================
// Analytics Hooks
// ============================================

/**
 * Hook to fetch Future CCU prediction
 */
export function useFutureCCU(mapCode: string | null): UseAPIState<FutureCCUPrediction> {
  const [data, setData] = useState<FutureCCUPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!mapCode) return;

    setLoading(true);
    setError(null);
    try {
      const result = await analyticsAPI.predictFutureCCU(mapCode);
      setData(result);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setLoading(false);
    }
  }, [mapCode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Hook to fetch Anomaly Detection
 */
export function useAnomalies(mapCode: string | null): UseAPIState<AnomalyDetection> {
  const [data, setData] = useState<AnomalyDetection | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!mapCode) return;

    setLoading(true);
    setError(null);
    try {
      const result = await analyticsAPI.detectAnomalies(mapCode);
      setData(result);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setLoading(false);
    }
  }, [mapCode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Hook to fetch Discovery Prediction
 */
export function useDiscoveryPrediction(mapCode: string | null): UseAPIState<DiscoveryPrediction> {
  const [data, setData] = useState<DiscoveryPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!mapCode) return;

    setLoading(true);
    setError(null);
    try {
      const result = await analyticsAPI.predictDiscovery(mapCode);
      setData(result);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setLoading(false);
    }
  }, [mapCode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Hook to fetch full map analysis (all 3 models)
 */
export function useFullMapAnalysis(mapCode: string | null) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!mapCode) return;

    setLoading(true);
    setError(null);
    try {
      const result = await getFullMapAnalysis(mapCode);
      setData(result);
    } catch (err) {
      setError(err as Error);
    } finally {
      setLoading(false);
    }
  }, [mapCode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================
// Chat Hooks
// ============================================

/**
 * Hook for AI chat functionality
 */
export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | Error | null>(null);

  const sendMessage = useCallback(async (message: string) => {
    setLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage: ChatMessage = { role: 'user', content: message };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await chatAPI.sendMessage(message, messages);
      
      // Add AI response
      const aiMessage: ChatMessage = { role: 'assistant', content: response.response };
      setMessages(prev => [...prev, aiMessage]);

      return response;
    } catch (err) {
      setError(err as APIError);
      // Remove user message if failed
      setMessages(prev => prev.slice(0, -1));
      throw err;
    } finally {
      setLoading(false);
    }
  }, [messages]);

  const getMapInsights = useCallback(async (mapCode: string) => {
    setLoading(true);
    setError(null);

    try {
      const response = await chatAPI.getMapInsights(mapCode);
      
      // Add AI response
      const aiMessage: ChatMessage = { role: 'assistant', content: response.response };
      setMessages(prev => [...prev, aiMessage]);

      return response;
    } catch (err) {
      setError(err as APIError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const compareMaps = useCallback(async (mapCodes: string[]) => {
    setLoading(true);
    setError(null);

    try {
      const response = await chatAPI.compareMaps(mapCodes);
      
      // Add AI response
      const aiMessage: ChatMessage = { role: 'assistant', content: response.response };
      setMessages(prev => [...prev, aiMessage]);

      return response;
    } catch (err) {
      setError(err as APIError);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  return {
    messages,
    loading,
    error,
    sendMessage,
    getMapInsights,
    compareMaps,
    clearMessages,
  };
}

// ============================================
// Maps Hooks
// ============================================

/**
 * Hook to fetch map details
 */
export function useMapDetails(mapCode: string | null): UseAPIState<MapData> {
  const [data, setData] = useState<MapData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | Error | null>(null);

  const fetchData = useCallback(async () => {
    if (!mapCode) return;

    setLoading(true);
    setError(null);
    try {
      const result = await mapsAPI.getMapDetails(mapCode);
      setData(result);
    } catch (err) {
      setError(err as APIError);
    } finally {
      setLoading(false);
    }
  }, [mapCode]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

/**
 * Hook to search maps
 */
export function useMapSearch() {
  const [data, setData] = useState<MapData[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | Error | null>(null);

  const search = useCallback(async (query: string, limit?: number) => {
    setLoading(true);
    setError(null);
    try {
      const results = await mapsAPI.searchMaps(query, limit);
      setData(results);
      return results;
    } catch (err) {
      setError(err as APIError);
      setData([]);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, search };
}

