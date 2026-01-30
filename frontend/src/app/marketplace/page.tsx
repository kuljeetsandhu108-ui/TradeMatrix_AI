"use client";

import React from "react";
import { motion } from "framer-motion";
import { Search, Filter, TrendingUp, ShoppingCart, Star, Check, Copy } from "lucide-react";
import Link from "next/link";
import axios from "axios";

// Fake "Premium" Data for the Marketplace
const MARKET_STRATEGIES = [
  {
    id: 101,
    name: "Nifty Alpha Prime",
    author: "QuantMaster",
    roi: "+145%",
    winRate: "72%",
    price: "₹4,999/mo",
    desc: "Aggressive trend-following system using triple EMA crossover on 15m timeframe.",
    tags: ["NIFTY", "High Risk", "Trend"],
    subscribers: 1240
  },
  {
    id: 102,
    name: "BankNifty Sniper",
    author: "AlgoWiz",
    roi: "+88%",
    winRate: "65%",
    price: "₹2,499/mo",
    desc: "Scalping bot designed for volatility. Uses RSI divergence and Bollinger Bands.",
    tags: ["BANKNIFTY", "Scalping", "Intraday"],
    subscribers: 856
  },
  {
    id: 103,
    name: "SafeGuard Options",
    author: "HedgeFundAI",
    roi: "+22%",
    winRate: "94%",
    price: "₹9,999/mo",
    desc: "Delta-neutral option selling strategy. Low drawdown, consistent weekly returns.",
    tags: ["FINNIFTY", "Hedging", "Low Risk"],
    subscribers: 2100
  }
];

export default function Marketplace() {
  const [cloningId, setCloningId] = React.useState<number | null>(null);

  const handleSubscribe = async (strat: any) => {
    setCloningId(strat.id);
    
    // Simulate API Call to clone strategy
    try {
      // In a real app, this would verify payment, then copy the strat to the user's DB
      const payload = {
        name: `${strat.name} (Copy)`,
        symbol: strat.tags[0] === "NIFTY" ? "NIFTY 50" : "BANKNIFTY",
        timeframe: "15m",
        conditions: [], // We would copy real logic here
        user_id: 1
      };
      
      await axios.post("http://127.0.0.1:8000/api/v1/strategy/create", payload);
      
      alert(`Successfully subscribed to ${strat.name}! It is now in your Dashboard.`);
    } catch (e) {
      alert("Failed to subscribe.");
    } finally {
      setCloningId(null);
    }
  };

  return (
    <div className="min-h-screen bg-background text-text-main font-sans selection:bg-primary selection:text-black">
      
      {/* Navbar */}
      <nav className="border-b border-border bg-surface/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link href="/" className="font-bold text-xl text-white tracking-tighter flex items-center gap-2">
             <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center text-black font-bold text-xs">TM</div>
             TradeMatrix <span className="text-primary">Market</span>
          </Link>
          <div className="flex gap-4">
            <Link href="/dashboard">
              <button className="text-sm font-medium hover:text-white transition">Dashboard</button>
            </Link>
            <button className="bg-white text-black px-4 py-2 rounded-lg text-sm font-bold hover:bg-gray-200 transition">
              Sign In
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-12">
        
        {/* Hero Section */}
        <div className="text-center mb-16">
          <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
            Discover Alpha. <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-blue-500">Automated.</span>
          </h1>
          <p className="text-xl text-text-dim max-w-2xl mx-auto mb-8">
            Browse verified strategies from top quant developers. Subscribe and execute instantly on your broker account.
          </p>
          
          {/* Search Bar */}
          <div className="max-w-xl mx-auto relative group">
            <div className="absolute inset-0 bg-primary/20 blur-xl rounded-full group-hover:bg-primary/30 transition duration-500" />
            <div className="relative bg-surface border border-border rounded-full flex items-center px-4 py-3 shadow-2xl">
              <Search className="text-text-dim w-5 h-5" />
              <input 
                type="text" 
                placeholder="Search strategies (e.g. 'Nifty Scalper')..." 
                className="bg-transparent border-none outline-none flex-1 px-4 text-white placeholder:text-gray-600"
              />
              <button className="p-2 bg-[#2A2A2A] rounded-full hover:bg-primary hover:text-black transition">
                <Filter size={16} />
              </button>
            </div>
          </div>
        </div>

        {/* Strategy Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {MARKET_STRATEGIES.map((strat) => (
            <motion.div 
              key={strat.id}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="bg-surface border border-border rounded-2xl p-6 hover:border-primary/50 transition group relative overflow-hidden flex flex-col"
            >
              {/* Top Badge */}
              <div className="flex justify-between items-start mb-6">
                 <div className="flex gap-2">
                   {strat.tags.map(tag => (
                     <span key={tag} className="text-[10px] uppercase font-bold tracking-wider bg-white/5 border border-white/10 px-2 py-1 rounded text-text-dim">
                       {tag}
                     </span>
                   ))}
                 </div>
                 <div className="flex items-center gap-1 text-yellow-500 text-xs font-bold">
                   <Star fill="currentColor" size={12} /> 4.9
                 </div>
              </div>

              {/* Title & Stats */}
              <h3 className="text-2xl font-bold text-white mb-2">{strat.name}</h3>
              <div className="text-sm text-text-dim mb-6 flex items-center gap-2">
                by <span className="text-white border-b border-dotted border-gray-500">{strat.author}</span>
                <Check size={12} className="bg-blue-500 text-white rounded-full p-[2px]" />
              </div>

              {/* Performance Metrics */}
              <div className="grid grid-cols-2 gap-4 mb-6 p-4 bg-background rounded-xl border border-border">
                <div>
                  <div className="text-xs text-text-dim mb-1">Total ROI</div>
                  <div className="text-xl font-bold text-green-500">{strat.roi}</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-text-dim mb-1">Win Rate</div>
                  <div className="text-xl font-bold text-white">{strat.winRate}</div>
                </div>
              </div>

              <p className="text-text-dim text-sm leading-relaxed mb-8 flex-1">
                {strat.desc}
              </p>

              {/* Footer / Action */}
              <div className="flex items-center justify-between border-t border-border pt-6 mt-auto">
                <div>
                  <div className="text-xs text-text-dim line-through decoration-red-500">₹6,000</div>
                  <div className="text-lg font-bold text-white">{strat.price}</div>
                </div>
                
                <button 
                  onClick={() => handleSubscribe(strat)}
                  disabled={cloningId === strat.id}
                  className="bg-white text-black px-6 py-2.5 rounded-lg font-bold hover:bg-primary transition flex items-center gap-2"
                >
                  {cloningId === strat.id ? (
                     "Cloning..."
                  ) : (
                     <>
                       <Copy size={16} /> Subscribe
                     </>
                  )}
                </button>
              </div>

            </motion.div>
          ))}
        </div>

      </main>
    </div>
  );
}