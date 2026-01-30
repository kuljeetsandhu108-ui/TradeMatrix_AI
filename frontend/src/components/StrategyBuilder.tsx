import React, { useState } from "react";
import { X, Plus, Save, Trash2, PlayCircle, Activity, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import api from "../utils/api"; // <--- CHANGED: Using our smart API helper instead of axios

// --- Types for Type Safety ---
interface BuilderProps {
  onClose: () => void;
}

interface ConditionRow {
  id: number;
  indicatorA: string;
  paramA: string;
  operator: string;
  indicatorB: string;
  paramB: string;
}

export default function StrategyBuilder({ onClose }: BuilderProps) {
  // --- STATE MANAGEMENT ---
  const [name, setName] = useState("");
  const [symbol, setSymbol] = useState("NIFTY 50");
  const [timeframe, setTimeframe] = useState("5m");
  const [isDeploying, setIsDeploying] = useState(false); // Loading state
  
  // The Logic Matrix State
  const [conditions, setConditions] = useState<ConditionRow[]>([
    { id: 1, indicatorA: "EMA", paramA: "9", operator: ">", indicatorB: "EMA", paramB: "21" }
  ]);

  // --- ACTIONS ---

  // 1. Add a new empty logic row
  const addCondition = () => {
    setConditions([
      ...conditions, 
      { id: Date.now(), indicatorA: "RSI", paramA: "14", operator: ">", indicatorB: "VALUE", paramB: "50" }
    ]);
  };

  // 2. Remove a row
  const removeCondition = (id: number) => {
    if (conditions.length === 1) return; // Prevent deleting the last row
    setConditions(conditions.filter(c => c.id !== id));
  };

  // 3. Update specific values in a row (The Logic Engine)
  const updateCondition = (id: number, field: keyof ConditionRow, value: string) => {
    setConditions(conditions.map(c => 
      c.id === id ? { ...c, [field]: value } : c
    ));
  };

  // 4. SAVE & DEPLOY TO BACKEND (Authenticated)
  const handleSave = async () => {
    // Basic Validation
    if (!name) return alert("Please give your strategy a name.");
    
    setIsDeploying(true);

    try {
      // The Payload
      const payload = {
        name: name,
        symbol: symbol,
        timeframe: timeframe,
        conditions: conditions,
        // user_id is NO LONGER needed here, the Backend extracts it from the Token!
      };

      // --- USING SMART API HELPER ---
      // This automatically adds the "Authorization: Bearer <token>" header
      const response = await api.post("/api/v1/strategy/create", payload);

      if (response.data.status === "success") {
        onClose(); // Close the modal to trigger the refresh
      }

    } catch (error) {
      console.error("Deployment Error:", error);
      alert("❌ Deployment Failed. Session might be expired. Try logging in again.");
    } finally {
      setIsDeploying(false);
    }
  };

  // --- RENDER ---
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      
      {/* Modal Container */}
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-[#0f1115] w-full max-w-4xl border border-[#2A2A2A] rounded-2xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
      >
        
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-[#2A2A2A] bg-[#1a1d23]">
          <div>
            <h2 className="text-2xl font-bold text-white flex items-center gap-2">
              <Activity className="text-primary" /> Create New Algorithm
            </h2>
            <p className="text-gray-400 text-sm">Define your entry and exit logic using the matrix.</p>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-gray-400 hover:text-white transition">
            <X size={24} />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="p-8 overflow-y-auto flex-1 space-y-8 custom-scrollbar">
          
          {/* Section 1: Configuration */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Name Input */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-500 uppercase tracking-wider">Strategy Name</label>
              <input 
                type="text" 
                placeholder="e.g. Ayush 1" 
                className="w-full bg-[#050505] border border-[#2A2A2A] rounded-lg p-3 text-white focus:border-primary focus:outline-none transition placeholder:text-gray-700 font-medium"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
            </div>

            {/* Instrument Select */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-500 uppercase tracking-wider">Instrument</label>
              <select 
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                className="w-full bg-[#050505] border border-[#2A2A2A] rounded-lg p-3 text-white focus:border-primary focus:outline-none appearance-none font-mono"
              >
                <option>NIFTY 50</option>
                <option>BANKNIFTY</option>
                <option>FINNIFTY</option>
                <option>RELIANCE</option>
                <option>HDFCBANK</option>
                <option>INFY</option>
              </select>
            </div>

            {/* Timeframe Select */}
            <div className="space-y-2">
              <label className="text-xs font-mono text-gray-500 uppercase tracking-wider">Timeframe</label>
              <div className="flex bg-[#050505] rounded-lg border border-[#2A2A2A] p-1">
                {["1m", "5m", "15m", "1H"].map((tf) => (
                  <button 
                    key={tf}
                    onClick={() => setTimeframe(tf)}
                    className={`flex-1 py-2 text-sm font-medium rounded-md transition ${
                      timeframe === tf ? "bg-[#2A2A2A] text-white shadow-sm border border-gray-700" : "text-gray-500 hover:text-gray-300"
                    }`}
                  >
                    {tf}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Section 2: The Logic Engine */}
          <div className="border-t border-[#2A2A2A] pt-8">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold text-white flex items-center gap-2">
                <PlayCircle className="text-primary" size={20} /> Entry Conditions
              </h3>
              <button 
                onClick={addCondition}
                className="text-xs bg-[#2A2A2A] hover:bg-[#333] text-white px-3 py-1.5 rounded flex items-center gap-1 transition border border-gray-700"
              >
                <Plus size={14} /> Add Condition
              </button>
            </div>

            <div className="space-y-3">
              {conditions.map((cond) => (
                <div key={cond.id} className="flex flex-col md:flex-row items-center gap-3 bg-[#0a0a0a] p-4 rounded-xl border border-[#2A2A2A] group hover:border-primary/50 transition">
                  
                  <span className="text-primary font-mono text-sm px-2 font-bold">IF</span>
                  
                  {/* Left Indicator */}
                  <select 
                    value={cond.indicatorA}
                    onChange={(e) => updateCondition(cond.id, "indicatorA", e.target.value)}
                    className="flex-1 bg-[#151515] text-white text-sm border border-[#2A2A2A] rounded p-2 focus:border-primary outline-none"
                  >
                    <option value="EMA">EMA</option>
                    <option value="SMA">SMA</option>
                    <option value="RSI">RSI</option>
                    <option value="CLOSE">Close Price</option>
                    <option value="OPEN">Open Price</option>
                  </select>

                  {/* Left Param (Value) */}
                  <input 
                    type="number" 
                    value={cond.paramA} 
                    onChange={(e) => updateCondition(cond.id, "paramA", e.target.value)}
                    className="w-20 bg-[#151515] text-white text-sm border border-[#2A2A2A] rounded p-2 text-center focus:border-primary outline-none" 
                  />

                  {/* Operator */}
                  <select 
                    value={cond.operator}
                    onChange={(e) => updateCondition(cond.id, "operator", e.target.value)}
                    className="w-32 bg-[#202020] text-primary font-bold text-sm border border-[#2A2A2A] rounded p-2 text-center outline-none"
                  >
                    <option value=">">Greater Than</option>
                    <option value="<">Less Than</option>
                    <option value="==">Equals</option>
                    <option value="CROSS_UP">Crosses Above</option>
                    <option value="CROSS_DOWN">Crosses Below</option>
                  </select>

                  {/* Right Indicator */}
                  <select 
                    value={cond.indicatorB}
                    onChange={(e) => updateCondition(cond.id, "indicatorB", e.target.value)}
                    className="flex-1 bg-[#151515] text-white text-sm border border-[#2A2A2A] rounded p-2 focus:border-primary outline-none"
                  >
                    <option value="EMA">EMA</option>
                    <option value="SMA">SMA</option>
                    <option value="RSI">RSI</option>
                    <option value="VALUE">Number Value</option>
                  </select>

                  {/* Right Param (Value) */}
                  <input 
                    type="number" 
                    value={cond.paramB} 
                    onChange={(e) => updateCondition(cond.id, "paramB", e.target.value)}
                    className="w-20 bg-[#151515] text-white text-sm border border-[#2A2A2A] rounded p-2 text-center focus:border-primary outline-none" 
                  />

                  {/* Delete Button */}
                  <button 
                    onClick={() => removeCondition(cond.id)} 
                    className="p-2 text-gray-600 hover:text-danger hover:bg-danger/10 rounded transition"
                    title="Remove Condition"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="p-6 border-t border-[#2A2A2A] bg-[#1a1d23] flex justify-end gap-4">
          <button 
            onClick={onClose} 
            className="px-6 py-3 rounded-lg font-bold text-gray-400 hover:text-white transition hover:bg-white/5"
            disabled={isDeploying}
          >
            Cancel
          </button>
          
          <button 
            onClick={handleSave} 
            disabled={isDeploying}
            className={`
              flex items-center gap-2 px-8 py-3 rounded-lg font-bold transition shadow-[0_0_20px_rgba(0,227,150,0.2)]
              ${isDeploying ? "bg-gray-600 cursor-not-allowed text-gray-300" : "bg-primary text-black hover:bg-[#00c985]"}
            `}
          >
            {isDeploying ? (
              <>
                <Loader2 className="animate-spin" size={20} /> Deploying...
              </>
            ) : (
              <>
                <Save size={20} /> Save & Deploy
              </>
            )}
          </button>
        </div>

      </motion.div>
    </div>
  );
}