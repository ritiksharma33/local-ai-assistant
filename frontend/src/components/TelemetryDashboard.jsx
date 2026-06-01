import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, Clock, Zap, Database } from 'lucide-react';
import { AI_API } from '../services/api';

export default function TelemetryDashboard() {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch data when the dashboard mounts
  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const rawData = await AI_API.getTelemetry();
        // Reverse the array so the oldest is on the left and newest is on the right of the chart
        const formattedData = rawData.reverse().map(record => ({
          ...record,
          // Extract just the time (HH:MM:SS) for cleaner X-axis labels
          timeStr: new Date(record.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
        }));
        setData(formattedData);
      } catch (error) {
        console.error("Failed to fetch telemetry:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTelemetry();
    // Auto-refresh every 10 seconds to catch new inferences
    const interval = setInterval(fetchTelemetry, 10000);
    return () => clearInterval(interval);
  }, []);

  // Calculate top-level stats
  const successfulRuns = data.filter(d => d.execution_status.includes('SUCCESS') || d.execution_status.includes('STREAM'));
  const avgSpeed = successfulRuns.length ? (successfulRuns.reduce((acc, curr) => acc + curr.tokens_per_second, 0) / successfulRuns.length).toFixed(1) : 0;
  const avgLatency = successfulRuns.length ? (successfulRuns.reduce((acc, curr) => acc + curr.total_time_seconds, 0) / successfulRuns.length).toFixed(2) : 0;

  if (loading) {
    return <div className="flex h-full items-center justify-center text-slate-400">Loading metrics from local SQLite...</div>;
  }

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-[#0f172a]">
      
      <div className="flex items-center gap-3 mb-8">
        <Database className="w-8 h-8 text-purple-500" />
        <div>
          <h2 className="text-2xl font-bold text-white">System Telemetry</h2>
          <p className="text-slate-400 text-sm">Real-time M1 inference performance metrics</p>
        </div>
      </div>

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-blue-500/20 rounded-lg"><Activity className="w-6 h-6 text-blue-400" /></div>
          <div>
            <p className="text-sm text-slate-400">Total Inferences</p>
            <p className="text-2xl font-bold text-white">{data.length}</p>
          </div>
        </div>
        
        <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-emerald-500/20 rounded-lg"><Zap className="w-6 h-6 text-emerald-400" /></div>
          <div>
            <p className="text-sm text-slate-400">Avg Generation Speed</p>
            <p className="text-2xl font-bold text-white">{avgSpeed} <span className="text-sm text-slate-500 font-normal">t/s</span></p>
          </div>
        </div>

        <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-orange-500/20 rounded-lg"><Clock className="w-6 h-6 text-orange-400" /></div>
          <div>
            <p className="text-sm text-slate-400">Avg Roundtrip Latency</p>
            <p className="text-2xl font-bold text-white">{avgLatency} <span className="text-sm text-slate-500 font-normal">sec</span></p>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
        
        {/* Token Speed Chart */}
        <div className="bg-slate-800/30 border border-slate-700 p-6 rounded-xl">
          <h3 className="text-lg font-semibold text-white mb-6">Inference Throughput (Tokens/sec)</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorSpeed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="timeStr" stroke="#94a3b8" fontSize={12} tickMargin={10} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(val) => `${val} t/s`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#f8fafc' }}
                  itemStyle={{ color: '#10b981' }}
                />
                <Area type="monotone" dataKey="tokens_per_second" name="Speed" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorSpeed)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Latency Chart */}
        <div className="bg-slate-800/30 border border-slate-700 p-6 rounded-xl">
          <h3 className="text-lg font-semibold text-white mb-6">Execution Latency (Seconds)</h3>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="timeStr" stroke="#94a3b8" fontSize={12} tickMargin={10} />
                <YAxis stroke="#94a3b8" fontSize={12} tickFormatter={(val) => `${val}s`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#f8fafc' }}
                  itemStyle={{ color: '#f97316' }}
                />
                <Line type="monotone" dataKey="total_time_seconds" name="Latency" stroke="#f97316" strokeWidth={3} dot={{ r: 4, fill: '#f97316' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

      </div>
    </div>
  );
}