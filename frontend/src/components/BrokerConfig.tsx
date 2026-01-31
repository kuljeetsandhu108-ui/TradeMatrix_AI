import React, { useState, useEffect } from "react";
import api from "../utils/api";
import { Shield, CheckCircle, Key, Lock, Server, RefreshCw } from "lucide-react";

export default function BrokerConfig() {
  const [selectedBroker, setSelectedBroker] = useState("delta"); // Default to Delta Exchange
  const [apiKey, setApiKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [connectedBrokers, setConnectedBrokers] = useState<any[]>([]);

  useEffect(() => { checkStatus(); }, []);

  const checkStatus = async () => {
    try {
      const res = await api.get("/api/v1/broker/status");
      setConnectedBrokers(res.data);
    } catch (err) { console.error(err); }
  };

  const handleConnect = async () => {
    if (!apiKey || !secretKey) return alert("Please enter both keys");
    
    setStatus("loading");
    try {
      // We assume user_id 1 for now (or backend extracts from token)
      // The backend 'connect' endpoint expects: broker_name, api_key, secret_key, user_id
      await api.post("/api/v1/broker/connect", {
        broker_name: selectedBroker,
        api_key: apiKey,
        secret_key: secretKey, 
        user_id: 1 
      });
      
      setStatus("success");
      checkStatus();
      setTimeout(() => setStatus("idle"), 2000);
    } catch (error) {
      console.error(error);
      setStatus("error");
    }
  };

  return (
    <div className="max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-8">
      
      {/* LEFT: Form */}
      <div className="bg-surface border border-border p-6 rounded-xl">
        <h3 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
          <Key className="text-primary" size={20} /> Crypto Exchange Setup
        </h3>

        <div className="space-y-4">
          <label className="text-xs font-mono text-text-dim uppercase">Select Exchange</label>
          <div className="grid grid-cols-2 gap-2">
            {["delta", "coindcx"].map((b) => (
              <button
                key={b}
                onClick={() => setSelectedBroker(b)}
                className={`py-3 rounded-lg border font-bold capitalize transition ${
                  selectedBroker === b 
                    ? "bg-primary/10 border-primary text-primary" 
                    : "bg-surface-hover border-border text-text-dim hover:text-white"
                }`}
              >
                {b}
              </button>
            ))}
          </div>

          <div>
            <label className="text-xs font-mono text-text-dim uppercase">API Key</label>
            <input 
              type="text" 
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full mt-1 bg-background border border-border rounded-lg p-3 text-white focus:border-primary outline-none"
              placeholder="Paste your API Key"
            />
          </div>

          <div>
            <label className="text-xs font-mono text-text-dim uppercase">API Secret</label>
            <div className="relative">
              <input 
                type="password" 
                value={secretKey}
                onChange={(e) => setSecretKey(e.target.value)}
                className="w-full mt-1 bg-background border border-border rounded-lg p-3 text-white focus:border-primary outline-none"
                placeholder="Paste your Secret Key"
              />
              <Lock className="absolute right-3 top-4 text-text-dim" size={16} />
            </div>
          </div>

          <button 
            onClick={handleConnect}
            disabled={status === "loading"}
            className={`w-full py-4 rounded-lg font-bold text-black mt-4 transition flex items-center justify-center gap-2 ${
              status === "success" ? "bg-green-500" : "bg-primary hover:bg-[#00c985]"
            }`}
          >
            {status === "loading" && <Server className="animate-spin" />}
            {status === "success" && <CheckCircle />}
            {status === "idle" && "Connect Exchange"}
            {status === "error" && "Connection Failed"}
          </button>
        </div>
      </div>

      {/* RIGHT: Status */}
      <div className="space-y-6">
        <div className="bg-surface/50 border border-dashed border-border p-6 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-blue-500/10 rounded-full text-blue-500">
             <Shield size={24} />
          </div>
          <div>
            <h4 className="text-white font-bold">24/7 Server-Side Execution</h4>
            <p className="text-xs text-text-dim mt-1">
              Crypto keys are persistent. No daily login required. Your bots will run continuously on our cloud servers.
            </p>
          </div>
        </div>

        <div>
           <div className="flex justify-between items-center mb-3">
              <h4 className="text-sm font-mono text-text-dim uppercase">Active Exchanges</h4>
              <button onClick={checkStatus} className="text-primary hover:text-white"><RefreshCw size={14}/></button>
           </div>
           
           {connectedBrokers.length > 0 ? (
             connectedBrokers.map((b: any, i) => (
               <div key={i} className="bg-surface border border-border p-4 rounded-lg flex justify-between items-center mb-2">
                 <div className="flex items-center gap-3">
                   <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                   <div>
                     <div className="text-white font-bold capitalize">{b.broker}</div>
                     <div className="text-[10px] text-text-dim font-mono uppercase">Key: {b.key_preview}</div>
                   </div>
                 </div>
                 <span className="text-green-500 text-xs bg-green-500/10 px-2 py-1 rounded border border-green-500/20">Connected</span>
               </div>
             ))
           ) : (
             <div className="text-text-dim text-sm italic">No exchanges connected.</div>
           )}
        </div>
      </div>

    </div>
  );
}