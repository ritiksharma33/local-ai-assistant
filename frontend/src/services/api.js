const BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const AI_API = {
  // Standard text generation (Buffered)
  generateText: async (prompt, model = 'llama3.2') => {
    const response = await fetch(`${BASE_URL}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        prompt: prompt, 
        model: model, 
        temperature: 0.7 
      })
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }
    return response.json();
  },

  // Agentic Tool Loop
  runAgent: async (prompt, model = 'llama3.2') => {
    const response = await fetch(`${BASE_URL}/agent/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        prompt: prompt, 
        model: model, 
        temperature: 0.1 
      })
    });
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${response.status}`);
    }
    return response.json();
  },

  // Fetch SQLite Telemetry Data
  getTelemetry: async () => {
    const response = await fetch(`${BASE_URL}/telemetry`);
    if (!response.ok) throw new Error(`Failed to fetch telemetry: ${response.status}`);
    return response.json();
  }
};