import { useState } from 'react';
import Sidebar from './components/Sidebar';

// Temporary placeholder components so our app doesn't crash before we build them
const ChatPlaceholder = () => (
  <div className="flex items-center justify-center h-full text-slate-400">
    Chat Interface will go here...
  </div>
);

const TelemetryPlaceholder = () => (
  <div className="flex items-center justify-center h-full text-slate-400">
    Telemetry Dashboard will go here...
  </div>
);

export default function App() {
  // This state controls what screen the user is currently looking at
  const [currentView, setCurrentView] = useState('chat');

  return (
    // The outermost wrapper: Flexbox to put sidebar and content side-by-side
    <div className="flex h-screen bg-[#0f172a] text-slate-50 overflow-hidden">
      
      {/* Pass the state and the state-updater function to the Sidebar 
        so it knows which button to highlight and how to change screens 
      */}
      <Sidebar currentView={currentView} setCurrentView={setCurrentView} />

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative">
        {/* Conditional Rendering: Show Chat if state is 'chat', else show Telemetry */}
        {currentView === 'chat' ? <ChatPlaceholder /> : <TelemetryPlaceholder />}
      </main>
      
    </div>
  );
}