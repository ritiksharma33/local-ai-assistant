import React from 'react';
import { MessageSquare, Activity, Cpu } from 'lucide-react';

export default function Sidebar({ currentView, setCurrentView }) {
  return (
    // A fixed-width sidebar with a deep dark background and a subtle right border
    <div className="w-64 h-screen bg-slate-900 border-r border-slate-800 flex flex-col">
      
      {/* App Header / Logo Area */}
      <div className="p-6 flex items-center gap-3 border-b border-slate-800">
        <Cpu className="w-6 h-6 text-blue-500" />
        <h1 className="text-lg font-bold text-slate-100">Local AI Agent</h1>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-4 space-y-2">
        {/* Chat Button */}
        <button
          onClick={() => setCurrentView('chat')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            currentView === 'chat' 
              ? 'bg-blue-600 text-white' // Active state styling
              : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200' // Inactive state styling
          }`}
        >
          <MessageSquare className="w-5 h-5" />
          <span className="font-medium">Workspace</span>
        </button>

        {/* Telemetry Button */}
        <button
          onClick={() => setCurrentView('telemetry')}
          className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
            currentView === 'telemetry' 
              ? 'bg-blue-600 text-white' 
              : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
          }`}
        >
          <Activity className="w-5 h-5" />
          <span className="font-medium">Telemetry</span>
        </button>
      </nav>

      {/* Bottom Footer Area */}
      <div className="p-4 border-t border-slate-800 text-sm text-slate-500 text-center">
        M1 Accelerated • Llama 3.2
      </div>
    </div>
  );
}