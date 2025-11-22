"use client"

import { useState, useEffect } from "react";
import { healthAPI, chatAPI, analyticsAPI } from "@/lib/api-client";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { CheckCircle2, XCircle, Loader2, AlertCircle } from "lucide-react";

export default function ConnectionTest() {
  const [tests, setTests] = useState({
    backend: { status: 'pending', message: '' },
    chat: { status: 'pending', message: '' },
    models: { status: 'pending', message: '' },
  });

  const runTests = async () => {
    // Reset
    setTests({
      backend: { status: 'loading', message: 'Testing...' },
      chat: { status: 'pending', message: '' },
      models: { status: 'pending', message: '' },
    });

    // Test 1: Backend Health
    try {
      const health = await healthAPI.check();
      setTests(prev => ({
        ...prev,
        backend: { status: 'success', message: `✓ Backend is healthy (${health.version || 'v1'})` }
      }));
    } catch (error) {
      setTests(prev => ({
        ...prev,
        backend: { status: 'error', message: `✗ Backend unreachable: ${error instanceof Error ? error.message : 'Unknown error'}` }
      }));
      return; // Stop if backend is down
    }

    // Test 2: Chat Service
    setTests(prev => ({
      ...prev,
      chat: { status: 'loading', message: 'Testing...' }
    }));

    try {
      const chatHealth = await chatAPI.checkHealth();
      setTests(prev => ({
        ...prev,
        chat: { status: 'success', message: `✓ Chat service ready (Gemini: ${chatHealth.gemini_available ? 'Available' : 'Unavailable'})` }
      }));
    } catch (error) {
      setTests(prev => ({
        ...prev,
        chat: { status: 'error', message: `✗ Chat service error: ${error instanceof Error ? error.message : 'Unknown error'}` }
      }));
    }

    // Test 3: ML Models
    setTests(prev => ({
      ...prev,
      models: { status: 'loading', message: 'Testing...' }
    }));

    try {
      const modelInfo = await analyticsAPI.getModelInfo();
      const loadedModels = Object.entries(modelInfo).filter(([_, loaded]) => loaded).map(([name]) => name);
      setTests(prev => ({
        ...prev,
        models: { status: 'success', message: `✓ ${loadedModels.length} models loaded: ${loadedModels.join(', ')}` }
      }));
    } catch (error) {
      setTests(prev => ({
        ...prev,
        models: { status: 'error', message: `✗ Models error: ${error instanceof Error ? error.message : 'Unknown error'}` }
      }));
    }
  };

  useEffect(() => {
    runTests();
  }, []);

  const getIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle2 className="w-5 h-5 text-green-400" />;
      case 'error': return <XCircle className="w-5 h-5 text-red-400" />;
      case 'loading': return <Loader2 className="w-5 h-5 text-brand-400 animate-spin" />;
      default: return <AlertCircle className="w-5 h-5 text-slate-400" />;
    }
  };

  const allPassed = Object.values(tests).every(t => t.status === 'success');

  return (
    <div className="min-h-screen bg-slate-950 text-white p-8">
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold">Connection Test</h1>
          <p className="text-slate-400">Testing Project Harvest API connectivity</p>
        </div>

        <Card className="bg-slate-900 border-slate-800 p-6 space-y-4">
          {Object.entries(tests).map(([key, test]) => (
            <div key={key} className="flex items-center gap-3 p-3 rounded-lg bg-slate-800/50">
              {getIcon(test.status)}
              <div className="flex-1">
                <p className="font-medium capitalize">{key} Service</p>
                <p className="text-sm text-slate-400">{test.message}</p>
              </div>
            </div>
          ))}
        </Card>

        <div className="flex items-center justify-center gap-4">
          <Button onClick={runTests} className="bg-brand-600 hover:bg-brand-700">
            Retry Tests
          </Button>
          {allPassed && (
            <Button
              onClick={() => window.location.href = '/analyzer'}
              className="bg-green-600 hover:bg-green-700"
            >
              Go to Analyzer →
            </Button>
          )}
        </div>

        {!allPassed && (
          <Card className="bg-yellow-500/10 border-yellow-500/30 p-4">
            <div className="flex gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-2">
                <p className="font-medium text-yellow-200">Troubleshooting Tips:</p>
                <ul className="text-sm text-yellow-100/80 space-y-1 list-disc list-inside">
                  <li>Make sure the backend is running: <code className="bg-slate-900/50 px-1 rounded">python -m uvicorn app.main:app --host 127.0.0.1 --port 8000</code></li>
                  <li>Check that <code className="bg-slate-900/50 px-1 rounded">NEXT_PUBLIC_API_URL</code> is set in <code className="bg-slate-900/50 px-1 rounded">.env.local</code></li>
                  <li>Verify Gemini API key is set in backend <code className="bg-slate-900/50 px-1 rounded">.env</code></li>
                  <li>Check console for detailed error messages</li>
                </ul>
              </div>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}

