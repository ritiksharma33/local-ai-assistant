import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { Activity, Clock, Zap, Database, Terminal, ShieldAlert, Cpu } from 'lucide-react';
import { AI_API } from '../services/api';

export default function TelemetryDashboard() {
  const [rawRecords, setRawRecords] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTelemetry = async () => {
      try {
        const rawData = await AI_API.getTelemetry();
        // Keep chronological order for the history table
        setRawRecords(rawData);

        // Reverse the array clone so time travels left-to-right on charts
        const formattedData = [...rawData].reverse().map(record => ({
          ...record,
          timeStr: new Date(record.timestamp).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit' 
          })
        }));
        setChartData(formattedData);
      } catch (error) {
        console.error("Failed to fetch telemetry:", error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 10000);
    return () => clearInterval(interval);
  }, []);

  // Structural aggregates
  const totalRequests = rawRecords.length;
  
  const modelBreakdown = rawRecords.reduce((acc, curr) => {
    acc[curr.model_used] = (acc[curr.model_used] || 0) + 1;
    return acc;
  }, {});

  const standardOrAgentRuns = rawRecords.filter(d => 
    d.endpoint_type === 'standard' || d.endpoint_type === 'agent'
  );

  const avgSpeed = standardOrAgentRuns.length 
    ? (standardOrAgentRuns.reduce((acc, curr) => acc + curr.tokens_per_second, 0) / standardOrAgentRuns.length).toFixed(1)
    : "Stream Latent";

  const avgLatency = standardOrAgentRuns.length 
    ? (standardOrAgentRuns.reduce((acc, curr) => acc + curr.total_time_seconds, 0) / standardOrAgentRuns.length).toFixed(2)
    : "Stream Live";

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center bg-[#0f172a] text-slate-400">
        <div className="flex flex-col items-center gap-2">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
          <span className="text-sm font-mono">Syncing internal SQLite memory logs...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-8 bg-[#0f172a]">
      
      {/* Title Header */}
      <div className="flex items-center justify-between border-b border-slate-800 pb-6 mb-8">
        <div className="flex items-center gap-3">
          <Database className="w-8 h-8 text-purple-500" />
          <div>
            <h2 className="text-2xl font-bold text-white tracking-tight">System Telemetry</h2>
            <p className="text-slate-400 text-sm font-mono">Hardware core layer optimization logs</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-xs font-medium text-emerald-400 font-mono">Active Guardrail Listening</span>
        </div>
      </div>

      {/* Metric Grid Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-5 mb-8">
        <div className="bg-slate-900/50 border border-slate-800/80 p-5 rounded-xl shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-xl"><Activity className="w-5 h-5 text-blue-400" /></div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Transaction Pool</p>
            <p className="text-2xl font-bold text-white">{totalRequests} <span className="text-xs text-slate-400 font-normal">inferences</span></p>
          </div>
        </div>
        
        <div className="bg-slate-900/50 border border-slate-800/80 p-5 rounded-xl shadow-sm flex items-center gap-4">
          <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-xl"><Zap className="w-5 h-5 text-emerald-400" /></div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Static Engine Speed</p>
            <p className="text-2xl font-bold text-white">{avgSpeed} {typeof avgSpeed === 'number' && <span className="text-xs text-slate-400 font-normal">t/s</span>}</p>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/80 p-5 rounded-xl shadow-sm flex items-center gap-4">
          <div className="p-3 bg-orange-500/10 border border-orange-500/20 rounded-xl"><Clock className="w-5 h-5 text-orange-400" /></div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Static Latency</p>
            <p className="text-2xl font-bold text-white">{avgLatency} {typeof avgLatency === 'number' && <span className="text-xs text-slate-400 font-normal">sec</span>}</p>
          </div>
        </div>

        <div className="bg-slate-900/50 border border-slate-800/80 p-5 rounded-xl shadow-sm flex items-center gap-4">
          <div className="p-3 bg-purple-500/10 border border-purple-500/20 rounded-xl"><Cpu className="w-5 h-5 text-purple-400" /></div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Primary Model Client</p>
            <p className="text-lg font-bold text-white truncate max-w-[160px]">
              {Object.keys(modelBreakdown).reduce((a, b) => modelBreakdown[a] > modelBreakdown[b] ? a : b, "None")}
            </p>
          </div>
        </div>
      </div>

      {/* Chart Grid Profiles */}
      <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 mb-8">
        <div className="bg-slate-900/30 border border-slate-800 p-5 rounded-xl">
          <h3 className="text-sm font-semibold text-slate-300 font-mono uppercase tracking-wider mb-4">Throughput (Tokens/sec)</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorSpeed" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="timeStr" stroke="#475569" fontSize={11} tickMargin={8} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} />
                <Area type="monotone" dataKey="tokens_per_second" name="Tokens/Sec" stroke="#10b981" strokeWidth={2.5} fillOpacity={1} fill="url(#colorSpeed)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-slate-900/30 border border-slate-800 p-5 rounded-xl">
          <h3 className="text-sm font-semibold text-slate-300 font-mono uppercase tracking-wider mb-4">Pipeline Latency Prototyping</h3>
          <div className="h-60">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="timeStr" stroke="#475569" fontSize={11} tickMargin={8} />
                <YAxis stroke="#475569" fontSize={11} />
                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }} />
                <Line type="monotone" dataKey="total_time_seconds" name="Latency (s)" stroke="#f97316" strokeWidth={2.5} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Target Instance Historical Log Table */}
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
        <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/80 flex items-center gap-2">
          <Terminal className="w-4 h-4 text-slate-400" />
          <h3 className="text-sm font-semibold text-slate-200 font-mono uppercase tracking-wider">Stored Database Instances (Inference History)</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-500 font-mono text-xs uppercase bg-slate-900/20">
                <th className="py-3 px-6">ID</th>
                <th className="py-3 px-6">Timestamp</th>
                <th className="py-3 px-6">Pipeline Target</th>
                <th className="py-3 px-6">Model Signature</th>
                <th className="py-3 px-6 text-center">Prompt Size</th>
                <th className="py-3 px-6 text-right">Metrics Profile</th>
                <th className="py-3 px-6 text-right">Execution Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-sm">
              {rawRecords.map((record) => (
                <tr key={record.id} className="hover:bg-slate-800/30 transition-colors group">
                  <td className="py-3.5 px-6 font-bold text-slate-600 group-hover:text-slate-400">{record.id}</td>
                  <td className="py-3.5 px-6 text-slate-400 text-xs">
                    {new Date(record.timestamp).toLocaleString()}
                  </td>
                  <td className="py-3.5 px-6">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-semibold tracking-wide ${
                      record.endpoint_type === 'stream' ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20' :
                      record.endpoint_type === 'agent' ? 'bg-purple-500/10 text-purple-400 border border-purple-500/20' :
                      record.endpoint_type === 'structured' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
                      'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    }`}>
                      {record.endpoint_type}
                    </span>
                  </td>
                  <td className="py-3.5 px-6 font-medium text-slate-300">{record.model_used}</td>
                  <td className="py-3.5 px-6 text-center text-slate-400">{record.prompt_length} <span className="text-xs text-slate-600">chars</span></td>
                  <td className="py-3.5 px-6 text-right text-xs">
                    {record.endpoint_type === 'stream' ? (
                      <span className="text-slate-500 italic">Streaming Active Socket</span>
                    ) : (
                      <span className="text-slate-300">
                        {record.tokens_per_second} t/s | {record.total_time_seconds}s
                      </span>
                    )}
                  </td>
                  <td className="py-3.5 px-6 text-right">
                    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold ${
                      record.execution_status.includes('SUCCESS') ? 'text-emerald-400' :
                      record.execution_status.includes('STARTED') ? 'text-blue-400' : 'text-rose-400'
                    }`}>
                      {!record.execution_status.includes('SUCCESS') && !record.execution_status.includes('STARTED') && (
                        <ShieldAlert className="w-3.5 h-3.5" />
                      )}
                      {record.execution_status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}