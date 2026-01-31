import React, { useEffect, useState } from "react";
import api from "../utils/api";
import { Wallet, TrendingUp, TrendingDown, RefreshCw, AlertCircle } from "lucide-react";

export default function LivePositions() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchPositions = async () => {
    setLoading(true);
    try {
      const res = await api.get("/api/v1/broker/positions");
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPositions();
    // Auto-refresh every 10 seconds
    const interval = setInterval(fetchPositions, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !data) return <div className="text-text-dim animate-pulse">Loading portfolio data...</div>;

  if (!data || data.status === "error") {
    return (
      <div className="flex flex-col items-center justify-center h-64 border border-dashed border-border rounded-xl">
        <AlertCircle className="w-10 h-10 text-red-500 mb-2" />
        <p className="text-text-dim">Could not load positions. Is Broker Connected?</p>
        <button onClick={fetchPositions} className="mt-4 text-primary hover:underline">Retry</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* 1. Account Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-surface border border-border p-6 rounded-xl">
          <div className="flex items-center gap-2 text-text-dim mb-2">
            <Wallet size={18} /> Wallet Balance
          </div>
          <div className="text-3xl font-bold text-white">
            ${data.balance?.toFixed(2) || "0.00"} <span className="text-sm text-text-dim">USDT</span>
          </div>
        </div>
        
        {/* Placeholder for Daily P&L (Backend calculation needed) */}
        <div className="bg-surface border border-border p-6 rounded-xl">
          <div className="flex items-center gap-2 text-text-dim mb-2">
            <TrendingUp size={18} /> Unrealized P&L
          </div>
          <div className={`text-3xl font-bold ${
             (data.positions?.reduce((sum:any, p:any) => sum + p.pnl, 0) || 0) >= 0 ? "text-green-500" : "text-red-500"
          }`}>
            ${(data.positions?.reduce((sum:any, p:any) => sum + p.pnl, 0) || 0).toFixed(2)}
          </div>
        </div>
      </div>

      {/* 2. Positions Table */}
      <div className="bg-surface border border-border rounded-xl overflow-hidden">
        <div className="flex justify-between items-center p-6 border-b border-border">
          <h3 className="text-lg font-bold text-white">Open Positions</h3>
          <button onClick={fetchPositions}><RefreshCw size={16} className="text-text-dim hover:text-white" /></button>
        </div>
        
        {data.positions?.length === 0 ? (
          <div className="p-12 text-center text-text-dim text-sm italic">
            No active positions. Your bots are waiting for a signal.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-background text-text-dim uppercase font-mono text-xs">
                <tr>
                  <th className="p-4">Symbol</th>
                  <th className="p-4">Side</th>
                  <th className="p-4">Size</th>
                  <th className="p-4">Entry</th>
                  <th className="p-4">Mark</th>
                  <th className="p-4 text-right">P&L</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {data.positions.map((pos: any, i: number) => (
                  <tr key={i} className="hover:bg-white/5 transition">
                    <td className="p-4 font-bold text-white">{pos.symbol}</td>
                    <td className="p-4">
                      <span className={`px-2 py-1 rounded text-xs font-bold uppercase ${
                        pos.side === 'long' ? 'bg-green-500/20 text-green-500' : 'bg-red-500/20 text-red-500'
                      }`}>
                        {pos.side}
                      </span>
                    </td>
                    <td className="p-4 text-text-dim">{pos.size}</td>
                    <td className="p-4 text-white">${pos.entry_price}</td>
                    <td className="p-4 text-white">${pos.market_price}</td>
                    <td className={`p-4 text-right font-bold ${pos.pnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                      {pos.pnl > 0 ? "+" : ""}{pos.pnl.toFixed(2)} USDT
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}