"use client";
import TradingViewWidget from "../../components/TradingViewWidget";
import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import axios from "axios";
import Link from "next/link"; // <--- Import Link
import { 
  LayoutDashboard, 
  Activity, 
  Zap, 
  Settings, 
  LogOut, 
  Plus,
  Terminal,
  TrendingUp,
  Wallet,
  Server,
  ShoppingCart // <--- Import ShoppingCart Icon
} from "lucide-react";

import StrategyBuilder from "../../components/StrategyBuilder";
import BrokerConfig from "../../components/BrokerConfig"; // Import Broker Config

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("builder"); // <--- Set default to 'builder' so you see buttons first
  const [isBuilderOpen, setIsBuilderOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const handleStrategyCreated = () => {
    setIsBuilderOpen(false);
    setRefreshTrigger(prev => prev + 1);
  };

  return (
    <div className="flex h-screen bg-background text-text-main overflow-hidden font-sans">
      
      {/* --- SIDEBAR --- */}
      <motion.div 
        initial={{ x: -100 }}
        animate={{ x: 0 }}
        className="w-64 bg-surface border-r border-border flex flex-col justify-between"
      >
        <div>
          {/* Logo Area */}
          <Link href="/">
            <div className="p-6 flex items-center gap-2 text-primary font-bold text-xl tracking-tighter cursor-pointer hover:opacity-80 transition">
              <div className="p-1.5 bg-primary/10 rounded-lg border border-primary/20">
                <Terminal className="w-5 h-5" />
              </div>
              TradeMatrix
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="mt-6 px-4 space-y-2">
            <NavItem 
              icon={<LayoutDashboard />} 
              label="Overview" 
              active={activeTab === "overview"} 
              onClick={() => setActiveTab("overview")} 
            />
            <NavItem 
              icon={<Zap />} 
              label="Algo Builder" 
              active={activeTab === "builder"} 
              onClick={() => setActiveTab("builder")} 
            />
            <NavItem 
              icon={<Activity />} 
              label="Live Positions" 
              active={activeTab === "positions"} 
              onClick={() => setActiveTab("positions")} 
            />
            <NavItem 
              icon={<Settings />} 
              label="Broker Config" 
              active={activeTab === "settings"} 
              onClick={() => setActiveTab("settings")} 
            />

            {/* MARKETPLACE LINK (New) */}
            <div className="pt-4 mt-4 border-t border-border">
              <Link href="/marketplace">
                <button className="flex items-center gap-3 w-full px-4 py-3 rounded-lg text-text-dim hover:bg-surface-hover hover:text-white transition group">
                   <ShoppingCart size={20} className="group-hover:text-yellow-400 transition-colors" />
                   <span className="font-medium text-sm">Marketplace</span>
                </button>
              </Link>
            </div>
          </nav>
        </div>

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-border">
          <div className="mb-4 px-4 py-3 bg-surface-hover rounded-xl border border-border">
             <div className="text-xs text-text-dim mb-1">Total P&L (Today)</div>
             <div className="text-primary font-mono font-bold text-lg">+₹0.00</div>
          </div>
          <button className="flex items-center gap-3 text-text-dim hover:text-danger transition w-full px-4 py-3 rounded-lg hover:bg-surface-hover">
            <LogOut className="w-5 h-5" />
            <span className="font-medium">Disconnect</span>
          </button>
        </div>
      </motion.div>

      {/* --- MAIN CONTENT AREA --- */}
      <div className="flex-1 flex flex-col relative z-0 overflow-hidden">
        
        {/* Top Header */}
        <header className="h-16 border-b border-border bg-surface/50 backdrop-blur-md flex items-center justify-between px-8">
          <div className="flex items-center gap-4">
             <div className="flex flex-col">
                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                  NSE Derivative Engine
                  <span className="px-2 py-0.5 rounded text-[10px] bg-primary/20 text-primary border border-primary/30">LIVE</span>
                </h2>
                <div className="flex items-center gap-2 text-xs text-text-dim font-mono">
                   <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
                   MARKET OPEN • NIFTY: <span className="text-white">21,456.30</span>
                </div>
             </div>
          </div>
          
          <div className="flex items-center gap-6">
             <div className="flex items-center gap-2 px-3 py-1.5 bg-surface border border-border rounded-full text-xs font-mono text-text-dim">
                <Server className="w-3 h-3 text-primary" />
                System: Online
             </div>
             
             <div className="flex items-center gap-3 border-l border-border pl-6">
                <div className="text-right hidden md:block">
                   <div className="text-sm text-white font-medium">Kuljeet Singh</div>
                   <div className="text-xs text-text-dim">Pro Plan</div>
                </div>
                <div className="w-9 h-9 rounded-full bg-gradient-to-tr from-primary to-blue-500 border-2 border-surface shadow-lg"></div>
             </div>
          </div>
        </header>

        {/* Workspace Canvas */}
        <main className="flex-1 overflow-y-auto p-8 bg-background relative">
           <div className="absolute inset-0 bg-[linear-gradient(to_right,#1a1a1a_1px,transparent_1px),linear-gradient(to_bottom,#1a1a1a_1px,transparent_1px)] bg-[size:2rem_2rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-10 pointer-events-none" />

           <div className="relative z-10">
              {activeTab === "builder" && (
                <AlgoBuilderView 
                  onOpenBuilder={() => setIsBuilderOpen(true)} 
                  refreshTrigger={refreshTrigger}
                />
              )}
              
              {activeTab === "overview" && (
  <div className="h-[80vh] flex flex-col gap-6">
     <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white">Market Overview</h1>
          <p className="text-text-dim">Real-time charting and technical analysis.</p>
        </div>
        {/* Quick Chips */}
        <div className="flex gap-2">
           <span className="px-3 py-1 bg-green-500/10 text-green-500 border border-green-500/20 rounded text-xs font-mono">NIFTY: Bullish</span>
           <span className="px-3 py-1 bg-red-500/10 text-red-500 border border-red-500/20 rounded text-xs font-mono">VIX: 13.2</span>
        </div>
     </div>
     
     {/* THE CHART */}
     <div className="flex-1 min-h-[500px]">
        <TradingViewWidget />
     </div>
  </div>
)}
              {activeTab === "positions" && <PlaceholderView title="Live Positions" />}
              {activeTab === "settings" && <BrokerConfig />} 
           </div>
           
           {isBuilderOpen && (
             <StrategyBuilder onClose={handleStrategyCreated} />
           )}
        </main>
      </div>
    </div>
  );
}

// --- SUB COMPONENTS ---

function NavItem({ icon, label, active, onClick }: any) {
  return (
    <button 
      onClick={onClick}
      className={`flex items-center gap-3 w-full px-4 py-3 rounded-lg transition-all group ${
        active 
          ? "bg-primary/10 text-primary border border-primary/20 shadow-[0_0_15px_rgba(0,227,150,0.1)]" 
          : "text-text-dim hover:bg-surface-hover hover:text-white border border-transparent"
      }`}
    >
      <div className={`transition-transform group-hover:scale-110 ${active ? "text-primary" : "text-text-dim group-hover:text-white"}`}>
        {React.cloneElement(icon, { size: 20 })}
      </div>
      <span className="font-medium text-sm">{label}</span>
      {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" />}
    </button>
  );
}

// --- ALGO BUILDER VIEW (With Live Logs) ---
import { Play, Square, Terminal as TerminalIcon } from "lucide-react";

interface Strategy {
  id: number;
  name: string;
  symbol: string;
  timeframe: string;
  conditions: any[];
  is_running: boolean;
}

function AlgoBuilderView({ onOpenBuilder, refreshTrigger }: { onOpenBuilder: () => void, refreshTrigger: number }) {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeLogs, setActiveLogs] = useState<string[]>([]);
  const [selectedStrategyId, setSelectedStrategyId] = useState<number | null>(null);

  const fetchStrategies = async () => {
    try {
      setLoading(true);
      const response = await axios.get("http://127.0.0.1:8000/api/v1/strategy/list");
      setStrategies(response.data);
    } catch (error) {
      console.error("Failed to fetch strategies", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchStrategies(); }, [refreshTrigger]);

  // Log Polling
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (selectedStrategyId) {
      interval = setInterval(async () => {
        try {
          const res = await axios.get(`http://127.0.0.1:8000/api/v1/execution/logs/${selectedStrategyId}`);
          if (res.data.logs) setActiveLogs(res.data.logs.reverse());
        } catch (e) { console.error(e); }
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [selectedStrategyId]);

  const toggleStrategy = async (id: number, currentStatus: boolean, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      if (currentStatus) {
        await axios.post(`http://127.0.0.1:8000/api/v1/execution/stop/${id}`);
        setSelectedStrategyId(null);
      } else {
        await axios.post(`http://127.0.0.1:8000/api/v1/execution/start/${id}`);
        setSelectedStrategyId(id);
      }
      fetchStrategies();
    } catch (error) {
      alert("Failed to toggle strategy. Check Backend Connection.");
    }
  };

  return (
    <div className="max-w-6xl mx-auto flex gap-6">
       <div className="flex-1">
         <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Strategy Builder</h1>
              <p className="text-text-dim">Your deployed algorithms running on the High-Frequency Engine.</p>
            </div>
            <button 
              onClick={onOpenBuilder}
              className="flex items-center gap-2 bg-primary text-black px-6 py-2.5 rounded-lg font-bold hover:bg-emerald-400 transition shadow-[0_0_20px_rgba(0,227,150,0.2)] hover:shadow-[0_0_30px_rgba(0,227,150,0.4)]"
            >
               <Plus className="w-5 h-5" /> New Strategy
            </button>
         </div>

         {!loading && strategies.length === 0 && (
           <div className="text-center py-20 border border-dashed border-border rounded-xl bg-surface/20">
             <Zap className="w-12 h-12 text-text-dim mx-auto mb-4 opacity-50" />
             <p className="text-text-dim text-lg">No strategies deployed yet.</p>
             <p className="text-sm text-gray-600">Click "New Strategy" to create your first bot.</p>
           </div>
         )}

         <div className="space-y-4">
            {strategies.map((strat) => (
              <div 
                key={strat.id} 
                onClick={() => setSelectedStrategyId(strat.id)}
                className={`bg-surface border p-6 rounded-xl transition cursor-pointer relative overflow-hidden group ${
                  selectedStrategyId === strat.id ? "border-primary" : "border-border hover:border-primary/50"
                }`}
              >
                 <div className="flex justify-between items-center relative z-10">
                    <div>
                      <h3 className="text-xl font-bold text-white mb-1 capitalize flex items-center gap-2">
                        {strat.name}
                        {strat.is_running && <span className="text-[10px] bg-green-500 text-black px-2 py-0.5 rounded font-bold animate-pulse">RUNNING</span>}
                      </h3>
                      <div className="text-text-dim text-sm font-mono flex gap-2">
                        <span>{strat.symbol}</span> • <span>{strat.timeframe}</span> • <span>{strat.conditions.length} Conditions</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => toggleStrategy(strat.id, strat.is_running, e)}
                      className={`p-3 rounded-full transition shadow-lg flex items-center justify-center ${
                        strat.is_running 
                          ? "bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white" 
                          : "bg-primary/10 text-primary hover:bg-primary hover:text-black"
                      }`}
                      title={strat.is_running ? "Stop Strategy" : "Start Strategy"}
                    >
                      {strat.is_running ? <Square fill="currentColor" size={18} /> : <Play fill="currentColor" size={18} />}
                    </button>
                 </div>
              </div>
            ))}
         </div>
       </div>

       {selectedStrategyId && (
         <div className="w-[400px] h-[600px] bg-[#0c0c0c] border border-border rounded-xl overflow-hidden flex flex-col shadow-2xl sticky top-8">
            <div className="bg-surface border-b border-border p-3 flex items-center gap-2 text-text-dim text-xs font-mono">
              <TerminalIcon size={14} /> Execution Logs
            </div>
            <div className="flex-1 p-4 overflow-y-auto font-mono text-[10px] space-y-2 custom-scrollbar">
               <div className="flex gap-2 mb-4 justify-end">
                  <div className="w-2 h-2 rounded-full bg-red-500"/>
                  <div className="w-2 h-2 rounded-full bg-yellow-500"/>
                  <div className="w-2 h-2 rounded-full bg-green-500"/>
               </div>
               {activeLogs.length === 0 ? (
                 <div className="text-gray-600 italic">Waiting for market data...</div>
               ) : (
                 activeLogs.map((log, i) => (
                   <div key={i} className="border-b border-white/5 pb-1">
                     <span className="text-gray-500 opacity-50">[{log.split(']')[0].replace('[','')}</span> 
                     <span className={`ml-2 ${
                        log.includes("BUY") ? "text-green-400 font-bold" : 
                        log.includes("SELL") ? "text-red-400 font-bold" : 
                        log.includes("SIGNAL") ? "text-yellow-400" :
                        "text-gray-300"
                     }`}>
                       {log.split(']')[1]}
                     </span>
                   </div>
                 ))
               )}
            </div>
         </div>
       )}
    </div>
  );
}

function PlaceholderView({ title }: { title: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-[60vh] text-center opacity-50">
      <div className="bg-surface p-6 rounded-full border border-border mb-4">
        <Settings className="w-10 h-10 text-text-dim" />
      </div>
      <h2 className="text-2xl font-bold text-white mb-2">{title}</h2>
      <p className="text-text-dim max-w-md">This module is currently under construction. Connect Broker API to enable live data.</p>
    </div>
  );
}