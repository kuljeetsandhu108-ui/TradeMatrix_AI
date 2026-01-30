import React, { useState, useEffect } from "react";
import axios from "axios";
import { Shield, CheckCircle, Key, Lock, Server, ExternalLink, RefreshCw } from "lucide-react";

export default function BrokerConfig() {
  const [selectedBroker, setSelectedBroker] = useState("fyres");
  const [clientId, setClientId] = useState("");
  const [appSecret, setAppSecret] = useState(""); // Changed from apiKey to Secret
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [connectedBrokers, setConnectedBrokers] = useState<any[]>([]);

  useEffect(() => { checkStatus(); }, []);

  const checkStatus = async () => {
    try {
      const res = await axios.get("http://127.0.0.1:8000/api/v1/broker/status");
      setConnectedBrokers(res.data);
    } catch (err) { console.error(err); }
  };

  // 1. SAVE STATIC KEYS (App ID & Secret)
  const handleSaveKeys = async () => {
    if (!clientId || !appSecret) return alert("Enter App ID & Secret Key first");
    setStatus("loading");
    try {
      await axios.post("http://127.0.0.1:8000/api/v1/broker/connect", {
        broker_name: selectedBroker,
        client_id: clientId,
        api_key: appSecret, // Saving Secret as api_key in DB
        user_id: 1
      });
      setStatus("success");
      setTimeout(() => setStatus("idle"), 2000);
    } catch (error) { setStatus("error"); }
  };

  // 2. DAILY LOGIN (The Morning OTP Flow)
  const handleDailyLogin = async () => {
    try {
      // Ask Backend for the official Fyres URL
      const res = await axios.get("http://127.0.0.1:8000/api/v1/broker/fyres/login-url");
      
      // Redirect User to Fyres (Opens in new window or same)
      window.location.href = res.data.login_url;
    } catch (error) {
      alert("Error: Save your keys first!");
    }
  };

  return (
    <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
      
      {/* LEFT: Configuration */}
      <div className="bg-surface border border-border p-6 rounded-xl">
        <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
          <Key className="text-primary" size={20} /> Broker Setup
        </h3>

        <div className="space-y-4">
          {/* Broker Selector */}
          <div className="grid grid-cols-2 gap-2">
            {["fyres", "angel"].map((b) => (
              <button
                key={b}
                onClick={() => setSelectedBroker(b)}
                className={`py-3 rounded-lg border font-bold capitalize transition ${
                  selectedBroker === b 
                    ? "bg-primary/10 border-primary text-primary" 
                    : "bg-surface-hover border-border text-text-dim"
                }`}
              >
                {b} One
              </button>
            ))}
          </div>

          {/* Static Keys Input */}
          <div>
            <label className="text-xs font-mono text-text-dim uppercase">App ID (Client ID)</label>
            <input 
              type="text" 
              value={clientId}
              onChange={(e) => setClientId(e.target.value)}
              className="w-full mt-1 bg-background border border-border rounded-lg p-3 text-white focus:border-primary outline-none"
              placeholder="Enter App ID from Broker Dashboard"
            />
          </div>

          <div>
            <label className="text-xs font-mono text-text-dim uppercase">App Secret Key</label>
            <div className="relative">
              <input 
                type="password" 
                value={appSecret}
                onChange={(e) => setAppSecret(e.target.value)}
                className="w-full mt-1 bg-background border border-border rounded-lg p-3 text-white focus:border-primary outline-none"
                placeholder="Enter Secret Key"
              />
              <Lock className="absolute right-3 top-4 text-text-dim" size={16} />
            </div>
          </div>

          <button 
            onClick={handleSaveKeys}
            className="w-full py-3 rounded-lg font-bold text-white bg-[#2A2A2A] hover:bg-white/10 transition border border-border"
          >
             {status === "loading" ? "Saving..." : "Step 1: Save Keys"}
          </button>

          <div className="border-t border-dashed border-border my-4 pt-4">
            <h4 className="text-sm font-bold text-white mb-2">Step 2: Morning Login</h4>
            <p className="text-xs text-text-dim mb-3">Click below every morning to generate a fresh Access Token.</p>
            
            <button 
              onClick={handleDailyLogin}
              className="w-full py-4 rounded-lg font-bold text-black bg-primary hover:bg-[#00c985] transition flex items-center justify-center gap-2 shadow-[0_0_20px_rgba(0,227,150,0.2)]"
            >
              <ExternalLink size={18} /> Login with Fyres (Generate Token)
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT: Status */}
      <div className="space-y-6">
        <div className="bg-surface/50 border border-dashed border-border p-6 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 rounded-full text-blue-500">
             <Shield size={24} />
          </div>
          <div>
            <h4 className="text-white font-bold">Token Security</h4>
            <p className="text-xs text-text-dim mt-1">
              Access Tokens are generated on our secure server, not your device. 
              This ensures trading continues even if your phone goes offline.
            </p>
          </div>
        </div>

        <div>
           <div className="flex justify-between items-center mb-3">
              <h4 className="text-sm font-mono text-text-dim uppercase">Active Connections</h4>
              <button onClick={checkStatus} className="text-primary hover:text-white"><RefreshCw size={14}/></button>
           </div>
           
           {connectedBrokers.length > 0 ? (
             connectedBrokers.map((b: any, i) => (
               <div key={i} className="bg-surface border border-border p-4 rounded-lg flex justify-between items-center mb-2">
                 <div className="flex items-center gap-3">
                   <div className={`w-2 h-2 rounded-full animate-pulse ${b.active ? "bg-green-500" : "bg-red-500"}`} />
                   <div>
                     <div className="text-white font-bold capitalize">{b.broker}</div>
                     <div className="text-[10px] text-text-dim font-mono uppercase">{b.active ? "Token Active" : "Token Expired"}</div>
                   </div>
                 </div>
                 <span className="text-green-500 text-xs bg-green-500/10 px-2 py-1 rounded border border-green-500/20">Ready</span>
               </div>
             ))
           ) : (
             <div className="text-text-dim text-sm italic">No brokers connected.</div>
           )}
        </div>
      </div>

    </div>
  );
}