const BASE_URL = 'http://127.0.0.1:8000/api/v1';

export const AI_API = {
  // Standard text generation
  generateText: async (prompt, model = 'llama3.2') => {
    const response = await fetch(`${BASE_URL}/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, model, temperature: 0.7 })
    });
    return response.json();
  },

  // Agentic Tool Loop
  runAgent: async (prompt, model = 'llama3.2') => {
    const response = await fetch(`${BASE_URL}/agent/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, model, temperature: 0.1 })
    });
    return response.json();
  },

  // Fetch SQLite Telemetry Data
  getTelemetry: async () => {
    const response = await fetch(`${BASE_URL}/telemetry`);
    return response.json();
  }
};