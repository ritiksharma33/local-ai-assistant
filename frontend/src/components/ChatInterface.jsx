import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Zap, Sparkles, ServerCog } from 'lucide-react';
import { AI_API } from '../services/api';
import ReactMarkdown from 'react-markdown'; // <-- This was the missing piece!

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I am your local Llama 3.2 agent. How can I help you today?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState('stream');

  const messagesEndRef = useRef(null);
  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => scrollToBottom(), [messages]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);

    try {
      if (mode === 'standard') {
        const data = await AI_API.generateText(userMessage);
        setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
      } 
      else if (mode === 'agent') {
        const data = await AI_API.runAgent(userMessage);
        setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
      } 
      else if (mode === 'stream') {
        setMessages((prev) => [...prev, { role: 'assistant', content: '' }]);
        
        const response = await fetch('http://127.0.0.1:8000/api/v1/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ prompt: userMessage, model: 'llama3.2', temperature: 0.7 })
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let done = false;

       while (!done) {
          const { value, done: readerDone } = await reader.read();
          done = readerDone;
          if (value) {
            const chunk = decoder.decode(value, { stream: true });
            
            setMessages((prev) => {
              const newMessages = [...prev];
              const lastIndex = newMessages.length - 1;
              
              // Create a completely new object for the last message
              newMessages[lastIndex] = {
                ...newMessages[lastIndex],
                content: newMessages[lastIndex].content + chunk
              };
              
              return newMessages;
            });
          }
        }
      }
    } catch (error) {
      console.error("API Error:", error);
      setMessages((prev) => [...prev, { role: 'assistant', content: `**Error:** Could not connect to local backend. (${error.message})` }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0f172a]">
      {/* Top Bar: Mode Selector */}
      <div className="flex items-center gap-2 p-4 border-b border-slate-800 bg-slate-900/50">
        <span className="text-sm font-medium text-slate-400 mr-2">Engine Mode:</span>
        <button onClick={() => setMode('stream')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${mode === 'stream' ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30' : 'text-slate-400 hover:bg-slate-800'}`}>
          <Zap className="w-4 h-4" /> Stream (Fast)
        </button>
        <button onClick={() => setMode('standard')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${mode === 'standard' ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30' : 'text-slate-400 hover:bg-slate-800'}`}>
          <ServerCog className="w-4 h-4" /> Standard (Buffered)
        </button>
        <button onClick={() => setMode('agent')} className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-sm transition-colors ${mode === 'agent' ? 'bg-purple-600/20 text-purple-400 border border-purple-500/30' : 'text-slate-400 hover:bg-slate-800'}`}>
          <Sparkles className="w-4 h-4" /> Agentic (Tools)
        </button>
      </div>

      {/* Chat History Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex gap-4 max-w-4xl mx-auto ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            
            {msg.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center shrink-0 mt-1">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}
            
            {/* Message Bubble with Markdown Parsing */}
            <div className={`px-5 py-3.5 rounded-2xl max-w-[80%] overflow-x-auto ${
              msg.role === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-slate-800 text-slate-200 border border-slate-700 shadow-sm prose prose-invert prose-sm max-w-none'
            }`}>
              {msg.role === 'user' ? (
                <div className="whitespace-pre-wrap">{msg.content}</div>
              ) : (
                <ReactMarkdown>{msg.content}</ReactMarkdown>
              )}
            </div>

            {msg.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center shrink-0 mt-1">
                <User className="w-5 h-5 text-white" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 bg-slate-900 border-t border-slate-800">
        <form onSubmit={handleSend} className="max-w-4xl mx-auto relative">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
            placeholder={isLoading ? "Llama 3.2 is thinking..." : "Send a message to your local agent..."}
            className="w-full bg-slate-800 border border-slate-700 text-white rounded-xl pl-4 pr-12 py-4 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 transition-all"
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="absolute right-2 top-2 bottom-2 bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 text-white p-2 rounded-lg transition-colors flex items-center justify-center"
          >
            <Send className="w-5 h-5" />
          </button>
        </form>
      </div>
    </div>
  );
}