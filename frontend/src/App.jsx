import { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import TelemetryDashboard from './components/TelemetryDashboard';

export default function App() {
  const [currentView, setCurrentView] = useState('chat');

  return (
    <div className="flex h-screen bg-[#0f172a] text-slate-50 overflow-hidden">
      
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        
        {/* Chat Interface - Always mounted, but hidden if not active */}
        <div className={`h-full w-full ${currentView === 'chat' ? 'block' : 'hidden'}`}>
          <ChatInterface />
        </div>

        {/* Telemetry Dashboar - Always mounted, but hidden if not active */}
        <div className={`h-full w-full ${currentView === 'telemetry' ? 'block' : 'hidden'}`}>
          <TelemetryDashboard />
        </div>

      </main>
      
    </div>
  );
}