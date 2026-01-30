"use client";

import { motion } from "framer-motion";
import { ShieldCheck, Zap, ArrowRight, BarChart3 } from "lucide-react";
import React from "react";
import Link from "next/link"; // <--- Added for navigation

// --- Types Definition ---
interface CardProps {
  icon: React.ReactNode;
  title: string;
  desc: string;
}

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col items-center justify-center relative overflow-hidden bg-background selection:bg-primary selection:text-black">
      
      {/* Background Grid - The "Matrix" feel */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1a1a1a_1px,transparent_1px),linear-gradient(to_bottom,#1a1a1a_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20" />

      <div className="z-10 text-center max-w-5xl px-6">
        
        {/* Animated Status Badge */}
        <motion.div 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="inline-flex items-center space-x-2 bg-surface border border-border rounded-full px-4 py-1.5 mb-8 shadow-lg shadow-black/50"
        >
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
          </span>
          <span className="text-xs tracking-wider text-text-dim uppercase font-semibold">NSE Connectivity: Active</span>
        </motion.div>

        {/* Main Title */}
        <motion.h1 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="text-6xl md:text-8xl font-bold tracking-tighter text-white mb-6"
        >
          TradeMatrix <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-emerald-600">AI</span>
        </motion.h1>

        <motion.p 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="text-xl text-text-dim mb-10 max-w-2xl mx-auto leading-relaxed"
        >
          Deploy automated strategies on NSE directly from your browser. 
          <br /> <span className="text-primary">No Code. Zero Latency. Pure Alpha.</span>
        </motion.p>

        {/* Buttons */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="flex flex-col md:flex-row gap-4 justify-center items-center"
        >
          {/* LINKED BUTTON TO DASHBOARD */}
          <Link href="/dashboard">
            <button className="group bg-primary text-black px-8 py-4 rounded-lg font-bold text-lg hover:bg-emerald-400 transition-all flex items-center gap-2 shadow-[0_0_20px_rgba(0,227,150,0.3)] hover:shadow-[0_0_30px_rgba(0,227,150,0.5)]">
              Initialize System <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </Link>
          
          <Link href="/marketplace">
  <button className="px-8 py-4 rounded-lg font-bold text-lg text-text-dim hover:text-white transition border border-border hover:border-primary/50 hover:bg-surface-hover">
    View Marketplace
  </button>
</Link>
        </motion.div>
      </div>

      {/* Feature Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-24 z-10 max-w-6xl px-6 w-full pb-20">
        <Card 
          icon={<Zap className="text-primary" />} 
          title="No-Code Builder" 
          desc="Construct complex algo logic using a visual drag-and-drop interface." 
        />
        <Card 
          icon={<BarChart3 className="text-accent" />} 
          title="Direct Execution" 
          desc="Trades execute directly on your Broker (Fyres/Angel) via API." 
        />
        <Card 
          icon={<ShieldCheck className="text-blue-500" />} 
          title="Encrypted Vault" 
          desc="API keys are stored with military-grade AES-256 encryption." 
        />
      </div>
    </main>
  );
}

// --- Component Implementation ---
function Card({ icon, title, desc }: CardProps) {
  return (
    <div className="bg-surface/40 backdrop-blur-md border border-border p-6 rounded-xl hover:border-primary/30 transition-colors group">
      <div className="mb-4 bg-surface p-3 w-fit rounded-lg border border-border group-hover:border-primary/50 transition-colors">
        {icon}
      </div>
      <h3 className="text-xl font-bold mb-2 text-white">{title}</h3>
      <p className="text-text-dim text-sm">{desc}</p>
    </div>
  );
}